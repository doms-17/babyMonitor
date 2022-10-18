FROM python:3-alpine

ADD RaspberrySubscriber.py /
ADD RaspberryPublisher.py /
ADD MyMQTT.py /
ADD configurationDevice.json /
ADD acceleration.txt /
ADD heart_rate.txt /
ADD oxygen_level.txt /
ADD respiration.txt /
ADD requirements.txt /

RUN pip3 install -r requirements.txt
CMD ["python3","./RaspberryPublisher.py"]

