# LiveLot Tracker

The purpose of this repository is host all of our tracking code and corresponding tooling.


## The Approach

So I found this sketchy Chinese repo that took the deepsort algorithm and configured it to run using the YOLO network and to utilize real-time object detection using open cv and the VideoCapture object. This is dope because Movidius NCS comes preconfigured with a YOLO cafe model which we will use to draw bounding boxes and feed it into deepsort for unique tracking.

Here is the link to said Chinese GitHub project: https://github.com/Qidian213/deep_sort_yolov3/ (MIT Licensed 😄)

Next, the dev in that repo used the provided deepsort model from the OG research project to perform these real time detections on people..not cars.

So, we're going to have to custom train a deepsort model to work on cars. Luckily I found another article to do just that :P. 

https://nanonets.com/blog/object-tracking-deepsort/
https://github.com/abhyantrika/nanonets_object_tracking/

I plan to train a custom deep sort model to work on vehicles using the NVIDIA AICity data set which is outlined in the article. After this is trained on a GPU configured instance, my next step will be to compile the model down to a Movidius NCS graph. Potential issue, in this article they use PyTorch to train the model, so we've gotta figure out a way to compile from the Torch generated model to a Caffe model, which we would then be able to compile down to the NCS compatible
graph.

Here is the link to the researchers open sourced deep sort research: https://github.com/nwojke/deep_sort

The big challenge here is to create a way to do real-time deepsort tracking using a YOLO model for the input layer locally on a NCS connected to an RPi. Lol we're gonna be rich af if we figure this out.


### Link to demo video 😳
https://www.bilibili.com/video/av23500163/
