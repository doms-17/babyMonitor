FROM python:3-alpine

ADD main_site.py /
ADD Monitoring.py /
ADD MyMQTT.py /
ADD MonitoringDB.json /
ADD requirements.txt /
COPY /Website /Website

RUN pip3 install -r requirements.txt
CMD ["python3","./Monitoring.py"]