from __future__ import print_function # Python 2/3 compatibility
import math
import boto3
import json
import decimal
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)
        
def getNumCars(lotname):
    dynamodb = boto3.resource("dynamodb", aws_access_key_id="AKIAIFYOEWMP7W4EPBHQ", aws_secret_access_key= "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",
         region_name='us-east-2', endpoint_url="https://dynamodb.us-east-2.amazonaws.com")

    table = dynamodb.Table('livelot')

    try:
        response = table.get_item(
            Key={
                'lotname': lotname
            }
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        numCars = response["Item"]['numcars']
        print("GetItem succeeded:")
        print(json.dumps(numCars, indent=4, cls=DecimalEncoder))
        return numCars

def updateCars(comingIn, comingOut, lotname):

    # get the current number of cars in the lot
    currNumCars = getNumCars(lotname)
    if(comingIn):
        currNumCars += 1
    elif(comingOut):
        currNumCars += 1

    dynamodb = boto3.resource("dynamodb", aws_access_key_id="AKIAIFYOEWMP7W4EPBHQ", aws_secret_access_key= "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",
         region_name='us-east-2', endpoint_url="https://dynamodb.us-east-2.amazonaws.com")

    table = dynamodb.Table('livelot')

    response = table.update_item(
        Key={
            'lotname': "StudentCenter"
        },
        UpdateExpression="set numcars = :r",
        ExpressionAttributeValues={
            ':r': currNumCars
        },
        ReturnValues="UPDATED_NEW"
    )

def calc_center(box_points):
    w, h = get_width_height(box_points)
    cx = box_points[0][0] + w / 2
    cy = box_points[0][1] + h / 2
    return cx, cy


def get_width_height(box_points):
    # box_points is in format x1,y1,x2,y2
    w = abs(box_points[1][0] - box_points[0][0])
    h = abs(box_points[1][1] - box_points[0][1])
    return w, h


def calc_area(box_points):
    w, h = get_width_height(box_points)
    return w * h


def get_vector(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    dx = x2 - x1
    dy = y2 - y1
    return (dx, dy)


class CarTracker:
    def __init__(self):
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
        #print("COORDS", x, y)
        #print(((y - self._y1 + self._m * self._x1) / self._m))
        if not self._lineVertical:
            if x <= max(self._x2, self._x1) and x >= min (self._x1, self._x2):
                if y > (self._m * (x - self._x1) + self._y1):
                    #print("below horiz")
                    return 1
                else:
                    #print("above horiz")
                    return -1
            else:
                print("not in col horiz")
        else:
            if y <= max(self._y2, self._y1) and y >= min(self._y1, self._y2):
                if x > ((y - self._y1 + self._m * self._x1) / self._m):
                    #print("right vert")
                    return 1
                else:
                    #print("left vert")
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
            new_pos_val = self.test_point(center[1], center[0])
            old_pos_val = self._memory_buffer[index][1]
            #print("NEW", new_pos_val, "OLD", old_pos_val)
            if new_pos_val == old_pos_val:
                print("NO CHANGE")
            elif new_pos_val == 1 and old_pos_val == -1:
                print("CAR ENTERED")
            else:
                print("CAR EXITED")
            self._memory_buffer[index][0] = obj
            self._memory_buffer[index][1] = new_pos_val
            self._memory_buffer[index][2] = 1

    def process_frame(self, frame_number, output_array, output_count):
        #print('I AM IN PROCESS FRAME')
        #print("FOR FRAME ", frame_number)
        #print("Output for each object : ", output_array)
        #print("Output count for unique objects : ", output_count)
        #print("------------END OF A FRAME --------------")


        # Get the location of every object in this frame
        this_frame_objects = []
        for i in range(0, output_count):
            obj = output_array.get('detection_boxes_{}'.format(i))
            if self.is_obj_in_col(obj):
                if not self._memory_buffer:
                    center = calc_center(obj)
                    pos_val = self.test_point(center[1], center[0])
                    temp_arr = [obj, pos_val, 1]
                    self._memory_buffer.append(temp_arr)
                else:
                    #print("UPDATE BUFFER")
                    self.update_buffer(obj)
        for i in range(len(self._memory_buffer) - 1, 0, -1):
            print(i, self._memory_buffer)
            if self._memory_buffer[i][2] == 0:
                self._memory_buffer.remove(self._memory_buffer[i])
        for i in range(0, len(self._memory_buffer) - 1):
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
            if dist < closest_obj_dist:
                closest_obj = obj2
                closest_obj_dist = dist
                index = i

        return closest_obj, closest_obj_dist, index

    def identify_objects(self):
        frame0 = self._tracked_frames.pop()
        object_to_frames = []

        for i, obj in enumerate(frame0):
            for frame in self._tracked_frames:
                closest_obj = self.find_object_in_frame(obj, frame)
                try:
                    object_to_frames[i].append(closest_obj)
                except IndexError:
                    object_to_frames.append([closest_obj])

        # Get unit vectors
        vectors = [
            get_vector(calc_center(path[0]), calc_center(path[-1]))
            for path in object_to_frames
        ]

        # Find cars coming in/going out
        coming_in = []
        going_out = []
        for v in vectors:
            x, y = v
            m = math.sqrt(x**2 + y**2)
            print(m)
            #m is threshold for determining in vs out 500 was original
            if m > 50:
                if y > 0:
                    self._num_cars_out += 1
                    #updateCars(False, True, "StudentCenter")
                    going_out.append(v)
                else:
                    self._num_cars_in += 1
                    #updateCars(True, False, "StudentCenter")
                    coming_in.append(v)

        print("-" * 80)
        print(f'Cars coming in: {len(coming_in)}')
        print(f'Cars going out: {len(going_out)}')
        print(f'Total cars in: {self._num_cars_in}')
        print(f'Total cars out: {self._num_cars_out}')
        print('OBJECTS THROUGH FRAMES')
        for i, locations in enumerate(object_to_frames):
            print(f'Object {i}: {locations}')
        print("-" * 80)
