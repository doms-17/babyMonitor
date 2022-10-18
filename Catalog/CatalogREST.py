import json
import cherrypy
import time
from CatalogManager import CatalogManager

class CatalogREST:
    exposed=True
    def __init__(self):
        self.CatalogManager=CatalogManager()
    
    @cherrypy.tools.json_out()
    def GET(self,*uri,**params):
        if ''.join(uri[0])=='':
            return "Welcome to MyBabyMonitor server"
        elif ''.join(uri[0])=='getChildren':
            childrenList= self.CatalogManager.getChildren()
            return childrenList
        elif ''.join(uri[0])=='getChannelID':
            deviceID=int(uri[1])
            channelID=self.CatalogManager.getChannelID(deviceID)
            response={
                "channelID": channelID
            }
            print(response)
            return json.dumps(response)
        elif ''.join(uri[0])=='getMosquittoConf':
            return self.CatalogManager.getMosquittoConf()
        elif ''.join(uri[0])=='getThingSpeakUrl':
            return self.CatalogManager.getThingSpeakUrl()
        elif ''.join(uri[0])=='getThingSpeakApiKey':
            return self.CatalogManager.getThingSpeakApiKey()
        elif ''.join(uri[0])=='getTopicApnea':
            return self.CatalogManager.getTopicApnea()
        elif ''.join(uri[0])=='getChildData':
            chatID=int(uri[1])
            return self.CatalogManager.getChildData(chatID)
        elif ''.join(uri[0])=='getTopicApnea':
            return self.CatalogManager.getTopicSeizure()
        elif ''.join(uri[0])=='getThingSpeakWriteApiKey':
            deviceID=int(uri[1])
            return self.CatalogManager.getThingSpeakWriteApiKey(deviceID)
        elif ''.join(uri[0])=='getServicesStatus':
            return self.CatalogManager.getServicesStatus()
    
        
    @cherrypy.tools.json_in()
    def POST(self,*uri,**params):
        #print(uri)
        if ''.join(uri[0])=='insertChild':
            newChild=cherrypy.request.json
            newChild=json.loads(newChild)
            username=newChild["username"]
            password=newChild["password"]
            name=newChild["name"]
            surname=newChild["surname"]
            chatID=newChild["chatID"]
            deviceID=newChild['deviceID']
            self.CatalogManager.insertChild(username,password,name,surname,chatID,deviceID)
        elif ''.join(uri[0])=='updateService':
            service=cherrypy.request.json
            service=json.loads(service)
            id=service["id"]
            print("Update service: " + id)
            url=service['url']
            timestamp=service['timestamp']
            self.CatalogManager.updateService(id,url,timestamp)
    
    @cherrypy.tools.json_in()
    def PUT(self,*uri,**params):
        #print(uri)
        if ''.join(uri[0])=='insertEvent':
            newEvent=cherrypy.request.json
            newEvent=json.loads(newEvent)
            #print(newEvent)
            chatID = newEvent['chatID']
            eventType = newEvent['eventType']
            duration = newEvent['duration']
            timestamp = newEvent['timestamp']
            self.CatalogManager.insertEvent(chatID, eventType, duration, timestamp)
        elif ''.join(uri[0])=='modifyAccount':
            #print(uri)
            newModify= cherrypy.request.json
            newModify=json.loads(newModify)
            chatID = newModify["chatID"]
            option=newModify["option"]
            value=newModify["value"]
            self.CatalogManager.modifyAccount(chatID,option,value)
    def DELETE(self, *uri, **params):
        #print(uri)
        if ''.join(uri[0])=='deleteAccount':
            chatID = int(uri[1])
            self.CatalogManager.deleteAccount(chatID)
    

if __name__=="__main__":
    conf={
        '/':{
            'request.dispatch':cherrypy.dispatch.MethodDispatcher(), 
            'tool.session.on':True
        } 
    }
    catalog = CatalogREST()
    cherrypy.tree.mount(catalog,'/',conf)
    cherrypy.config.update(conf)
    cherrypy.config.update({'server.socket_host':'0.0.0.0'})
    cherrypy.engine.start()

    # check periodically if the service is online, otherwise delete it from the catalog
    while(True):
        catalog.CatalogManager.removeServices()
        time.sleep(100)
