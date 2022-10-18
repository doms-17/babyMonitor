from flask import Blueprint, render_template, request
import requests
import json

views = Blueprint("views", __name__)

@views.route('/index',methods=['GET','POST'])
def index():
    conf = json.load(open("MonitoringDB.json"))
    urlCatalog = conf["urlCatalog"]
    urlMonitoring = conf["urlMonitoring"]
    chatID = request.args.get('chatID',type=str)
    
    childData = requests.get(urlCatalog+"getChildData"+f"/{chatID}")
    childData = childData.json()
    childData = json.loads(childData)
    
    username = childData["username"]
    childName = childData["childName"]
    childSurname = childData["childSurname"]
    idTs = childData["tsChannel"]['id']
    deviceID = childData["deviceID"]
    apneaList=[]
    seizureList=[]
    idFound = False
    devices = conf["devices"]
    for device in devices:
        if device["deviceID"] == deviceID:
            idFound = True
            apneaList = device["events"]["apnea"]
            seizureList = device["events"]["seizure"]
    
    return render_template("index.html",username=username, childName=childName, childSurname=childSurname, idTs=idTs,
                                        apneaList=apneaList, seizureList=seizureList, idFound=idFound)