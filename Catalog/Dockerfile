FROM python:3-alpine

ADD CatalogManager.py /
ADD CatalogREST.py /
ADD MyMQTT.py /
ADD catalog.json /
ADD device_template.json /
ADD requirements.txt /
EXPOSE 8080
RUN pip3 install -r requirements.txt
CMD ["python3","./CatalogREST.py"]

