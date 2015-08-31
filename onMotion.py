#!/usr/bin/python3

'''
Script to look for new webcam images created by the motion program and email
them via GMail.

At the time of writing, you need to switch your Google account onto 
'Allow less secure apps: ON'.  Therefore it's recommended to set up a new
GMail account specifically for this script so that the impact of your
account getting compromised is limited to only seeing your webcam images.

You want to run this script from the on_event_end trigger in /etc/motion.conf.

This script takes a configuration file as a parameter - by default it will
read 'config.json' from the same directory in which this script is located.

'''


from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import datetime
import json
import os
import smtplib
import sys

lastFileName = 'lastfile.txt'

class Config():
    
    def __init__(self, configFile):
        with open(configFile) as fhIn:
            data = json.load(fhIn)
            self.webcamDir = data['webcam_dir']
            self.subject = data['subject']
            self.gmailAddress = data['gmail_address']
            self.gmailPassword = data['gmail_password']
            self.recipients = data['recipients']
            self.maxDays = int(data['max_days'])
    
    def getWebcamDir(self):
        return self.webcamDir
    
    def getGmailAddress(self):
        return self.gmailAddress
    
    def getGmailPassword(self):
        return self.gmailPassword
    
    def getSubject(self):
        return self.subject
    
    def getRecipients(self):
        return self.recipients

    def getMaxDays(self):
        return self.maxDays

def sendEmail(webcamDir, gmailAddress, gmailPassword, subject, recipients, 
    files):

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(gmailAddress, gmailPassword)
    
    msg = MIMEMultipart()
    msg['Subject'] = subject 
    msg['From'] = gmailAddress
    msg['To'] = ', '.join(recipients)

    for file in files:
        with open(webcamDir + '/' + file, 'rb') as fp:
            img = MIMEImage(fp.read())
        msg.attach(img)
    
    try:
        server.sendmail(gmailAddress, recipients, msg.as_string())
        print ('email sent')
    except:
        print ('error sending mail')
    
    server.quit()

def writeLastFile(webcamDir, fileName):
    with open(webcamDir + '/' + lastFileName, 'w') as fh:
        print(fileName, file=fh)

def readLastFile(webcamDir):
    
    retVal = None
    
    lastFileFullPath = webcamDir + '/' + lastFileName
    if os.path.exists(lastFileFullPath):
        with open(lastFileFullPath) as fh:
            retVal = fh.readline().rstrip()

    
    return retVal

def findNewFiles(webcamDir):

    retVal = []

    lastFile = readLastFile(webcamDir)
    foundLast = False
    files = os.listdir(webcamDir)
    lastJPGFile = None
    for file in sorted(files):
        if file.endswith('.jpg'):
            lastJPGFile = file
            if file == lastFile:
                foundLast = True
            else:
                if foundLast:
                    retVal.append(file)
    if lastJPGFile is not None:
        writeLastFile(webcamDir, lastJPGFile)

    return retVal

def deleteOldFiles(webcamDir, maxDays):
    
    files = os.listdir(webcamDir)
    for file in files:
        if file.endswith('.jpg'):
            curpath = os.path.join(webcamDir, file)
            file_modified = \
                datetime.datetime.fromtimestamp(os.path.getmtime(curpath))
            if datetime.datetime.now() - file_modified > \
                datetime.timedelta(days=maxDays):
                os.remove(curpath)

def main(configFile):
    config = Config(configFile)
    deleteOldFiles(config.getWebcamDir(), config.getMaxDays())
    newFiles = findNewFiles(config.getWebcamDir())
    if len(newFiles) > 0:
        sendEmail(config.getWebcamDir(), config.getGmailAddress(), 
            config.getGmailPassword(), config.getSubject(), 
            config.getRecipients(), newFiles)

if __name__ == "__main__":
    configFile = None
    if len(sys.argv) == 2:
        configFile = sys.argv[1]
    else:
        configFile = os.path.dirname(os.path.realpath(sys.argv[0])) + \
            '/config.json'
    main(configFile)
    
