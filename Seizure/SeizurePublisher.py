from MyMQTT import* 

class SeizurePublisher: 
    def __init__(self,clientID,topic,broker,port):
        self.topic=topic 
        self.clientID=clientID
        self.client=MyMQTT(clientID,broker,port,None) 

     
    def start (self): 
        self.client.start() 
 
    def stop (self): 
        self.client.stop() 
 
    def publish(self,deviceID,timestamp,duration): 

        message={ 
                        "id": self.clientID,
                        "topic": self.topic,
                        "e":
                        { 
                            "eventType": "Seizure",
                            "deviceID": deviceID,  
                            "timestamp": timestamp,
                            "duration": duration
                        }      
                    }
        self.client.myPublish(self.topic,message) 
        print(f'Published with {self.topic}')
        
