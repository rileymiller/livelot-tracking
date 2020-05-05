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
from picamera import PiCamera
from picamera.array import PiRGBArray

from PIL import Image
from tflite_runtime.interpreter import load_delegate
from tflite_runtime.interpreter import Interpreter
import io

from openvino.inference_engine import IENetwork, IECore
import openvino.inference_engine.ie_api

from utils import visualize_output
from car_tracker import CarTracker
from PiVideoStream import PiVideoStream

# Detection threshold: Minimum confidance to tag as valid detection
CONFIDANCE_THRESHOLD = 0.60 # 60% confidant

# Variable to store commandline arguments
ARGS                 = None

# OpenCV object for video capture
camera               = None

# Initialize CarTracker
car_tracker = CarTracker()

#Boundary line
line_x1 = -1
line_x2 = -1
line_y1 = -1
line_y2 = -1

#Image Dimensions
image_width = 1640#1280
image_height = 922#720



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

def classify_image(interpreter, image, top_k=1):
  """Returns a sorted array of classification results."""
  set_input_tensor(interpreter, image)
  interpreter.invoke()
  output_details = interpreter.get_output_details()[0]
  output = np.squeeze(interpreter.get_tensor(output_details['index']))

  # If the model is quantized (uint8 data), then dequantize the results
  if output_details['dtype'] == np.uint8:
    scale, zero_point = output_details['quantization']
    output = scale * (output - zero_point)

  ordered = np.argpartition(-output, top_k)
  return [(i, output[i]) for i in ordered[:top_k]]

def infer_image( img, frame, input_blob, output_blob, exec_net ):
    detection_start = time.time()
    exec_net.start_async(request_id=0, inputs={input_blob: img})
    num_detections = 0
    obj_list = []
    if exec_net.requests[0].wait(-1) == 0:
        inference_results = exec_net.requests[0].outputs[output_blob]
        for num, detection_result in enumerate(inference_results[0][0]):
            # if a car (7), bus (6), or motorbike (14) human (15)
            if detection_result[1] in [7, 6, 14] and detection_result[2] > 0.5:
                x1 = int(detection_result[3] * image_width)
                y1 = int(detection_result[4] * image_height)
                x2 = int(detection_result[5] * image_width)
                y2 = int(detection_result[6] * image_height)
                #[bounding box, class, confidence]
                obj = [[(y1, x1), (y2, x2)], detection_result[1], detection_result[2]]
                num_detections = num_detections + 1
                obj_list.append(obj)
    if timing:
        print("Detection time (ms): ", 1000 * (time.time() - detection_start)) 

    car_tracker_start = time.time()
    car_tracker.process_frame(obj_list)
    if timing:
        print("Car Tracker Time (ms): ", 1000 * (time.time() - car_tracker_start)) 
    if (debug):
        show_inference(obj_list, frame)

def show_inference(obj_list, frame):
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

    # If a display is available, show the image on which inference was performed
    if debug == True and 'DISPLAY' in os.environ:
        cv2.line(frame, (line_x1, line_y1), (line_x2, line_y2), (0,255,0), 10)
        cv2.imshow( 'NCS live inference', frame )

