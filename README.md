# LiveLot Tracker

## Different Approaches

### Vector Math

The first approach tried was using the bounding box moving throughout the frame to determine direction based on movement vectors. However we moved away from this approach due to the following reasons:

1. There's too much lot specific thresholding that would need to be done to determine if the car was moving a certain direction.
2. There was no clear indicator of when a car was inside or outside.
3. It was set up so that it needed a certain amount of frames with detections before it did the vector math so if there were no detections it would wait indefinitely before analyzing the frames.
4. With the batch frame method there was no memory sharing so cars from one batch were not correlated to cars in the next batch when they should be.

### Frame by frame memory buffer tracking with user specified line

This was the second approach where each frame was processed and the detections were put into a memory buffer and referenced by the next iteration to determine whether or not it had crossed a line drawn in the frame.

General Psuedocode

```
detections = get_detections()
if memory_buffer is empty:
    memory_buffer.append(detection)
else:
   for each detection:
	update_memory_buffer(detection);

for each object in memory_buffer:
    if not updated and line_side_changed:
	call_api()
	memory_buffer.remove(object)
    if not updated:
	memory_buffer.remove(object)
    if updated:
	memory_buffer[object].updated = !updated
```

Updating the memory buffer consisted of matching the `detection` to the closest object in the memory buffer and testing which side the car is on. If the side changed then a field in the memory buffer was updated so that the api could be called later in the code.

The above psuedocode is the general pipeline that the code followed. However it had 2 main flaws:

1. If a car was stationary on one side of the line then cars moving throughout the frame would be matched with it causing inaccurate results and cases where you see a car enter followed imediately by a car exit or vice versa.
2. If a car was not detected in the frame on either side of the line then it would not be counted as changing side because the memory buffer only looked at the previous frame when determining a change of side.

### Memory buffer with 3 frame timer and different distance minimizing algorithm

To fix the issues in the previous appraoch I added a 3 frame timer to address issue #1. The memory buffer now has a field on each object that starts at 3 and for each frame that it does not get matched to a car it drops by 1 and is removed once it hits 0 and then the api is called if needed. When a car gets matched to the memory buffer it returns to 3.

For issue #2 I recreated the method to match cars with memory buffer objects. Each detection originally just got matched to the closest object in the memory buffer sequentially. Now it iterates over all detections and finds the minimum distance between car and memory buffer object each iteration. This makes stationary cars get matched with itself.

### Multithreaded PiCamera Module

To increase the framerate the PiVideoStream file was made so that the camera constantly polls for new images on a thread seperate from the main thread. Then when an image is needed the main thread can get the most recent image from the image thread.

## Current Issues
1. There is no gurantee that cars are always matched with their own memory buffer object so there might be edge cases where it fails. In concept it shouldn't matter since the net result of cars coming in/out and being matched should be the true count.

2. Depending on the camera angle, occlusions can't be avoided and therefore it's possible that the tracking can mess up.
