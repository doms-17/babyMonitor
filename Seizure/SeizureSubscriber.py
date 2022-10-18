import json
from MyMQTT import* 
from SeizurePublisher import*
from datetime import datetime
import cherrypy
import time
import requests

class SeizureSubscriber:
    exposed=True
    def __init__(self, clientID, topic,topicEvent,broker,port):
        self.client=MyMQTT(clientID,broker,port,self)
        self.topic=topic
        self.topicEvent = topicEvent
        self.port=port
        self.broker=broker
        self.databaseFilename="SeizureDB.json"
        self.event=SeizurePublisher("seizure_service","MyBabyMonitor/Event/",self.broker,self.port)
        self.event.client.start()
        self.dataCollector = {}
        self.seizureDatabase = json.load(open(self.databaseFilename))
                   
    def start (self):
        self.client.start()
        self.client.mySubscribe(self.topic)
    def stop (self):
        self.client.stop()
    def notify(self,topic,msg):
        d=json.loads(msg)
        heart_rate=float(d['e'][0]['v'])
        oxy_level=float(d['e'][1]['v'])
        acceleration=float(d['e'][2]['v'])
        deviceID=d['bn']
        timestamp=datetime.today().strftime("%Y-%m-%d-%H:%M:%S")
        print(f"Data: \n\thr: {heart_rate} \n\toxy: {oxy_level} \n\tacc: {acceleration}")
       
        
        if(self.dataCollector.get(deviceID)!=None):
            eventFound = self.dataCollector[deviceID]["eventFound"]
            eventDuration = self.dataCollector[deviceID]["eventDuration"]
            eventStop = self.dataCollector[deviceID]["eventStop"]
           # print(f"Event stop {eventStop} event found flag")
            eventFoundFlag = self.dataCollector[deviceID]["eventFoundFlag"]
           # print(eventFoundFlag)
            lastSample = self.dataCollector[deviceID]["lastSample"]

            
            if eventFoundFlag and acceleration < 3 and eventStop == 0:
                eventStop+=1
                self.dataCollector[deviceID]["eventStop"]=eventStop
                self.dataCollector[deviceID]["lastSample"] = acceleration
                self.dataCollector[deviceID]["eventDuration"] += 1
            elif eventFoundFlag and acceleration < 3 and lastSample < 3 and eventStop !=0:    
                eventStop+=1
                self.dataCollector[deviceID]["eventStop"]=eventStop
                self.dataCollector[deviceID]["lastSample"] = acceleration
                self.dataCollector[deviceID]["eventDuration"] += 1

                if eventStop > 2:
                    
                    #### Publish Event Duration to the Device
                    self.event.topic = self.topicEvent+str(deviceID)+'/Duration'
                    self.event.publish(deviceID,timestamp,eventDuration)
                    
                    #### Insert New Event
                    self.insertEvent(deviceID,timestamp,eventDuration)
                    
                    self.dataCollector[deviceID]["eventFoundFlag"] = False
                    self.dataCollector[deviceID]["eventStop"] = 0
                    self.dataCollector[deviceID]["eventFound"] = 0
                    self.dataCollector[deviceID]["lastSample"] = acceleration
                    self.dataCollector[deviceID]["eventDuration"] = 5
            elif acceleration>=3:
                eventFound+=1
                self.dataCollector[deviceID]["eventFound"]=eventFound
                if heart_rate>=160 and oxy_level<95 and eventFound>=5 and not eventFoundFlag:
                    print("Seizure event found")
                    
                    #### Publish Event start to the Device
                    self.event.topic = self.topicEvent+str(deviceID)
                    self.event.publish(deviceID,timestamp,eventDuration)
                    
                    self.dataCollector[deviceID]["eventFoundFlag"] = True
                    self.dataCollector[deviceID]["eventFound"] = eventFound
                    self.dataCollector[deviceID]["lastSample"] = acceleration
                elif heart_rate>=160 and oxy_level<95 and eventFound>=5 and eventFoundFlag:
                    self.dataCollector[deviceID]["eventDuration"] += 1
                    self.dataCollector[deviceID]["lastSample"] = acceleration
                    if eventStop > 0:
                        self.dataCollector[deviceID]["eventStop"] = 0
                    
            else:
                self.dataCollector[deviceID]["eventFound"]=0
                self.dataCollector[deviceID]["eventFoundFlag"] = False
                self.dataCollector[deviceID]["eventDuration"] = 5
                self.dataCollector[deviceID]["eventStop"] = 0
                self.dataCollector[deviceID]["lastSample"] = acceleration
        else: 
            #self.dataCollector[deviceID]=0 #qui inseriamo il device ID nel dizionario a 0    
            self.dataCollector[deviceID]={}
            self.dataCollector[deviceID]["eventFound"] = 0
            self.dataCollector[deviceID]["eventFoundFlag"] = False
            self.dataCollector[deviceID]["eventDuration"] = 5
            self.dataCollector[deviceID]["eventStop"] = 0
            self.dataCollector[deviceID]["lastSample"] = acceleration   
        
        #print(self.dataCollector.get(deviceID))        
    
    def insertEvent(self,deviceID,timestamp, eventDuration):
        deviceFound=False    
        eventDuration = int(eventDuration)
        timestamp=str(timestamp)
        dateAndTime=timestamp.split(":")[0]
        sec=int(timestamp.split(":")[-1])
        min=int(timestamp.split(":")[1])
        if (sec - eventDuration)<0:
            sec = (sec+60) - eventDuration
            min -= 1
        else:
            sec -= eventDuration    
        timestamp= str(dateAndTime) + ":" + str(min) + ":" + str(sec)
        
        newDevice= {
                "deviceID":deviceID,
                "events":[]
            }
        event=  {
                        "time": timestamp,
                        "duration": eventDuration
                }
        
        for device in self.seizureDatabase["devices"]:
            if deviceID == device["deviceID"]:
                device["events"].append(event)
                deviceFound=True
        if deviceFound==False:
            newDevice["events"].append(event)
            self.seizureDatabase["devices"].append(newDevice)
        
        self.save(self.databaseFilename)
        
        
            
    def save(self,filename):
        self.seizureDatabase['lastUpdate']=datetime.today().strftime("%Y-%m-%d-%H:%M:%S")
        json_file=json.dumps(self.seizureDatabase,indent=4)
        with open(filename,'w') as f:
            f.write(json_file)
        
               