def main():
    if not tpu:
        try:
            ir = './mobilenet-ssd.xml'
            ie = IECore()
            net = IENetwork(model = ir, weights = ir[:-3] + 'bin')
            exec_net = ie.load_network(network = net, device_name = 'MYRIAD')
            input_blob = next(iter(net.inputs))
            output_blob = next(iter(net.outputs))
            input_shape = net.inputs[input_blob].shape
            output_shape = net.outputs[output_blob].shape
            n, c, h, w = input_shape
            x, y, detections_count, detections_size = output_shape
        except Exception as e:
            logger.error(str(e))
        logger.info('Model succesfully loaded to NCS')
    #try:
        #camera = PiCamera()
        #camera.resolution = (image_width,image_height)
        #camera.framerate = 30
        #rawCapture = PiRGBArray(camera, size=(image_width, image_height))
    #except Exception as e:
    #    logger.error(str(e))
    if tpu:
        labels = load_labels('./coco_labels.txt')
        interpreter = Interpreter('./ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite',
            experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
        interpreter.allocate_tensors()
        _, height, width, _ = interpreter.get_input_details()[0]['shape']
        logger.info('Model loaded to TPU')
    start_time = time.time()
    frame_count = 0
    if tpu:
        #for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        vs = PiVideoStream(resolution=(image_width, image_height),framerate=60).start()
        time.sleep(2.0)
        while True:    
            frame_count = frame_count + 1
            frame_start_time = time.time()
            img = vs.read()
            displayImg = img
            frameImg = img
            frameImg = cv2.resize(frameImg, (width,height))
            detection_start = time.time()
            results = detect_objects(interpreter, frameImg, 0.5)#classify_image(interpreter, image)
            if timing:
                print("Detection time (ms): ", 1000 * (time.time() - detection_start)) 
                
            car_bboxs = []
            for obj in results:
                # 0 - person 2 - car 3 - motorcycle 5 - bus 7 - truck
                if obj["class_id"] in [0,2,3,5,7] and obj["score"] > 0.5:
                    x1 = int(obj["bounding_box"][1] * image_width)
                    y1 = int(obj["bounding_box"][0] * image_height)
                    x2 = int(obj["bounding_box"][3] * image_width)
                    y2 = int(obj["bounding_box"][2] * image_height)
                    bbox_obj = [[(y1, x1),(y2, x2)], obj["class_id"], obj["score"]]
                    car_bboxs.append(bbox_obj)

            if(debug):
                show_inference(car_bboxs, displayImg)

            if( cv2.waitKey( 5 ) & 0xFF == ord( 'q' ) ):
                vs.stop()
                break
            car_tracker.process_frame(car_bboxs)
            elapsed_ms = (time.time() - start_time) * 1000
            #rawCapture.truncate(0)

            if timing:
                print("FPS: ", frame_count / (time.time() - start_time)) # FPS = 1 / time to process loop
                print("Total time (ms)", 1000 * (time.time() - frame_start_time))
    if not tpu:
        try:
            camera = PiCamera()
            camera.resolution = (image_width,image_height)
            camera.framerate = 30
            rawCapture = PiRGBArray(camera, size=(image_width, image_height))
        except Exception as e:
            logger.error(str(e))
        logger.info('Pi Camera initialized')
        # Main loop: Capture live stream & send frames to NCS
        for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
            frame_count = frame_count + 1
            frame_start_time = time.time()
            frameImg = frame.array
            camImg = frame.array
            camImg = cv2.resize(camImg, (w,h))
            camImg = np.transpose(camImg, (2,0,1))
            camImg = camImg.reshape((n, c, h, w))
            img = camImg
            infer_image(img, frameImg, input_blob, output_blob, exec_net)
            rawCapture.truncate(0)
            if( cv2.waitKey( 5 ) & 0xFF == ord( 'q' ) ):
                break
            if timing:
                print("FPS: ", frame_count / (time.time() - start_time)) # FPS = 1 / time to process loop
                print("Total time (ms)", 1000 * (time.time() - frame_start_time))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
                         description="Detect objects on a LIVE camera feed using \
                         Intel® Movidius™ Neural Compute Stick 2." )

    parser.add_argument( '-M', '--mean', type=float,
                         nargs='+',
                         default=[127.5, 127.5, 127.5],
                         help="',' delimited floating point values for image mean." )

    parser.add_argument( '-d', '--debug', type=bool,
                         nargs='?',
                         const=True, default=False,
                         help="Shows the image feed with bounding boxes and boundary line." )
    parser.add_argument( '-t', '--timing', type=bool,
                         nargs='?',
                         const=True, default=False,
                         help="Prints out timing information." )
    
    parser.add_argument( '-T', '--TPU', type=bool,
                         nargs='?',
                         const=True, default=False,
                         help="Use the TPU instead of NCS2." )

    ARGS = parser.parse_args()
    timing = ARGS.timing 
    debug = ARGS.debug
    tpu = ARGS.TPU

    try:
        pointFile = open("points.txt", "r")
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
