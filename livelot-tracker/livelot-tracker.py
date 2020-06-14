#!/usr/bin/python3


import logging
from datetime import datetime
import os

#Set up logger
now = datetime.now().strftime("_%d-%m-%Y_%H:%M:%S.log")
logger = logging.getLogger('livelot-tracker')
logging.basicConfig(level=logging.INFO)
if not os.path.exists('./logs'):
    os.makedirs('./logs')
fileHandler = logging.FileHandler('logs/tracker' + now)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)

import os
import time
import cv2
import numpy as np
import argparse

from PIL import Image
from tflite_runtime.interpreter import load_delegate
from tflite_runtime.interpreter import Interpreter
import io

from utils import visualize_output
from car_tracker import CarTracker
from utils.PiVideoStream import PiVideoStream

# Detection threshold: Minimum confidance to tag as valid detection
CONFIDENCE_THRESHOLD = 0.60 # 60% confidant

# Variable to store commandline arguments
ARGS                 = None

# Initialize CarTracker
car_tracker = CarTracker()

#Boundary line
line_x1 = -1
line_x2 = -1
line_y1 = -1
line_y2 = -1

#Image Dimensions
image_width = 1648
image_height = 928




def load_labels(path):
  with open(path, 'r') as f:
    return {i: line.strip() for i, line in enumerate(f.readlines())}


def set_input_tensor(interpreter, image):
  tensor_index = interpreter.get_input_details()[0]['index']
  input_tensor = interpreter.tensor(tensor_index)()[0]
  input_tensor[:, :] = image

def get_output_tensor(interpreter, index):
  """Returns the output tensor at the given index."""
  output_details = interpreter.get_output_details()[index]
  tensor = np.squeeze(interpreter.get_tensor(output_details['index']))
  return tensor

def detect_objects(interpreter, image, threshold):
  """Returns a list of detection results, each a dictionary of object info."""
  set_input_tensor(interpreter, image)
  interpreter.invoke()

  # Get all output details
  boxes = get_output_tensor(interpreter, 0)
  classes = get_output_tensor(interpreter, 1)
  scores = get_output_tensor(interpreter, 2)
  count = int(get_output_tensor(interpreter, 3))

  results = []
  for i in range(count):
    if scores[i] >= threshold:
      result = {
          'bounding_box': boxes[i],
          'class_id': classes[i],
          'score': scores[i]
      }
      results.append(result)
  return results

def show_inference(obj_list, frame, record_bool):
    for obj in obj_list:
        (y1, x1) = obj[0][0]
        (y2, x2) = obj[0][1]
        display_str = (str(obj[1])
                        + ": "
                        + str( obj[2] )
                        + "%" )

        frame = visualize_output.draw_bounding_box( 
                y1, x1, y2, x2, 
                frame,
                thickness=4,
                color=(255, 255, 0),
                display_str=display_str )
    if record_bool:
        cv2.line(frame, (line_x1, line_y1), (line_x2, line_y2), (0,255,0), 5)
        record_file.write(frame)

    # If a display is available, show the image on which inference was performed
    if debug == True and 'DISPLAY' in os.environ:
        cv2.line(frame, (line_x1, line_y1), (line_x2, line_y2), (0,255,0), 5)
        cv2.imshow( 'Live inference', frame )

def main():
    labels = load_labels('./model/coco_labels.txt')
    interpreter = Interpreter('./model/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite',
        experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
    interpreter.allocate_tensors()
    _, height, width, _ = interpreter.get_input_details()[0]['shape']
    logger.info('Model loaded to TPU')
    start_time = time.time()
    frame_count = 0
    
    vs = PiVideoStream(resolution=(image_width, image_height),framerate=60).start()
    #Sleep to allow camera set up
    time.sleep(2.0)
    while True:    
        frame_count = frame_count + 1
        frame_start_time = time.time()
        img = vs.read()
        displayImg = img
        frameImg = img
        frameImg = cv2.resize(frameImg, (width,height))
        detection_start = time.time()
        results = detect_objects(interpreter, frameImg, CONFIDENCE_THRESHOLD)
        if timing:
            print("Detection time (ms): ", 1000 * (time.time() - detection_start)) 
                
        car_bboxs = []
        for obj in results:
            if people:
                track_list = [0]
            else:
                track_list = [2,3,5,7]
            # 0 - person 2 - car 3 - motorcycle 5 - bus 7 - truck
            if obj["class_id"] in track_list:
                x1 = int(obj["bounding_box"][1] * image_width)
                y1 = int(obj["bounding_box"][0] * image_height)
                x2 = int(obj["bounding_box"][3] * image_width)
                y2 = int(obj["bounding_box"][2] * image_height)
                bbox_obj = [[(y1, x1),(y2, x2)], obj["class_id"], obj["score"]]
                car_bboxs.append(bbox_obj)
        
        if record != None:
            show_inference(car_bboxs, displayImg, True)
        
        if debug:
            show_inference(car_bboxs, displayImg, False)

        if( cv2.waitKey( 5 ) & 0xFF == ord( 'q' ) ):
            vs.stop()
            if record_file != None:
                record_file.release()
            break
            
        car_tracker.process_frame(car_bboxs)
        elapsed_ms = (time.time() - start_time) * 1000

        if timing:
            print("FPS: ", frame_count / (time.time() - start_time)) # FPS = 1 / time to process loop
            print("Total time (ms)", 1000 * (time.time() - frame_start_time))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Main runner for the LiveLot tracking software." )

    parser.add_argument( '-r', '--record', type=str,
                         nargs='?',
                         const="livelot_recording",
                         default=None,
                         help="',' delimited floating point values for image mean." )

    parser.add_argument( '-d', '--debug', type=bool,
                         nargs='?',
                         const=True, default=False,
                         help="Shows the image feed with bounding boxes and boundary line." )
    parser.add_argument( '-t', '--timing', type=bool,
                         nargs='?',
                         const=True, default=False,
                         help="Prints out timing information." )
    parser.add_argument( '-p', '--people', type=bool,
                         nargs='?',
                         const=True, default=False,
                         help="Used for testing using people instead of cars." )
    

    ARGS = parser.parse_args()
    timing = ARGS.timing 
    debug = ARGS.debug
    record = ARGS.record
    people = ARGS.people
    
    if record != None:
        record_file = cv2.VideoWriter('./recordings/{}.avi'.format(record),cv2.VideoWriter_fourcc('M','J','P','G'), 30, (image_width,image_height))


    try:
        pointFile = open("./config/points.txt", "r")
    except Exception as e:
        logger.error(str(e))
    line_x1 = int(pointFile.readline())
    line_y1 = int(pointFile.readline())
    line_x2 = int(pointFile.readline())
    line_y2 = int(pointFile.readline())
    pointFile.close()
    logger.info('Boundary line point data has been loaded')
    main()
    try:
        main()
    except Exception as e:
        logger.error(str(e))
