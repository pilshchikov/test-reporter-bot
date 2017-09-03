FROM python:3.6.1-alpine

COPY src/ /opt/app/
COPY requirements.txt /opt/app/
RUN pip install -r /opt/app/requirements.txt

ENTRYPOINT ["python", "/opt/app/reporter.py"]
