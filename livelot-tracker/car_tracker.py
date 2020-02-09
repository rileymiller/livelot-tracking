import math
import requests
from pprint import pprint
import json
import _thread
#Will update  use later        
def getNumCars(lotname):
    return

def updateCars(val, lotId):
    if val == 1:
        response = requests.put('https://livelotapi.herokuapp.com/lot/{}/carIn'.format(lotId))
    else:
        response = requests.put('https://livelotapi.herokuapp.com/lot/{}/carOut'.format(lotId))
    print(response.json())
    return response

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
        self.loop = asyncio.get_event_loop()
        self._tracked_frames = []
        self._num_of_frames_to_track = 25
        self._num_cars_in = 0
        self._num_cars_out = 0
        pointFile = open("points.txt", "r")
        self._x1 = int(pointFile.readline())
        self._y1 = int(pointFile.readline())
        self._x2 = int(pointFile.readline())
        self._y2 = int(pointFile.readline())
        self._m = (self._y2 - self._y1) / (self._x1 - self._x2)
        pointFile.close()
        self._memory_buffer = []
        angle = abs(math.degrees(math.atan(self._m)))
        self._lineVertical = True
        self._dist_thresh = 10000
        if angle < 45:
            self._lineVertical = False

    # -1 = outside 1 = inside
    def test_point(self, x, y):
        if not self._lineVertical:
            if x <= max(self._x2, self._x1) and x >= min (self._x1, self._x2):
                if y > (self._m * (x - self._x1) + self._y1):
                    #below horizontal line
                    return 1
                else:
                    #above horizontal line
                    return -1
            else:
                return
        else:
            if y <= max(self._y2, self._y1) and y >= min(self._y1, self._y2):
                if x > ((y - self._y1 + self._m * self._x1) / self._m):
                    #right of vertical line
                    return 1
                else:
                    #left of vertical line 
                    return -1
            else:
                print("not in col vert")
    
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
    
    def update_buffer(self, obj):
        closest_obj, dist, index = self.find_object_in_frame(obj, self._memory_buffer)
        #will need to figure out good threshold value for cars
        if dist <= self._dist_thresh:
            center = calc_center(obj)
            new_pos_val = self.test_point(center[0], center[1])
            old_pos_val = self._memory_buffer[index][1]
            self._memory_buffer[index][0] = obj
            self._memory_buffer[index][1] = new_pos_val
            self._memory_buffer[index][2] = 1
            if new_pos_val == old_pos_val:
                print("NO CHANGE")
            elif new_pos_val == 1 and old_pos_val == -1:
                print("CAR ENTERED")
                _thread.start_new_thread(updateCars,(1, '5db10d68660f730017cddd1e'))
            else:
                print("CAR EXITED")
                _thread.start_new_thread(updateCars,(-1, '5db10d68660f730017cddd1e'))

    def process_frame(self, output_array):
        # Get the location of every object in this frame
        this_frame_objects =[]
        for obj in output_array:
            obj = obj[0]
            if self.is_obj_in_col(obj):
                closest_obj, dist, index = self.find_object_in_frame(obj, self._memory_buffer)
                if closest_obj == None:
                    center = calc_center(obj)
                    pos_val = self.test_point(center[0], center[1])
                    temp_arr = [obj, pos_val, 1]
                    self._memory_buffer.append(temp_arr)
                else:
                    self.update_buffer(obj)
        for i in range(len(self._memory_buffer) - 1, -1, -1):
            if self._memory_buffer[i][2] == 0:
                self._memory_buffer.remove(self._memory_buffer[i])
        for i in range(0, len(self._memory_buffer)):
            self._memory_buffer[i][2] = 0

    def find_object_in_frame(self, obj1, objs_in_frame):
        num_objs_in_frame = len(objs_in_frame)
        obj1_center = calc_center(obj1)
        closest_obj = None
        closest_obj_dist = 10000
        index = -1
        for i in range(num_objs_in_frame):
            obj2 = objs_in_frame[i][0]
            obj2_center = calc_center(obj2)
            dist = math.hypot(
                obj2_center[0] - obj1_center[0], obj2_center[1] - obj1_center[1]
            )

            # TODO there should probably be some sort of thresholding done here
            if dist < closest_obj_dist and objs_in_frame[i][2] != 1:
                closest_obj = obj2
                closest_obj_dist = dist
                index = i
        
        return closest_obj, closest_obj_dist, index

