import emoji
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import json
import requests
from MyMQTT import *

class MyBabyMonitorBot:
    exposed=True
    def __init__(self, token,urlCatalog, broker, port,topic):
        # Local token
        
        self.tokenBot = token
        self.urlcatalog=urlCatalog
        self.bot = telepot.Bot(self.tokenBot)
        self.signInList=[] #per gestire due utenti che si registrano contemporaneamente 
        self.loginList=[] #per gestire login paralleli
        self.modifyList=[] #lista delle persone che stanno modificando 
        self.usernameList=[]
        self.signInListUsername =[]
        
        self.topic=topic
        self.status=None

        self.broker= broker
        self.port = port
        self._paho_mqtt = PahoMQTT.Client("client_IDBot1", True)
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived

        MessageLoop(self.bot,  {'chat': self.on_chat_message, 'callback_query': self.on_callback_query}).run_as_thread()
                
        self.chatIDs, self.childrenList, self.usernameList=self.updateLists()

        #### keyboards ####
        self.keyboardHome = InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton(text=emoji.emojize(':chart_increasing: Website',use_aliases=True), callback_data='website')],
                                [InlineKeyboardButton(text=emoji.emojize(':gear: Account Settings',use_aliases=True), callback_data='settings')],
                                [InlineKeyboardButton(text=emoji.emojize(':vertical_traffic_light: Services Status',use_aliases=True), callback_data='status_services')],
                                ])

        self.keyboardStart = InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton(text=emoji.emojize('Sign In :bust_in_silhouette:',use_aliases=True), callback_data='signIn')],
                                [InlineKeyboardButton(text=emoji.emojize('Log In :locked_with_pen:',use_aliases=True), callback_data='login')],
                                ])

        self.keyboardSettings = InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton(text=emoji.emojize(':memo: Modify account information',use_aliases=True), callback_data='modify_info')],
                                [InlineKeyboardButton(text=emoji.emojize(':no_mobile_phones: Delete Account',use_aliases=True), callback_data='delete_account')],
                                [InlineKeyboardButton(text=emoji.emojize(':back: Back',use_aliases=True), callback_data='home')],
                                ])
        self.keyboardModify = InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton(text=emoji.emojize(':red_circle: Modify child name',use_aliases=True), callback_data='modify_name'),
                                 InlineKeyboardButton(text=emoji.emojize(':blue_circle: Modify child surname',use_aliases=True), callback_data='modify_surname')],
                                [InlineKeyboardButton(text=emoji.emojize(':purple_circle: Modify username',use_aliases=True), callback_data='modify_username'),
                                 InlineKeyboardButton(text=emoji.emojize(':green_circle: Modify password',use_aliases=True), callback_data='modify_password')],
                                [InlineKeyboardButton(text=emoji.emojize(':back: Back',use_aliases=True), callback_data='settings')],
                                ])
        


    def start(self):
        
        self._paho_mqtt.connect(self.broker, self.port) 
        self._paho_mqtt.loop_start()
        self._paho_mqtt.subscribe(self.topic, 2)
        print(f"Start mqtt with topic {self.topic}")

    def stop(self):
        self._paho_mqtt.unsubscribe(self.topic) 
        self._paho_mqtt.loop_stop() 
        self._paho_mqtt.disconnect()

    def myOnConnect (self, paho_mqtt, userdata, flags, rc):
        print ("Connected to %s with result code: %d" % (self.broker, rc))

    def myOnMessageReceived(self, paho_mqtt , userdata, msg):
        # A new message is received
        self.notify(msg.topic, msg.payload)
    
    def updateServicesStatus(self):
        self.servicesList = requests.get(self.urlcatalog+"getServicesStatus")
        self.servicesList=self.servicesList.json()
        self.servicesList=json.loads(self.servicesList)
        return self.servicesList

    def updateLists(self):
        self.childrenList=requests.get(self.urlcatalog+"getChildren")
        self.childrenList=self.childrenList.json()
        self.childrenList=json.loads(self.childrenList)
                
        self.chatIDs=[child["chatID"] for child in self.childrenList]
        self.usernameList=[child["username"] for child in self.childrenList]
        return self.chatIDs, self.childrenList, self.usernameList
        
    def notify(self,topic,message):
        d=json.loads(message)
        #print(message)

        eventType=d['e']["eventType"]
        deviceID=d['e']['deviceID']
        timestamp=d['e']['timestamp']
        duration=d['e']['duration']
        
        self.chatIDs, self.childrenList, self.usernameList=self.updateLists()
        #print(self.chatIDs)
        #print(self.childrenList)
        if 'Duration' not in topic:
            alarmMsg=f"ALARM: {eventType} event detected at {timestamp}."
        else:
            alarmMsg=f"ALARM: {eventType} event finished at {timestamp}. Duration: {duration} s"
        

        ##### send the alarm to the user ######
        for child in self.childrenList:
            if child['deviceID']==deviceID:
                chatID=child['chatID']
                #print(child)
                #print(chatID)
                self.bot.sendMessage(chatID,alarmMsg,reply_markup=None)
                

   
    def on_chat_message(self, msg):
        content_type, chat_type, chatID = telepot.glance(msg)
        found = False # flag per vedere se abbiamo trovato due persone che si stanno registrando contemporaneamente con lo stesso username
        self.chatIDs,self.childrenList, self.usernameList = self.updateLists()
        message = msg['text']
        #print(chatID)

        if chatID not in self.chatIDs:
            #print("siamo nell'if del chatID")
            if message == "/start":
                self.bot.sendMessage(chatID,text="Welcome to MyBabyMonitorBot")
                self.bot.sendMessage(chatID, 'Choose an option:', reply_markup=self.keyboardStart)
            else:
                for newChild in self.signInList:
                    if  chatID == newChild["chatID"] and newChild["username"]=="":
                        newChild["username"]=message
                        #print(newChild["username"])
                        for child in self.signInList:
                            if child['chatID'] != chatID and child['username'] == newChild["username"] :
                                self.bot.sendMessage(chatID, ("This username already exist, please choose another username:"), reply_markup=None)
                                found=True
                                
                        if found==False:    
                            self.bot.sendMessage(chatID, ("Choose your password: "), reply_markup=None)
                    elif  chatID == newChild["chatID"] and newChild["username"]!="" and  newChild["password"] =="":
                        #print(message)
                        newChild["password"]=message
                        self.bot.sendMessage(chatID, ("Type child's name: "), reply_markup=None)
                        #print(newChild)
                    elif chatID == newChild["chatID"] and newChild["password"]!="" and newChild["name"]=="":
                        newChild["name"]=message
                        #print(newChild["name"])
                        self.bot.sendMessage(chatID, ("Type child's surname: "), reply_markup=None)
                    elif chatID == newChild["chatID"] and newChild["name"]!="" and newChild["surname"]=="":
                        newChild["surname"]=message
                        #print(newChild["surname"])
                        self.bot.sendMessage(chatID, ("Insert the provided device ID number: "), reply_markup=None)

                    elif chatID == newChild["chatID"] and newChild["surname"]!="" and newChild["deviceID"]=="":
                        newChild['deviceID']=message
                        print(newChild)
                        requests.post(self.urlcatalog+"insertChild",json=json.dumps(newChild))
                        self.signInList.remove(newChild)
                        self.chatIDs,self.childrenList, self.usernameList=self.updateLists()
                        #print(self.signInList)
                        self.bot.sendMessage(chatID, 'You have succesfully registered on MyBabyMonitor!', reply_markup=None)
                        self.bot.sendMessage(chatID, 'Choose an option:', reply_markup=self.keyboardStart)
        else:
            if message == "/start":
                self.bot.sendMessage(chatID,text="Welcome to MyBabyMonitorBot")
                self.bot.sendMessage(chatID, 'Choose an option:', reply_markup=self.keyboardStart)
            else:
                for user in self.modifyList:
                    if chatID == user["chatID"]:
                        if user['flagName']:
                            modify={"chatID":chatID,"option":"name","value":message} 
                            requests.put(self.urlcatalog+"modifyAccount",json=json.dumps(modify)) 
                            self.modifyList.remove(user)
                            self.bot.sendMessage(chatID, ("Name correctly modified!"), reply_markup=self.keyboardModify)
                            return
                        elif user['flagSurname']:
                            modify={"chatID":chatID,"option":"surname","value":message} 
                            requests.put(self.urlcatalog+"modifyAccount",json=json.dumps(modify))  
                            self.modifyList.remove(user)
                            self.bot.sendMessage(chatID, ("Surname correctly modified!"), reply_markup=self.keyboardModify)
                            return
                        elif user['flagUsername']:
                            self.signInListUsername=[child["username"] for child in self.signInList]
                            if message not in self.usernameList and message not in self.signInListUsername:
                                modify={"chatID":chatID,"option":"username","value":message} 
                                requests.put(self.urlcatalog+"modifyAccount",json=json.dumps(modify)) 
                                self.modifyList.remove(user)
                                self.bot.sendMessage(chatID, ("Username correctly modified!"), reply_markup=self.keyboardModify)
                                return
                            else:
                                self.bot.sendMessage(chatID, ("This username already exist, please choose another username:"), reply_markup=None)
                                return
                        elif user['flagPassword']:
                            modify={"chatID":chatID,"option":"password","value":message} 
                            requests.put(self.urlcatalog+"modifyAccount",json=json.dumps(modify)) 
                            self.modifyList.remove(user)
                            self.bot.sendMessage(chatID, ("Password correctly modified!"), reply_markup=self.keyboardModify)
                            return
                                    
                for user in self.loginList:
                    if  chatID == user["chatID"] and user["username"]=="":
                        user["username"]=message
                        for child in self.childrenList:
                            if child["chatID"] == chatID:
                                savedUsername=child["username"]
                        if savedUsername==user["username"]:
                            #print(user["username"])
                            self.bot.sendMessage(chatID, emoji.emojize(':key: Insert your password ',use_aliases=True), reply_markup=None)
                        else:
                            user["username"]=""
                            self.bot.sendMessage(chatID, emoji.emojize(":cross_mark: Wrong username, please try again",use_aliases=True) , reply_markup=None)
                            self.bot.sendMessage(chatID,emoji.emojize(":bust_in_silhouette: Insert your username",use_aliases=True) , reply_markup=None)
                    elif chatID == user["chatID"] and user["username"]!="":
                        user["password"]=message
                        for child in self.childrenList:
                            if child["chatID"] == chatID:
                                savedPassword=child["password"]
                        if savedPassword==user["password"]:
                            user["flagLogin"]=True
                            
                            self.bot.sendMessage(chatID, emoji.emojize(":house: Welcome to your home, please select an options!",use_aliases=True), reply_markup=self.keyboardHome)
                            #print(self.loginList)
                            
                        else:
                            user["password"]=""
                            self.bot.sendMessage(chatID, emoji.emojize(":cross_mark: Wrong password, please try again",use_aliases=True) , reply_markup=None)
                            self.bot.sendMessage(chatID, emoji.emojize(':key: Insert your password ',use_aliases=True), reply_markup=None)



                    elif chatID == user["chatID"] and user["username"]!="":
                        user["password"]=message
                        for child in self.childrenList:
                            if child["chatID"] == chatID:
                                savedPassword=child["password"]
                            if savedPassword==user["password"]:
                                self.bot.sendMessage(chatID, emoji.emojize(':key: Insert your password ',use_aliases=True), reply_markup=None)


    def on_callback_query(self, msg):
        self.chatIDs,self.childrenList, self.usernameList = self.updateLists()
        query_id, chatID, query_data= telepot.glance(msg, flavor='callback_query')
        message_id_tuple=telepot.origin_identifier(msg)
        if query_data=='signIn':
            if chatID in self.chatIDs:
                self.bot.sendMessage(chatID, ("You are already registered"), reply_markup=None)
                self.bot.sendMessage(chatID, 'Choose an option:', reply_markup=self.keyboardStart)
            else:    
                self.bot.sendMessage(chatID, ("Choose your username: "), reply_markup=None)
                newChild={ "username": "","password": "","chatID": chatID,"name":"", "surname":"", "deviceID":""} 
                self.signInList.append(newChild)
        elif query_data=='login':
            chatIDs, childrenList, usernameList = self.updateLists()
            if chatID not in chatIDs:
                self.bot.sendMessage(chatID,emoji.emojize(":bust_in_silhouette: You are not registered. Please sign in.",use_aliases=True) , reply_markup=self.keyboardStart)
            else:
                self.bot.sendMessage(chatID,emoji.emojize(":bust_in_silhouette: Insert your username",use_aliases=True) , reply_markup=None)
                user={"username":"","password":"","chatID": chatID, "flagLogin": False} # FLAG LOG IN??? 
                self.loginList.append(user)
        elif query_data=='home':
            self.bot.sendMessage(chatID, emoji.emojize(":house: Welcome to your home, please select an options!",use_aliases=True), reply_markup=self.keyboardHome)
        elif query_data=='website':
            for child in self.childrenList:
                if child['chatID']==chatID:
                    response = self.bot.sendMessage(chat_id=chatID, text=f"<a href='http://0.0.0.0:5000/index?chatID={chatID}'> Link </a>", parse_mode='HTML')
        elif query_data=='settings':
            self.chatIDs, self.childrenList , self.usernameList = self.updateLists()
            for child in self.childrenList:
                if child['chatID']==chatID:
                    username = child['username']
                    childName = child['childName']
                    childSurname = child['childSurname']
            self.bot.sendMessage(chatID, f"Username: {username}\nChild Name: {childName}\nChild Surname: {childSurname}", reply_markup=self.keyboardSettings)
        elif query_data=='status_services':
            flag_apnea='offline'
            flag_seizure='offline'
            flag_monitoring='offline'
            self.servicesList=self.updateServicesStatus()
            for service in self.servicesList:
                if 'Apnea' == service['id']:
                    flag_apnea='online'
                elif 'Seizure' == service['id']:
                    flag_seizure='online'
                elif 'Monitoring' == service['id']:
                    flag_monitoring='online'
            self.bot.sendMessage(chatID, f"Apnea: {flag_apnea}\nSeizure: {flag_seizure}\nMonitoring: {flag_monitoring}")

        elif query_data=='modify_info':
            self.bot.sendMessage(chatID, "Choose an option: ", reply_markup=self.keyboardModify)
        ## Non consideriamo che si possa modificare contemporaneamente per errore più di un campo ##
        elif query_data=='modify_name':
            self.bot.sendMessage(chatID, "Choose the new Name: ", reply_markup=None)
            user={"flagName":True,"flagSurname":False,"flagUsername":False,"flagPassword":False,"chatID": chatID}
            self.modifyList.append(user)

        elif query_data=='modify_surname':
            self.bot.sendMessage(chatID, "Choose the new surname: ", reply_markup=None)
            user={"flagName":False,"flagSurname":True,"flagUsername":False,"flagPassword":False,"chatID": chatID}
            self.modifyList.append(user)
            
        elif query_data=='modify_username':
            self.bot.sendMessage(chatID, "Choose the new username: ", reply_markup=None)
            user={"flagName":False,"flagSurname":False,"flagUsername":True,"flagPassword":False,"chatID": chatID}
            self.modifyList.append(user)
            
        elif query_data=='modify_password':
            self.bot.sendMessage(chatID, "Choose the new password: ", reply_markup=None)
            user={"flagName":False,"flagSurname":False,"flagUsername":False,"flagPassword":True,"chatID": chatID}
            self.modifyList.append(user)
            
        elif query_data=='delete_account':
            if (requests.delete(self.urlcatalog+"deleteAccount"+'/'+str(chatID)).status_code == 200):
                self.bot.sendMessage(chatID,text="Account correctly removed.")
                self.bot.sendMessage(chatID,text="Welcome to MyBabyMonitorBot")
                self.bot.sendMessage(chatID, 'Choose an option:', reply_markup=self.keyboardStart)

             

if __name__ == "__main__":
    ## read configuration data ##
    conf = json.load(open("conf_bot.json"))
    urlCatalog= conf["urlCatalog"]
    token = conf["token"]

    ## retrieve mosquitto configuration data from the main catalog ##
    mosquitto = requests.get(conf['urlCatalog']+ 'getMosquittoConf')
    mosquitto=mosquitto.json()
    mosquitto=json.loads(mosquitto)
    broker=mosquitto['broker']
    port=mosquitto["port"]
    topic=mosquitto['topicAlarm']+"#"
  
    bot=MyBabyMonitorBot(token,urlCatalog,broker, port,topic)
    bot.start()
    while(1):
        pass
    