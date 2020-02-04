#!/usr/bin/python3

# ****************************************************************************
# Copyright(c) 2017 Intel Corporation. 
# License: MIT See LICENSE file in root directory.
# ****************************************************************************

# Detect objects on a LIVE camera feed using
# Intel® Movidius™ Neural Compute Stick (NCS)

import os
import cv2
import numpy
import argparse
from picamera import PiCamera
from picamera.array import PiRGBArray

from openvino.inference_engine import IENetwork, IECore
import openvino.inference_engine.ie_api

from utils import visualize_output
from car_tracker import CarTracker

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
image_width = 1280
image_height = 720

def infer_image( img, frame, input_blob, output_blob, exec_net ):
    exec_net.start_async(request_id=0, inputs={input_blob: img})
    num_detections = 0
    obj_list = []
    if exec_net.requests[0].wait(-1) == 0:
        inference_results = exec_net.requests[0].outputs[output_blob]
        for num, detection_result in enumerate(inference_results[0][0]):
            # if a car (7), bus (6), or motorbike (14) human (15)
            if detection_result[1] in [7, 6, 14, 15] and detection_result[2] > 0.5:
                x1 = int(detection_result[3] * image_width)
                y1 = int(detection_result[4] * image_height)
                x2 = int(detection_result[5] * image_width)
                y2 = int(detection_result[6] * image_height)
                #[bounding box, class, confidence]
                obj = [[(y1, x1), (y2, x2)], detection_result[1], detection_result[2]]
                num_detections = num_detections + 1
                obj_list.append(obj)
    
    car_tracker.process_frame(obj_list)

    if (debug):
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
    # Main loop: Capture live stream & send frames to NCS
    for frame in camera.capture_continuous(rawCapture, format="bgr"):
        frameImg = frame.array
        camImg = frame.array
        camImg = cv2.resize(camImg, (w,h))
        camImg = numpy.transpose(camImg, (2,0,1))
        camImg = camImg.reshape((n, c, h, w))
        img = camImg
        infer_image(img, frameImg, input_blob, output_blob, exec_net)
        rawCapture.truncate()
        rawCapture.seek(0)
        if( cv2.waitKey( 5 ) & 0xFF == ord( 'q' ) ):
            break

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
    ARGS = parser.parse_args()

    debug = ARGS.debug
    camera = PiCamera()
    camera.resolution = (image_width,image_height)
    rawCapture = PiRGBArray(camera, size=(image_width, image_height))
    pointFile = open("points.txt", "r")
    line_x1 = int(pointFile.readline())
    line_y1 = int(pointFile.readline())
    line_x2 = int(pointFile.readline())
    line_y2 = int(pointFile.readline())
    pointFile.close()
    main()