if __name__ == "__main__":  
    conf=json.load(open("SeizureDB.json"))
    mosquitto=requests.get(conf["urlCatalog"]+"getMosquittoConf")
    mosquitto= mosquitto.json()
    mosquitto=json.loads(mosquitto)
   
    broker=mosquitto["broker"]
    port=mosquitto["port"]
    topic=mosquitto["topicSeizure"]+"#"
    topicEvent=mosquitto['topicEvent']
    seizure= SeizureSubscriber("seizure_subscriber",topic,topicEvent,broker,port)
    seizure.start()
    
    confCherrypy={
        '/':{
            'request.dispatch':cherrypy.dispatch.MethodDispatcher(), 
            'tool.session.on':True
        } 
    }
    cherrypy.tree.mount(seizure,'/',confCherrypy)
    cherrypy.config.update(confCherrypy)
    cherrypy.config.update({'server.socket_host':'0.0.0.0'})
    cherrypy.config.update({
        "server.socket_port": conf["port"]
    })
    cherrypy.engine.start()
    #cherrypy.engine.block()      
    
    url_catalog= conf["urlCatalog"]
    url= url_catalog + 'updateService'
    data = {
            'id':'Seizure',
            'url': conf["urlSeizure"],
            'timestamp': time.time()
        }
    while True:
        data["timestamp"]=time.time()
        #print(url)
        requests.post(url,json=json.dumps(data))
        time.sleep(100)
                    
                
            
            
  