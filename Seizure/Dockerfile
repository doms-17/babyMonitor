FROM python:3-alpine

ADD SeizureSubscriber.py /
ADD SeizurePublisher.py /
ADD MyMQTT.py /
ADD SeizureDB.json /
ADD requirements.txt /

RUN pip3 install -r requirements.txt
CMD ["python3","./SeizureSubscriber.py"]
