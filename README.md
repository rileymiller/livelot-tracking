## Setting up a Raspberry Pi from scratch

1. Image the Pi with the most recent RPi image: 
``` 
    git clone https://www.raspberrypi.org/downloads/raspberry-pi-desktop/
```
2. Enable Raspberry Pi for ssh if not already enabled:
    - Launch `Raspberry Pi Configuration` from the `Preferences` menu
    - Navigate to the `Interfaces` tab
    - Select `Enabled` next to `SSH`
    - Click `OK`
3. Place `pyfind.py` under `/home/pi/` (TODO write `install.sh` script) and change privileges running:
```
    chmod 777 pyfind.py
``` 
then edit `/etc/rc.local` and add two lines in the file:
    ```
        sleep 30s
        python /home/pi/pifind.py
    ```
4. Pull down the `livelot-tracking` repo: 
```
    git clone https://github.com/rileymiller/livelot-tracking
```
5. Install all Debian and Python dependencies for the RPi and NCS:
```
    sudo apt-get install -y libusb-1.0-0-dev libprotobuf-dev libleveldb-dev libsnappy-dev libopencv-dev libhdf5-serial-dev protobuf-compiler libatlas-base-dev git automake byacc lsb-release cmake libgflags-dev libgoogle-glog-dev liblmdb-dev swig3.0 graphviz libxslt-dev libxml2-dev gfortran python3-dev python-pip python3-pip python3-setuptools python3-markdown python3-pillow python3-yaml python3-pygraphviz python3-h5py python3-nose python3-lxml python3-matplotlib python3-numpy python3-protobuf python3-dateutil python3-skimage python3-scipy python3-six python3-networkx python3-tk
```
6. Navigate into `livelot-tracking` and compile NCSDK's API framework:
```
    cd ~/livelot-tracking/ncsdk
    make
    sudo make install
```
7. Install OpenCV and additional dependencies for RPi:
```
    sudo apt-get install python-opencv
    sudo pip3 install opencv-python==3.4.3
    sudo apt-get install libjasper-dev
    sudo apt-get install libqtgui4
    sudo apt-get install libqt4-test
    pip install boto3
```
8. Navigate and run script to detect cars:
```
    cd ~/livelot-tracking/ncsappzoo/apps/livelot-object-detector
    python3 live-object-detector-copy.py (TODO update this with correct naming conventions)
```
