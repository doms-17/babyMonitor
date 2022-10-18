import json
from MyMQTT import* 
from RaspberryPublisher import *

class Event:
	def __init__(self, clientID, topic,broker,port,deviceID,topicAlarm):
		self.client=MyMQTT(clientID,broker,port,self)
		self.topic=topic
		self.port=port
		self.broker=broker
		self.topicAlarm = topicAlarm
		self.alarm=Publisher("AlarmPublisher_tobot",deviceID,self.broker,self.port)
		self.alarm.client.start()

	def start (self):
		self.client.start()
		self.client.mySubscribe(self.topic)

	def stop (self):
		self.client.stop()
			
	def notify(self,topic,msg):
		d=json.loads(msg)
		eventType=d['e']['eventType']
		deviceID=d['e']['deviceID']
		timestamp=d['e']['timestamp']
		duration=d['e']['duration'] 
		if ('Duration' in topic):
			print(f"Event type: {eventType}, Time: {timestamp}, Device: {deviceID}, Duration: {duration}")
			self.alarm.topic=self.topicAlarm+str(deviceID)+"/Duration"
			self.alarm.publishAlarm(self.alarm.topic,deviceID,timestamp,duration,eventType)
		else:
			self.alarm.topic=self.topicAlarm+str(deviceID)
			self.alarm.publishAlarm(self.alarm.topic,deviceID,timestamp,duration,eventType)



