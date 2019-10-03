import smtplib, string, subprocess
# Script to get IP Address while running a Raspberry Pi headless.
# pifind.py gets the system parameters you want to know and
# emails them through gmail to a destination of your choice

# INSTALLING pifind
# Add this line to /etc/rc.local
#   python /home/pi/pifind.py
# And place this file, pifind.py in your /home/pi folder, then
#   sudo chmod 755 /home/pi/pifind.py

# Settings
#When editing these lines, remove the <>, but not the quotes
fromaddr = 'livelotminesnodeip@gmail.com'
toaddr  =  'livelotminesnodeip@gmail.com'
#Googlemail login details
username = 'livelotminesnodeip'
password = 'mineslivelot'
output_if = subprocess.Popen("hostname -I", shell=True, stdout=subprocess.PIPE).communicate()[0]
output_if = output_if.decode("utf-8")
output_if = output_if.split()[0]

BODY = string.join((
        "From: %s" % fromaddr,
        "To: %s" % toaddr,
        "Subject: Your RasPi just booted",
        "",
        output_if,
#        output_cpu,
        ), "\r\n")

# send the email
server = smtplib.SMTP('smtp.gmail.com:587')
server.starttls()
server.login(username,password)
server.sendmail(fromaddr, toaddr, BODY)
server.quit()

