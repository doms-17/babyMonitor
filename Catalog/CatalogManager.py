import json
from logging import raiseExceptions
from datetime import datetime
import random
import requests
import time

class CatalogManager:
    def __init__(self):
        self.catalog_filename = 'catalog.json'
        with open(self.catalog_filename) as f:
            self.data = json.load(f)
            self.modified=0
        self.device_template_filename = 'device_template.json'
        with open(self.device_template_filename) as f:
            self.device_temp = json.load(f)
        self.userAPIKey = self.data["thingSpeak"]["userAPIKey"]
        pass

    def printAll(self):
        print(self.data)

    ###############################
    ########## SERVICES ###########
    ###############################

    def getServicesStatus(self):
        return json.dumps(self.data['onlineServices'])

    def removeServices(self):
        for service in self.data['onlineServices']:
                actualTimestamp = time.time()
                if actualTimestamp-service['timestamp'] > 300:
                    #remove the service because it did not update the status (timestamp)
                    self.data['onlineServices'].remove(service)
                    print("Service "+service["id"])
        self.save(self.catalog_filename)
                
    def updateService(self,id,url,timestamp):
        serviceFound=False
        for service in self.data['onlineServices']:
            if id == service['id']:
                 #aggiorna timestamp
                service['timestamp']=timestamp
                self.save(self.catalog_filename)
                serviceFound=True
        
        if serviceFound == False:
            #service not present in the list, add it
            self.setServiceOnline(id,url,timestamp)

        self.save(self.catalog_filename)

    def setServiceOnline(self,id,url,timestamp):
        
        service = {
            "id":id,
            "url":url,
            "timestamp":timestamp
        }
        self.data['onlineServices'].append(service)
        self.save(self.catalog_filename)
        
    def getMosquittoConf(self):
        conf = self.data['mosquitto']
        return json.dumps(conf)

    def getThingSpeakUrl(self):
        url = self.data['thingSpeak']['url']
        return url

    def getThingSpeakApiKey(self):
        apiKey = self.data['thingSpeak']['userAPIKey']
        return apiKey

    def getThingSpeakWriteApiKey(self,deviceID):
        for child in self.data['childrenList']:
            if child['deviceID']==deviceID:
                for api in child['tsChannel']['tsApiKeys']:
                    if api['write_flag']:
                        writeApiKey=api['api_key']
                        return writeApiKey
        
    def getTopicApnea(self):
        topicApnea = self.data['mosquitto']['topicApnea']
        return json.dumps(topicApnea)

    def getTopicSeizure(self):
        topicSeizure = self.data['mosquitto']['topicSeizure']
        return json.dumps(topicSeizure)   
    
    
    #########################################################
    ########## FUNCTIONS TO MANAGE DB's USER DATA ###########
    #########################################################
    

    ## insert new child in the DB ##
    
    def insertChild(self,username,password,name,surname,chatID,deviceID):
        lastChildID = self.data['lastChildID']+1
        
         ### ThingSpeak
        url = self.data['thingSpeak']['urlChannel']
        params = {
            "api_key":self.userAPIKey,
            "name":username,
            "field1":"Heartrate",
            "field2":"Blood Oxygen Level",
            "public_flag": True
        }
        request=requests.post(url,params=params)
        dataTS = request.json()
        tsID = dataTS["id"]
        tsApiKeys = dataTS["api_keys"]

        newChild = {
            "username" : username,
            "password" : password,
            "childName": name,
            "childSurname" : surname,
            "childID": lastChildID,
            "chatID": chatID,
            "deviceID": int(deviceID),
            "tsChannel": {
                "id":tsID,
                "tsApiKeys":tsApiKeys
            }   
            
        }
        #print(newChild)
        self.data['childrenList'].append(newChild)
        self.insertDevice(deviceID,lastChildID)
        # update global ID 
        self.data['lastChildID'] = lastChildID
        # save modified catalog
        self.save(self.catalog_filename)

    ## insert new device in the DB ##

    def insertDevice(self,deviceID,childID):
        new_device = self.device_temp
        new_device['deviceID'] = int(deviceID)
        new_device['childID'] = childID

        microphoneID = str(deviceID) + "-" + str(random.randint(1000,9999))
        new_device['sensorsList'][0]['sensorID'] = microphoneID
        oximeterID = str(deviceID) + "-" + str(random.randint(1000,9999))
        new_device['sensorsList'][1]['sensorID'] = oximeterID
        accelerometerID = str(deviceID) + "-" + str(random.randint(1000,9999))
        new_device['sensorsList'][2]['sensorID'] = accelerometerID
        heartrateID = str(deviceID) + "-" + str(random.randint(1000,9999))
        new_device['sensorsList'][3]['sensorID'] = heartrateID
        temperatureID = str(deviceID) + "-" + str(random.randint(1000,9999))
        new_device['sensorsList'][4]['sensorID'] = temperatureID
        humidityID = str(deviceID) + "-" + str(random.randint(1000,9999))
        new_device['sensorsList'][5]['sensorID'] = humidityID

        self.data['devicesList'].append(new_device)
        return
    
    def getChildren(self):
        childrenList=self.data["childrenList"]
        return json.dumps(childrenList)

    def getChannelID(self,deviceID):
        childrenList=self.data["childrenList"]
        for child in childrenList:
            if child["deviceID"]==deviceID:
                channelID=child["tsChannel"]["id"]
                return channelID
    
    def getDevices(self):
        devicesList=self.data["devicesList"]
        return json.dumps(devicesList)
    
    def getChildData(self,chatID):
        for child in self.data["childrenList"]:
            if child["chatID"]==chatID:
                return json.dumps(child)

    ## modify account information ##
    
    def modifyAccount(self,chatID,option,value):
        for child in self.data['childrenList']:
            if child['chatID'] == chatID:
                if option =="name": 
                        child["childName"]=value
                        self.save(self.catalog_filename)
                        return
                elif option =="surname":
                        child["childSurname"]=value
                        self.save(self.catalog_filename)
                        return
                elif option =="username":
                        child["username"]=value
                        self.save(self.catalog_filename)
                        return
                if option == "password":
                        child["password"]=value
                        self.save(self.catalog_filename)
                        return
                    
    
    ## delete the account and the device from the catalog ## 
    ## delete personal Thingspeak channel with a delete request ##

    def deleteAccount(self,chatID):
        for child in self.data['childrenList']:
            if child['chatID'] == chatID:
                deviceID = child['deviceID']
                url = "https://api.thingspeak.com/channels/"+str(child["tsChannel"]["id"])+".json"
                try:
                    self.data['childrenList'].remove(child)
                    for device in self.data['devicesList']:
                        if device['deviceID'] == deviceID:
                            try:
                                self.data['devicesList'].remove(device)
                                try:
                                    params = {
                                        "api_key":self.userAPIKey
                                    }
                                    requests.delete(url,params=params)
                                    self.save(self.catalog_filename)
                                except raiseExceptions:
                                    print("Device not removed correctly")
                            except raiseExceptions:
                                    print("Device not removed correctly")
                except raiseExceptions:
                    print("Child not removed correctly")

        


        

    #################################################
    ### function that saves data in catalog.json ####
    #################################################

    def save(self,filename):
            self.data['lastUpdate']=datetime.today().strftime("%Y-%m-%d-%H:%M:%S")
            json_file=json.dumps(self.data,indent=4)
            with open(filename,'w') as f:
                f.write(json_file)
        


