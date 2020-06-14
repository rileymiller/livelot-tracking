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
            cv2.line(img, (x1, y1), (x2, y2), (0,255,0), 10)
            print("LINE")
        mouseX,mouseY = x,y

def testPoint(event, x, y, flags, param):
    global x1, x2, y1, y2, m
    if event == cv2.EVENT_LBUTTONUP:
        angle = abs(math.degrees(math.atan(m)))
        if angle < 45:
            if x <= max(x2,x1) and x >= min(x1,x2):
                if y > (m * (x - x1) + y1):
                    print("below vert")
                else:
                    print("above vert")
            else:
                print("not in col vert")
        else:
            print("y",y,"y1",y1,"y2",y2)
            if y <= max(y2,y1) and y >= min(y1,y2):
                if x > ((y - y1 + m * x1) / m):
                    print("below horiz")
                else:
                    print("above horiz")
            else:
                print("not in col horiz")


x1 = -1 
y1 = -1 
x2 = -1 
y2 = -1
m = -1

lineDrawn = False
camera = PiCamera()

camera.resolution = (1648,928)
rawCapture = PiRGBArray(camera, size=(1648,928))

outFile = open("points.txt", "w")
cv2.namedWindow('test')
cv2.setMouseCallback('test',draw_line) 
for frame in camera.capture_continuous(rawCapture, format="bgr"):  
    img = frame.array
    if x1 != -1 and x2 != -1:
        m = (y2 - y1) / (x2 - x1)
        cv2.line(img, (x1, y1), (x2, y2), (0,255,0), 10)
        if lineDrawn == False:
            lineDrawn = True
            outFile.write(str(x1)+ '\n')
            outFile.write(str(y1)+ '\n')
            outFile.write(str(x2)+ '\n') 
            outFile.write(str(y2)+ '\n')
            outFile.close()
            cv2.setMouseCallback('test', testPoint)
    cv2.imshow("test", img)
    k = cv2.waitKey(20) & 0xFF
    if k == 27:
        break
    elif k == ord('a'):
        print(mouseX,mouseY)
        print(x1, y1)
        print(x2, y2)
    rawCapture.truncate()
    rawCapture.seek(0)

