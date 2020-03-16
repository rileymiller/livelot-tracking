class CarObject:
    def __init__(self, bounding_box, initial_position):
        #Bounding box of the car
        self.bounding_box = bounding_box
        #Initial side of the line
        self.initial_position = initial_position
        #Which side of the line the car is on in the current frame
        self.frame_position = 0
        #Whether the car object has been updated this frame
        self.updated = 1
        #Frame timeout counter
        self.timeout_counter = 3