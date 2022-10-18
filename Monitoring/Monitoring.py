import json
import requests
import cherrypy
from MyMQTT import* 
from datetime import datetime
import time
from Website import create_app

import threading


class MonitoringService:
    def __init__(self, clientID, topic,broker,port):
        self.client=MyMQTT(clientID,broker,port,self)
        self.topic=topic
        self.port=port
        self.broker=broker
        self.databaseFilename = "MonitoringDB.json"
        self.monitoringDatabase = json.load(open(self.databaseFilename))
        
    def start (self):
        self.client.start()
        self.client.mySubscribe(self.topic)
    
    def stop (self):
        self.client.stop()
    
    def notify(self,topic,msg):
        d=json.loads(msg)
        if "Duration" in topic:
            eventType=d['e']['eventType']
            deviceID=d['e']['deviceID']
            timestamp=d['e']['timestamp']
            duration=d['e']['duration']
            print(f"Event type: {eventType}, Time: {timestamp}, Device: {deviceID}, Duration: {duration}")
            ##### insert new event in the DB #####
            self.insertEvent(deviceID,timestamp,duration,eventType)
        	

    def insertEvent(self,deviceID,timestamp,eventDuration,eventType):
        deviceFound = False
        eventDuration = int(eventDuration)
        dateAndTime=timestamp.split(":")[0]
        timestamp=str(timestamp)
        sec=int(timestamp.split(":")[-1])
        min=int(timestamp.split(":")[1])
        if (sec - eventDuration)<0:
            sec = (sec+60) - eventDuration
            min -= 1
        else:
            sec -= eventDuration    
        timestamp= str(dateAndTime) + ":" + str(min) + ":" + str(sec)

        newDevice = {
                "deviceID": deviceID,
                "events": {
                    "apnea":[],
                    "seizure":[]
                }
            }

        event = {
                "time": timestamp,
                "duration": eventDuration
            }

        for device in self.monitoringDatabase['devices']:
            if deviceID==device['deviceID']:
                if eventType=='Apnea':
                    device['events']['apnea'].append(event)
                    deviceFound = True
                elif eventType=='Seizure':
                    device['events']['seizure'].append(event)
                    deviceFound = True

        if deviceFound == False:
            if eventType=='Apnea':
                newDevice['events']['apnea'].append(event)
                self.monitoringDatabase['devices'].append(newDevice)
            elif eventType=='Seizure':
                newDevice['events']['seizure'].append(event)
                self.monitoringDatabase['devices'].append(newDevice)

        
        self.save(self.databaseFilename)
        
    def save(self,filename):
        self.monitoringDatabase['lastUpdate']=datetime.today().strftime("%Y-%m-%d-%H:%M:%S")
        json_file=json.dumps(self.monitoringDatabase,indent=4)
        with open(filename,'w') as f:
            f.write(json_file)    

    
def loopUpdateService(url,urlMonitoring):
   
    data = {
            'id':'Monitoring',
            'url': urlMonitoring,
            'timestamp': time.time()
        }   
    while(True):
        data["timestamp"]=time.time()
        print(url)
        requests.post(url,json=json.dumps(data))
        time.sleep(100)

if __name__ == "__main__":


    conf=json.load(open("MonitoringDB.json"))
    mosquitto = requests.get(conf['urlCatalog']+ 'getMosquittoConf')
    mosquitto=mosquitto.json()
    mosquitto=json.loads(mosquitto)
    
    broker=mosquitto["broker"]
    port=mosquitto["port"]
    topic = mosquitto["topicAlarm"]+"#"
    monitoring= MonitoringService("Monitoring_subscriber",topic,broker,port)

    url_catalog= conf["urlCatalog"]
    url= url_catalog + 'updateService'
    urlMonitoring=conf["urlMonitoring"]
    
    monitoring.start()
    app = create_app()

    t=threading.Thread(target=loopUpdateService, args=(url,urlMonitoring,))
    t.start()

     ##### run website ####
    app.run(host='0.0.0.0',port=5000,debug=True,use_reloader=False)
   
        
