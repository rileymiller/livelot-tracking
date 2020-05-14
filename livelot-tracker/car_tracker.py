import logging
logger = logging.getLogger('livelot-tracker.car_tracker')

import configparser
import math
import json
from request_interface import carIn, carOut

import _thread

from car_object import CarObject
#Will update  use later        
def getNumCars(lotname):
    return

def updateCars(val, lotId):
    try:
        if val == 1:
            carIn(lotId)
        else:
            carOut(lotId)
    except Exception as e:
        logger.error(str(e))


def calc_center(box_points):
    w, h = get_width_height(box_points)
    cx = box_points[0][1] + w / 2
    cy = box_points[0][0] + h / 2
    return cx, cy


def get_width_height(box_points):
    # box_points is in format y1,x1,y2,x2  
    h = abs(box_points[1][0] - box_points[0][0])
    w = abs(box_points[1][1] - box_points[0][1])
    return w, h

class CarTracker:
    def __init__(self):
        self.logger = logging.getLogger('livelot-tracker.car_tracker.CarTracker')
        config = configparser.ConfigParser()
        try:
            config.read("./LotConfig.ini")
            self._lotId = config.get('Lot', 'lotId')
            self._flipBoundary = config.getboolean('Lot','flipBoundary')
            self.logger.info("Config file read.")
        except Exception as e:
            self.logger.error(str(e))
        self._tracked_frames = []
        self._num_cars_in = 0
        self._num_cars_out = 0
        try:
            pointFile = open("points.txt", "r")
            self._x1 = int(pointFile.readline())
            self._y1 = int(pointFile.readline())
            self._x2 = int(pointFile.readline())
            self._y2 = int(pointFile.readline())
        except Exception as e:
            self.logger.error(str(e))
        self._m = (self._y2 - self._y1) / (self._x1 - self._x2)
        pointFile.close()
        self._memory_buffer = []
        angle = abs(math.degrees(math.atan(self._m)))
        self._lineVertical = True
        self._dist_thresh = 10000
        if angle < 45:
            self._lineVertical = False
        self.logger.info('CarTracker Initialized')

    # -1 = outside 1 = inside
    def test_point(self, x, y):
        if not self._lineVertical:
            if x <= max(self._x2, self._x1) and x >= min (self._x1, self._x2):
                if y > (self._m * (x - self._x1) + self._y1):
                    #below horizontal line
                    return 1 if not self._flipBoundary else -1
                else:
                    #above horizontal line
                    return -1 if not self._flipBoundary else 1
            else:
                return
        else:
            if y <= max(self._y2, self._y1) and y >= min(self._y1, self._y2):
                if x > ((y - self._y1 + self._m * self._x1) / self._m):
                    #right of vertical line
                    return 1 if not self._flipBoundary else -1
                else:
                    #left of vertical line 
                    return -1 if not self._flipBoundary else 1
            else:
                return 
    def is_obj_in_col(self, obj):
        x, y = calc_center(obj)
        if not self._lineVertical:
            if x <= max(self._x2, self._x1) and x >= min (self._x1, self._x2):
                return True
            else:
                return False
        else:
            if y <= max(self._y2, self._y1) and y >= min(self._y1, self._y2):
                return True
            else:
                return False
    
    def update_buffer(self, this_frame_cars):
        #0 - distance 1 - index of frame obj 2 - index of mem buff
        min_dist = [9999, -1, -1]
        #n^2 (n^3 considering loop that calls it) but hopefully its not that many objects to cause performance issues?
        for new_pos in this_frame_cars:
            for carObj in self._memory_buffer:
                #already updated continue
                if carObj.updated == True:
                    continue
                prev_pos = carObj.getBoundingBox()
                new_pos_center = calc_center(new_pos)
                prev_pos_center = calc_center(prev_pos)
                dist = math.hypot(new_pos_center[0] - prev_pos_center[0], new_pos_center[1] - prev_pos_center[1])
                if dist < min_dist[0]:
                    min_dist = [dist, this_frame_cars.index(new_pos), self._memory_buffer.index(carObj)]

        bounding_box = this_frame_cars[min_dist[1]]
        index = min_dist[2]
        #will need to figure out good threshold value for cars
        center = calc_center(bounding_box)
        new_pos_val = self.test_point(center[0], center[1])
        self._memory_buffer[index].updateObj(bounding_box, new_pos_val)
            
    def remove_from_buffer(self, index):
        old_pos_val = self._memory_buffer[index].getInitialPos()
        new_pos_val = self._memory_buffer[index].getFramePos()
        self._memory_buffer.remove(self._memory_buffer[index])
        if new_pos_val == old_pos_val or new_pos_val == 0:
            return
        elif new_pos_val == 1 and old_pos_val == -1:
            _thread.start_new_thread(updateCars,(1, self._lotId))
        else:
            _thread.start_new_thread(updateCars,(-1, self._lotId))

    def process_frame(self, output_array):
        # Get the location of every object in this frame
        this_frame_cars =[]
        
        for obj in output_array:
            this_frame_cars.append(obj[0])

        for obj in output_array:
            obj = obj[0]
            closest_obj, dist, index = self.find_object_in_frame(obj, self._memory_buffer)
            if closest_obj == None:
                center = calc_center(car)
                pos_val = self.test_point(center[0], center[1])
                carObj = CarObject(car, pos_val)
                self._memory_buffer.append(carObj)
            else:
                self.update_buffer(this_frame_cars)
        for i in range(len(self._memory_buffer) - 1, -1, -1):
            if self._memory_buffer[i].getUpdated() == False and self._memory_buffer[i].getCounter() == 0:
                self.remove_from_buffer(i)
            elif self._memory_buffer[i].getUpdated() == False:
                self._memory_buffer[i].decrementCounter()
        for i in range(0, len(self._memory_buffer)):
            self._memory_buffer[i].setUpdated(False)

    def find_object_in_frame(self, obj1, objs_in_frame):
        num_objs_in_frame = len(objs_in_frame)
        obj1_center = calc_center(obj1)
        closest_obj = None
        closest_obj_dist = 10000
        index = -1
        for i in range(num_objs_in_frame):
            obj2 = objs_in_frame[i].bounding_box
            obj2_center = calc_center(obj2)
            dist = math.hypot(
                obj2_center[0] - obj1_center[0], obj2_center[1] - obj1_center[1]
            )

            # TODO there should probably be some sort of thresholding done here
            if dist < closest_obj_dist and objs_in_frame[i].getUpdated() != True:
                closest_obj = obj2
                closest_obj_dist = dist
                index = i
        
        return closest_obj, closest_obj_dist, index

