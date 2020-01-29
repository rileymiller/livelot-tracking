#!/usr/bin/python3

# ****************************************************************************
# Copyright(c) 2017 Intel Corporation. 
# License: MIT See LICENSE file in root directory.
# ****************************************************************************

# Detect objects on a LIVE camera feed using
# Intel® Movidius™ Neural Compute Stick (NCS)

import os
import cv2
import sys
import numpy
import ntpath
import argparse
from picamera import PiCamera
from picamera.array import PiRGBArray

from openvino.inference_engine import IENetwork, IECore
import openvino.inference_engine.ie_api

from utils import visualize_output
from utils import deserialize_output
from car_tracker import CarTracker

# Detection threshold: Minimum confidance to tag as valid detection
CONFIDANCE_THRESHOLD = 0.60 # 60% confidant

# Variable to store commandline arguments
ARGS                 = None

# OpenCV object for video capture
camera               = None

# Initialize CarTracker
car_tracker = CarTracker()

line_x1 = -1
line_x2 = -1
line_y1 = -1
line_y2 = -1
image_width = 1280
image_height = 720

# ---- Step 1: Open the enumerated device and get a handle to it -------------

def open_ncs_device():

    # Look for enumerated NCS device(s); quit program if none found.
    devices = mvnc.EnumerateDevices()
    if len( devices ) == 0:
        print( "No devices found" )
        quit()

    # Get a handle to the first enumerated device and open it
    device = mvnc.Device( devices[0] )
    device.OpenDevice()

    return device

# ---- Step 2: Load a graph file onto the NCS device -------------------------

def load_graph( device ):

    # Read the graph file into a buffer
    with open( ARGS.graph, mode='rb' ) as f:
        blob = f.read()

    # Load the graph buffer into the NCS
    graph = device.AllocateGraph( blob )

    return graph

# ---- Step 3: Pre-process the images ----------------------------------------

def pre_process_image( frame ):

    # Resize image [Image size is defined by choosen network, during training]
    img = cv2.resize( frame, tuple( ARGS.dim ) )

    # Convert RGB to BGR [OpenCV reads image in BGR, some networks may need RGB]
    if( ARGS.colormode == "rgb" ):
        img = img[:, :, ::-1]

    # Mean subtraction & scaling [A common technique used to center the data]
    img = img.astype( numpy.float16 )
    img = ( img - numpy.float16( ARGS.mean ) ) * ARGS.scale

    return img

# ---- Step 4: Read & print inference results from the NCS -------------------

def infer_image( img, frame, input_blob, output_blob, exec_net ):
    cur_request_id = 0
    exec_net.start_async(request_id=cur_request_id, inputs={input_blob: img})
    num_detections = 0
    obj_list = []
    if exec_net.requests[cur_request_id].wait(-1) == 0:
        inference_results = exec_net.requests[cur_request_id].outputs[output_blob]
        for num, detection_result in enumerate(inference_results[0][0]):
            if detection_result[1] in [7, 6, 14, 15] and detection_result[2] > 0.5:
                x1 = int(detection_result[3] * image_width)
                y1 = int(detection_result[4] * image_height)
                x2 = int(detection_result[5] * image_width)
                y2 = int(detection_result[6] * image_height)
                #[bounding box, class, confidence]
                obj = [[(y1, x1), (y2, x2)], detection_result[1], detection_result[2]]
                num_detections = num_detections + 1
                obj_list.append(obj)
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


    # if a car (7), bus (6), or motorbike (14) human (15)
    if False:
    #if(output_dict['num_detections'] != 0):
        if(output_dict['detection_classes_0'] == 15 or output_dict['detection_classes_0'] == 7 or output_dict['detection_classes_0'] == 6 or output_dict['detection_classes_0'] == 14):
            #print('detected a motorized vehical')
            car_tracker.process_frame(0, output_dict, output_dict['num_detections'])
            if(debug):
                for i in range(0, output_dict['num_detections']):
                    # Draw bounding boxes around valid detections 
                    (y1, x1) = output_dict.get('detection_boxes_{}'.format(i))[0]
                    (y2, x2) = output_dict.get('detection_boxes_{}'.format(i))[1]

                    # Prep string to overlay on the image
                    display_str = (labels[output_dict.get('detection_classes_0')]
                                    + ": "
                                    + str( output_dict.get('detection_scores_0' ) )
                                    + "%" )

                    frame = visualize_output.draw_bounding_box( 
                            y1, x1, y2, x2, 
                            frame,
                            thickness=4,
                            color=(255, 255, 0),
                            display_str=display_str )
                 #print( '\n' )
   
   
    #for i in range( 0, output_dict['num_detections'] ):
        #if(labels[ int(output_dict['detection_classes_' + str(i)]) ] == "15: person"):
            #print( "%3.1f%%\t" % output_dict['detection_scores_' + str(i)] 
                   #+ labels[ int(output_dict['detection_classes_' + str(i)]) ]
                   #+ ": Top Left: " + str( output_dict['detection_boxes_' + str(i)][0] )
                   #+ " Bottom Right: " + str( output_dict['detection_boxes_' + str(i)][1] ) )

        

    # If a display is available, show the image on which inference was performed
    if debug == True and 'DISPLAY' in os.environ:
        cv2.line(frame, (line_x1, line_y1), (line_x2, line_y2), (0,255,0), 10)
        cv2.imshow( 'NCS live inference', frame )

