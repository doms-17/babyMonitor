FROM python:3-alpine

ADD ApneaSubscriber.py /
ADD ApneaPublisher.py /
ADD MyMQTT.py /
ADD ApneaDB.json /
ADD requirements.txt /
EXPOSE 8082
RUN pip3 install -r requirements.txt
CMD ["python3","./ApneaSubscriber.py"]

