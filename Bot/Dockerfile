FROM python:3-alpine

ADD MyBabyMonitorBot.py /
ADD MyMQTT.py /
ADD conf_bot.json /
ADD requirements.txt /

RUN pip3 install -r requirements.txt
CMD ["python3","./MyBabyMonitorBot.py"]