# ---- Step 5: Unload the graph and close the device -------------------------

def close_ncs_device( device, graph ):
    graph.DeallocateGraph()
    device.CloseDevice()
    camera.close()
    cv2.destroyAllWindows()

# ---- Main function (entry point for this script ) --------------------------

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
        #img = pre_process_image(camImg)
        img = camImg
        infer_image(img, frameImg, input_blob, output_blob, exec_net)
        rawCapture.truncate()
        rawCapture.seek(0)
        if( cv2.waitKey( 5 ) & 0xFF == ord( 'q' ) ):
            break

    close_ncs_device( device, graph )

# ---- Define 'main' function as the entry point for this script -------------

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
                         description="Detect objects on a LIVE camera feed using \
                         Intel® Movidius™ Neural Compute Stick." )

    parser.add_argument( '-g', '--graph', type=str,
                         default='../../caffe/SSD_MobileNet/graph',
                         help="Absolute path to the neural network graph file." )

    parser.add_argument( '-v', '--video', type=int,
                         default=0,
                         help="Index of your computer's V4L2 video device. \
                               ex. 0 for /dev/video0" )

    parser.add_argument( '-l', '--labels', type=str,
                         default='../../caffe/SSD_MobileNet/labels.txt',
                         help="Absolute path to labels file." )

    parser.add_argument( '-M', '--mean', type=float,
                         nargs='+',
                         default=[127.5, 127.5, 127.5],
                         help="',' delimited floating point values for image mean." )

    parser.add_argument( '-S', '--scale', type=float,
                         default=0.00789,
                         help="Absolute path to labels file." )

    parser.add_argument( '-D', '--dim', type=int,
                         nargs='+',
                         default=[300, 300],
                         help="Image dimensions. ex. -D 224 224" )

    parser.add_argument( '-c', '--colormode', type=str,
                         default="bgr",
                         help="RGB vs BGR color sequence. This is network dependent." )

    parser.add_argument( '-d', '--debug', type=bool,
                         nargs='?',
                         const=True, default=False,
                         help="RGB vs BGR color sequence. This is network dependent." )
    ARGS = parser.parse_args()

    debug = ARGS.debug
    # Create a VideoCapture object
    camera = PiCamera()
    # Set camera resolution
    camera.resolution = (1280,720)#(1280, 720)#(640,480)
    rawCapture = PiRGBArray(camera, size=(1280,720))
    # Load the labels file
    labels =[ line.rstrip('\n') for line in
              open( ARGS.labels ) if line != 'classes\n']
    pointFile = open("points.txt", "r")
    line_x1 = int(pointFile.readline())
    line_y1 = int(pointFile.readline())
    line_x2 = int(pointFile.readline())
    line_y2 = int(pointFile.readline())
    pointFile.close()
    main()

# ==== End of file ===========================================================
