1. Head to https://www.raspberrypi.org/downloads/ and download the latest version of Rasbian (Raspian Buster with desktop)
2. Flash the sd card with the image.
3. Connect the pi to a display and plug in a keyboard and mouse.
4. Setup the timezone, password, wifi,  and install the latest software.
5. Clone the `livelot-tracking` repository into the home directory.
6. `sudo apt-get install dnsutils`
7. pip3 install "python-socketio[client]"
6. Edit `/etc/rc.local` and add `sleep 30s` and `python3 /home/pi/livelot-tracking/pifind.py`
7. Go to the top left dropdown > Preferences > Raspberry Pi Configuration > Interfaces and enable Camera and SSH.
8. Visit `https://download.01.org/opencv/2020/openvinotoolkit/` and find the latest version of the OpenVino toolkin and download it I.E. `wget https://download.01.org/opencv/2020/openvinotoolkit/2020.1/l_openvino_toolkit_runtime_raspbian_p_2020.1.023.tgz`
9. sudo mkdir -p /opt/intel/openvino
10. `sudo tar -xf  l_openvino_toolkit_runtime_raspbian_p_<version>.tgz --strip 1 -C /opt/intel/openvino`
11. `sudo apt install cmake`
12. `source /opt/intel/openvino/bin/setupvars.sh`
13. `echo "source /opt/intel/openvino/bin/setupvars.sh" >> ~/.bashrc`
14. `sudo usermod -a -G users "$(whoami)"`
15. reboot the pi
16. `sh /opt/intel/openvino/install_dependencies/install_NCS_udev_rules.sh`


