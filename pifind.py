import socketio
import re
import uuid
import configparser
import subprocess

sio = socketio.Client()
sio.connect('https://livelotapi-rm-ip-table-q3tgigl.herokuapp.com/')

config = configparser.ConfigParser(comment_prefixes='/', allow_no_value=True)
config.read("./livelot-tracker/LotConfig.ini")

cameraID = config.get('Lot', 'cameraID')
if cameraID == "-1":
    cameraID = str(uuid.uuid4())
    config.set('Lot', 'cameraID', cameraID)
    f = open('./livelot-tracker/LotConfig.ini', 'w')
    config.write(f)
    f.close()

ipv4 = subprocess.Popen("hostname -I", shell=True, stdout=subprocess.PIPE).communicate()[0]
ipv4 = ipv4.decode("utf-8")
ipv4 = ipv4.split()[0]

#Get the ipv6 address from the linux dig command
ipv6 = subprocess.Popen("dig TXT +short o-o.myaddr.l.google.com @ns1.google.com", shell=True, stdout=subprocess.PIPE).communicate()[0]
ipv6 = ipv6.decode("utf-8")
#The ipv6 address comes back with double qoutes so strip them
ipv6 = re.findall(r'"([^"]*)"', ipv6)[0]

sio.emit("camera-connection", {"ipv4": ipv4, "ipv6": ipv6, "cameraID": cameraID})
