#!/usr/bin/python

import sys
import rrdtool
import os.path
import smtplib
import tempfile
import time
import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

data_sources = [
  "DS:temperature:GAUGE:120:-50:100",
  "DS:humidity:GAUGE:120:0:100" ]

rrdfile = "/root/temperature/data.rrd"
Debug = True

From = "me@host.com"
To = "you@host.com"
Subject = "Daily Report"

def makeGraph():
  DAY = 86400
  YEAR = 365 * DAY
  fd,path = tempfile.mkstemp('.png')

  rrdtool.graph(path,
              '--imgformat', 'PNG',
              '--width', '800',
              '--height', '600',
              '--start', "-%i" % DAY * 7,
              '--end', "-1",
              '--vertical-label', 'Temperatur/Woche',
              '--title', 'Temperatur/Woche',
              '--lower-limit', '0',
              "DEF:temperature=%s:temperature:AVERAGE" % rrdfile,
              'AREA:temperature#990033:Temperature')

  now = datetime.datetime.now()

  secondsFromMidnight = now.hour * 60 * 60
  secondsFromMidnight += (now.minute * 60)
  secondsFromMidnight += now.second

  secondsFromMonth = secondsFromMidnight + (now.day + 86400)

#print time.mktime(datetime.datetime(now.year, now.month, now.day).timetuple())

  fd,path1 = tempfile.mkstemp('.png')
  rrdtool.graph(path1,
              '--imgformat', 'PNG',
              '--width', '800',
              '--height', '600',
              '--start', "-%i" % secondsFromMidnight,
              '--end', "-1",
              '--vertical-label', 'Temperatur/Tag',
              '--title', 'Temperatur/Tag',
              '--lower-limit', '0',
              "DEF:temperature=%s:temperature:AVERAGE" % rrdfile,
              'AREA:temperature#990033:Temperature')

  fd,path2 = tempfile.mkstemp('.png')
  rrdtool.graph(path2,
              '--imgformat', 'PNG',
              '--width', '800',
              '--height', '600',
              '--start', "-%i" % YEAR,
              '--end', "-1",
              '--vertical-label', 'Temperatur/Jahr',
              '--title', 'Temperatur/Jahr',
              '--lower-limit', '0',
              "DEF:temperature=%s:temperature:AVERAGE" % rrdfile,
              'AREA:temperature#990033:Temperature')

  fd,path3 = tempfile.mkstemp('.png')
  rrdtool.graph(path3,
              '--imgformat', 'PNG',
              '--width', '800',
              '--height', '600',
              '--start', "-%i" % secondsFromMonth,
              '--end', "-1",
              '--vertical-label', 'Temperatur/Monat',
              '--title', 'Temperatur/Monat',
              '--lower-limit', '0',
              "DEF:temperature=%s:temperature:AVERAGE" % rrdfile,
              'AREA:temperature#990033:Temperature')

  return([path1, path, path3, path2])


def sendEmail():
  msg = MIMEMultipart()
  msg['Subject'] = Subject
  msg['To'] = To
  msg['From'] = From
  
  for file in makeGraph():
    print file
    if os.path.exists(file) == True:
      fp = open(file, "rb")
      img = MIMEImage(fp.read())
      fp.close()
      msg.attach(img)
      os.remove(file)

  s = smtplib.SMTP_SSL("smtp.host.com", 465)
  s.login("smtpauth@host.com", "password");
  s.sendmail(msg["From"], msg["To"], msg.as_string())


def createDatabase():
  if os.path.exists(rrdfile) == False:
    if Debug:
      print "Creating rrdfile"
    rrdtool.create(rrdfile, 
      "--step", "60",
      data_sources,
      "RRA:AVERAGE:0.5:1:1440",
      "RRA:MIN:0.5:1:1440",
      "RRA:MAX:0.5:1:1440",
      "RRA:AVERAGE:0.5:30:17520",
      "RRA:MIN:0.5:30:17520",
      "RRA:MAX:0.5:30:17520")


def read_temperature():
  tfile = open("/sys/bus/w1/devices/10-0008010fe123/w1_slave")
  text = tfile.read()
  tfile.close()

  lines = text.split("\n")

  if lines[0].find("YES") > 0:
    temp = float((lines[1].split(" ")[9])[2:]) / 1000
    return temp
    
  return MIN_TEMP-1


def getSensors():
  file = open('/sys/devices/w1_bus_master1/w1_master_slaves')
  slaves = file.readlines()
  file.close()
  return(slaves.split("\n"))

def update():
  current_temp = read_temperature()
  if current_temp >= -50:
    rrdtool.update(rrdfile, "N:%f:%s" % (current_temp, 0))


def main(argv):
  if len(argv) < 2:
    sys.stderr.write("Usage: %s ...\n" % (argv[0]))
    return 1

  if argv[1] == "update":
    update()
    return 0

  if argv[1] == "mail":
    sendEmail()
    return 0
  
  return 255

if __name__ == "__main__":
  sys.exit(main(sys.argv))
