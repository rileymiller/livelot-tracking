#!/usr/bin/python3

import argparse
import livelot_tracker
import config.lineSetup
import argparse
import os
import time

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
    people = ARGS.people    
    if not os.path.isfile("./config/points.txt"):
        config.lineSetup.main()
    time.sleep(2)
    livelot_tracker.run(ARGS)
