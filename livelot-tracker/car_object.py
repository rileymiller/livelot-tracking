class CarObject:
    def __init__(self, bounding_box, initial_position):
        #Bounding box of the car
        self.bounding_box = bounding_box
        #Initial side of the line
        self.initial_position = initial_position
        #Which side of the line the car is on in the current frame
        self.frame_position = 0
        #Whether the car object has been updated this frame
        self.updated = True
        #Frame timeout counter
        self.timeout_counter = 3

    def decrementCounter(self):
        self.timeout_counter = self.timeout_counter - 1

    def getCounter(self):
        return self.timeout_counter

    def getUpdated(self):
        return self.updated
    
    def setUpdated(self, val):
        self.updated = val

    def getBoundingBox(self):
        return self.bounding_box

    def setBoundingBox(self, box):
        self.bounding_box = box

    def getFramePos(self):
        return self.frame_position

    def setFramePos(self, pos):
        self.frame_position = pos
    
    def getInitialPos(self):
        return self.initial_position
    
    def updateObj(self, box, pos):
        self.bounding_box = box
        self.frame_position = pos
        self.updated = True
        self.timeout_counter = 3
