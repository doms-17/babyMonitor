from MyMQTT import*
import time
from datetime import datetime
import json
from ApneaPublisher import *
import requests
import cherrypy

class ApneaSubscriber:
    def __init__(self, clientID, topic,topicEvent,broker,port):
        self.client=MyMQTT(clientID,broker,port,self)
        self.topic=topic
        self.broker=broker
        self.port=port
        self.topicEvent = topicEvent
        self.event=ApneaPublisher("Apnea_service",self.topicEvent,self.broker,self.port)
        self.event.client.start()
        self.dataCollector = {}
        self.databaseFilename = "ApneaDB.json"
        self.apneaDatabase = json.load(open(self.databaseFilename))

    def start (self):
        self.client.start()
        self.client.mySubscribe(self.topic)
    
    def stop (self):
        self.client.stop()
		
    def notify(self,topic,msg):
        d=json.loads(msg)
        print(d)
        deviceID=d['bn']
        timestamp=datetime.today().strftime("%Y-%m-%d-%H:%M:%S")

        valueResp = int(d['e'][0]['v'])
        valueBLO = int(d['e'][1]['v'])
        print(f"Data received: \n\tresp: {valueResp} \n\tblo: {valueBLO}")
        
        
        ## manage received data and search for an Apnea event ##

        if self.dataCollector.get(deviceID) != None:
            eventFound = self.dataCollector[deviceID]["eventFound"]
            eventDuration = self.dataCollector[deviceID]["eventDuration"]
            eventStop = self.dataCollector[deviceID]["eventStop"]
            lastSample = self.dataCollector[deviceID]["lastSample"]
            eventFoundFlag = self.dataCollector[deviceID]["eventFoundFlag"]

            
            if eventFoundFlag and valueResp > 0 and eventStop == 0:
                eventStop+=1
                self.dataCollector[deviceID]["eventStop"]=eventStop
                self.dataCollector[deviceID]["lastSample"] = valueResp
                self.dataCollector[deviceID]["eventDuration"] += 1

                
            elif eventFoundFlag and valueResp > 0 and lastSample == 1 and eventStop !=0:    
                eventStop+=1
                self.dataCollector[deviceID]["eventStop"]=eventStop
                self.dataCollector[deviceID]["eventDuration"] += 1
                self.dataCollector[deviceID]["lastSample"] = valueResp

                if eventStop > 2:
                    self.event.topic = self.topicEvent+str(deviceID)+'/Duration'

                    ###### Publish event duration to the device ####
                    self.event.publish(deviceID,timestamp,eventDuration)
                    ##### insert new event in the DB #####
                    self.insertEvent(deviceID,timestamp,eventDuration)

                    self.dataCollector[deviceID]["eventFoundFlag"] = False
                    self.dataCollector[deviceID]["eventStop"] = 0
                    self.dataCollector[deviceID]["eventFound"] = 0
                    self.dataCollector[deviceID]["lastSample"] = valueResp
                    self.dataCollector[deviceID]["eventDuration"] = 5
            
            elif valueResp <= 0:
                eventFound+=1
                self.dataCollector[deviceID]["eventFound"]=eventFound
                if valueBLO <= 95 and eventFound >= 5 and not self.dataCollector[deviceID]["eventFoundFlag"]:
                    print("Apnea event found")
                    self.event.topic = self.topicEvent+str(deviceID)

                    #### Publish event start to the device ####
                    self.event.publish(deviceID,timestamp,eventDuration)

                    self.dataCollector[deviceID]["eventFoundFlag"] = True
                    self.dataCollector[deviceID]["eventFound"] = eventFound
                    self.dataCollector[deviceID]["lastSample"] = valueResp
                elif valueBLO < 95 and eventFound >= 5 and self.dataCollector[deviceID]["eventFoundFlag"]:
                    self.dataCollector[deviceID]["eventDuration"] += 1
                    self.dataCollector[deviceID]["lastSample"] = valueResp
                    if eventStop > 0:
                        self.dataCollector[deviceID]["eventStop"] = 0
            else:
                self.dataCollector[deviceID]["eventFound"]=0
                self.dataCollector[deviceID]["eventFoundFlag"] = False
                self.dataCollector[deviceID]["eventDuration"] = 5
                self.dataCollector[deviceID]["eventStop"] = 0
                self.dataCollector[deviceID]["lastSample"] = valueResp
        else: 
            self.dataCollector[deviceID]={}
            #self.dataCollector[deviceID]=0 #qui inseriamo il device ID nel dizionario a 0    
            self.dataCollector[deviceID]["eventFoundFlag"] = False
            self.dataCollector[deviceID]["eventFound"] = 0
            self.dataCollector[deviceID]["eventDuration"] = 5
            self.dataCollector[deviceID]["eventStop"] = 0
            self.dataCollector[deviceID]["lastSample"] = valueResp
        
        #print(self.dataCollector.get(deviceID))    
            

    def insertEvent(self,deviceID,timestamp,eventDuration):
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
                "events":[]
            }

        event = {
                "time": timestamp,
                "duration": eventDuration
            }

        for device in self.apneaDatabase['devices']:
            if deviceID==device['deviceID']:
                device['events'].append(event)
                deviceFound = True

        if deviceFound == False:
            newDevice['events'].append(event)
            self.apneaDatabase['devices'].append(newDevice)
        
        self.save(self.databaseFilename)

    ## write the DB on json file to save ##
    def save(self,filename):
        self.apneaDatabase['lastUpdate']=datetime.today().strftime("%Y-%m-%d-%H:%M:%S")
        json_file=json.dumps(self.apneaDatabase,indent=4)
        with open(filename,'w') as f:
            f.write(json_file)

if __name__ == "__main__":
    conf=json.load(open("ApneaDB.json"))
    mosquitto = requests.get(conf['urlCatalog']+ 'getMosquittoConf')
    mosquitto=mosquitto.json()
    mosquitto=json.loads(mosquitto)

    
    broker=mosquitto['broker']
    port=mosquitto["port"]
    topic=mosquitto['topicApnea']+"#"
    topicEvent = mosquitto['topicEvent']
    apnea = ApneaSubscriber("apnea_subscriber",topic,topicEvent,broker,port)
    apnea.start()

    confCherrypy={
        '/':{
            'request.dispatch':cherrypy.dispatch.MethodDispatcher(), 
            'tool.session.on':True
        } 
    }
    cherrypy.tree.mount(apnea,'/',confCherrypy)
    cherrypy.config.update(confCherrypy)
    cherrypy.config.update({'server.socket_host':'0.0.0.0'})
    cherrypy.config.update({
        "server.socket_port": conf['port']
    })
    cherrypy.engine.start()
    
    #cherrypy.engine.block()  
    url= conf['urlCatalog'] + 'updateService'
    data = {
        'id':'Apnea',
        'url': conf["urlApnea"],
        'timestamp': time.time()
    }
    while True:
        data['timestamp']=time.time()
        requests.post(url,json=json.dumps(data))
        time.sleep(100)
	