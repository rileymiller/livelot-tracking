1. Head to https://www.raspberrypi.org/downloads/ and download the latest version of Rasbian (Raspian Buster with desktop)
2. Flash the sd card with the image.
3. Connect the pi to a display and plug in a keyboard and mouse.
4. Setup the timezone, password, wifi,  and install the latest software.
5. Clone the `livelot-tracking` repository into the home directory.
6. `sudo apt-get install dnsutils`
7. pip3 install "python-socketio[client]"
6. Edit `/etc/rc.local` and add:
 ```python
    sleep 30s 
    set +e
    sudo -H pip3 install python-socketio
    sudo python3 /home/pi/livelot-tracking/pifind.py &
  ```
7. Go to the top left dropdown > Preferences > Raspberry Pi Configuration > Interfaces and enable Camera and SSH.
8. Set up the Coral TPU Runtime
9. echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
10. curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
11. sudo apt-get update
12. sudo apt-get install libedgetpu1-std
13. pip3 install https://dl.google.com/coral/python/tflite_runtime-2.1.0.post1-cp37-cp37m-linux_armv7l.whl



