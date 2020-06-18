import cv2
import math
from picamera import PiCamera
from picamera.array import PiRGBArray
def draw_line(event,x,y,flags,param):
    global mouseX,mouseY, x1, y1, x2, y2
    if event == cv2.EVENT_LBUTTONUP:
        if x1 == -1:
            x1 = x
            y1 = y
        else:
            x2 = x
            y2 = y
        if x1 != -1 and x2 != -1:
            cv2.line(img, (x1, y1), (x2, y2), (0,255,0), 5)
        mouseX,mouseY = x,y


x1 = -1 
y1 = -1 
x2 = -1 
y2 = -1
m = -1

textDisplayed = False
lineDrawn = False
camera = PiCamera()

camera.resolution = (1664,928)
rawCapture = PiRGBArray(camera, size=(1664,928))

outFile = open("points.txt", "w")
cv2.namedWindow('Line Setup')
cv2.setMouseCallback('Line Setup',draw_line) 
print("Click two points on the image to draw a line or \'q\' to quit.")
for frame in camera.capture_continuous(rawCapture, format="bgr"):  
    img = frame.array
    if x1 != -1 and x2 != -1:
        m = (y2 - y1) / (x2 - x1)
        cv2.line(img, (x1, y1), (x2, y2), (0,255,0), 10)
        if lineDrawn == False:
            lineDrawn = True
        else:
            if textDisplayed == False:
                print("Press \'q\' to exit or \'r\' to redraw line.")
                textDisplayed = True
            k = cv2.waitKey(25) & 0xFF
            if k == 113:
                outFile.write(str(x1)+ '\n')
                outFile.write(str(y1)+ '\n')
                outFile.write(str(x2)+ '\n') 
                outFile.write(str(y2)+ '\n')
                outFile.close()
                exit()
            elif k == 114:
                x1 = x2 = y2 = y2 = -1
                textDisplayed = False
                print("Redraw line.")
    cv2.imshow("Line Setup", img)
    k = cv2.waitKey(25) & 0xFF
    if k == 113:
        exit()
    rawCapture.truncate()
    rawCapture.seek(0)

