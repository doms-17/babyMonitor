import json
from MyMQTT import* 
import time
import requests
from RaspberrySubscriber import *

class Publisher: 
    def __init__(self,clientID,deviceID,broker,port): 
        self.clientID=clientID
        self.client=MyMQTT(clientID,broker,port,None) 
        self.deviceID=deviceID

     
    def start (self): 
        self.client.start() 
 
    def stop (self): 
        self.client.stop() 
 
    def publish(self,topic,message): 
        self.client.myPublish(topic,message) 
        print(f'Published with topic: {topic}')
    
    def publishAlarm(self,topic, deviceID, timestamp, duration, eventType):
        message={ 
                        "topic": topic,
                        "e":
                        { 
                            "deviceID": deviceID,  
                            "timestamp": timestamp,
                            "duration": duration,
                            "unitOfMeasurement":"s",
                            "eventType": eventType
                
                        }      
                    }
        self.client.myPublish(topic,message)
        print(f'Published Alarm with topic: {topic}')
    
            
            
        
if __name__ == "__main__":
    ## read configuration data from the file on the raspberry 
    conf=json.load(open("configurationDevice.json"))
    mosquitto = requests.get(conf['urlCatalog']+ 'getMosquittoConf')
    mosquitto=mosquitto.json()
    mosquitto=json.loads(mosquitto)
    
    broker=mosquitto["broker"]
    deviceID=conf['deviceID']
    port=mosquitto["port"]
    urlCatalog=conf['urlCatalog']

    ### create lists of data sensors read from sensors files
    filename_acc='acceleration.txt'   
    acc_list=[] 
    with open(filename_acc,'r') as fp: 
        for line in fp: 
            acc_list.append(line)
    filename_hr='heart_rate.txt'   
    hr_list=[] 
    with open(filename_hr,'r') as fp: 
        for line in fp: 
            hr_list.append(line)
    filename_resp='respiration.txt'   
    resp_list=[] 
    with open(filename_resp,'r') as fp: 
        for line in fp: 
            resp_list.append(line) 
    filename_oxy='oxygen_level.txt'   
    oxy_list=[] 
    with open(filename_oxy,'r') as fp: 
        for line in fp: 
            oxy_list.append(line)    
    
    ### Get Channel ID of ThingSpeak
    result=requests.get(urlCatalog+"getChannelID/"+str(deviceID))
    print(result.json())
    data=result.json()
    data=json.loads(data)
    channelID=data["channelID"]   

    ########## Create subscriber to receive events from the services 
    ########## and publish an alarm on the bot 

    topicAlarm = mosquitto["topicAlarm"]
    topicEvent=mosquitto["topicEvent"]+"#"
    raspberrySubscriber= Event("Raspberry_subscriber",topicEvent,broker,port,deviceID,topicAlarm)
    raspberrySubscriber.start()

    ########## Create two publisher to publish to the services ##########
    raspberryToApnea = Publisher('Apnea_service',deviceID,broker,port)
    raspberryToSeizure = Publisher('Seizure_service',deviceID,broker,port)
    raspberryToApnea.client.start()
    raspberryToSeizure.client.start()
    
   
    mosquitto=requests.get(conf["urlCatalog"]+"getMosquittoConf")
    mosquitto= mosquitto.json()
    mosquitto=json.loads(mosquitto)
    topicApnea = mosquitto['topicApnea']
    topicSeizure = mosquitto['topicSeizure']
    
    ####################################################
    ## retrieve ThingSpeak url and api_key 
    #url="https://api.thingspeak.com/update.json"
    url=requests.get(urlCatalog+"getThingSpeakUrl/")
    url= url.text
    url=url.replace('"',"")
    apiKey=requests.get(urlCatalog+"getThingSpeakWriteApiKey/"+str(deviceID))
    apiKey=apiKey.text
    apiKey=apiKey.replace('"',"")



    while(1):
        for acc, hr, resp, oxy in zip(acc_list, hr_list, resp_list, oxy_list):
            time.sleep(1)
            ## create seizure message to be sent
            seizureMessage={ 
                "bn": deviceID,
                "e":[
                { 
                    "n": "heartrate",
                    "u": "bpm",
                    "t": time.time(),
                    "v": hr
                },
                { 
                    "n": "oxylevel",
                    "u": "",
                    "t": time.time(),
                    "v": oxy
                },
                { 
                    "n": "acceleration",
                    "u": "m/s^2", 
                    "t": time.time(),
                    "v": acc
                }
                ]
            }
            ## create apnea message to be sent
            apneaMessage={
				"bn": deviceID,
                "e":[
                { 
                    "n": "respiration",
                    "u": "",
                    "t": time.time(),
                    "v": resp
                },
                { 
                    "n": "oxylevel",
                    "u": "",
                    "t": time.time(),
                    "v": oxy
                }
                ]   
            }
            ## publish the messages to the services
            raspberryToApnea.publish(topicApnea+str(deviceID),apneaMessage)
            raspberryToSeizure.publish(topicSeizure+str(deviceID),seizureMessage)
            
            
            ### post data to personal ThinkSpeak channel
            
            params={
                "api_key": apiKey,
                "field1": hr,
                "field2": oxy
            }
            requests.post(url,params=params)
            

