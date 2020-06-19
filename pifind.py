import socketio
import re
import uuid
import configparser
import subprocess
sio = socketio.Client()


sio.connect('https://livelotapi.herokuapp.com/')
#sio.connect('http://localhost:3000')


config = configparser.ConfigParser(comment_prefixes='/', allow_no_value=True)
config.read("/home/pi/livelot-tracking/livelot-tracker/LotConfig.ini")

cameraID = config.get('Lot', 'cameraID')

if cameraID == "-1":
    cameraID = str(uuid.uuid4())
    config.set('Lot', 'cameraID', cameraID)
    f = open('/home/pi/livelot-tracking/livelot-tracker/LotConfig.ini', 'w')
    config.write(f)
    f.close()

lotName = config.get('Lot', 'lotname')

ipv4 = subprocess.Popen("hostname -I", shell=True, stdout=subprocess.PIPE).communicate()[0]
ipv4 = ipv4.decode("utf-8")
ipv4 = ipv4.split()[0]

#Get the ipv6 address from the linux dig command
ipv6 = subprocess.Popen("dig TXT +short o-o.myaddr.l.google.com @ns1.google.com", shell=True, stdout=subprocess.PIPE).communicate()[0]
ipv6 = ipv6.decode("utf-8")
#The ipv6 address comes back with double qoutes so strip them
ipv6 = re.findall(r'"([^"]*)"', ipv6)[0]

sio.emit("camera-connection", {"lotName": lotName, "ipv4": ipv4, "ipv6": ipv6, "cameraID": cameraID, "online": 'true'})

@sio.on('camera-update-success')
def camera_update_success(data):
    print('Camera update was a success', data)


@sio.on('camera-update-fail')
def camera_update_fail(err):
    print('Camera update failed', err)
