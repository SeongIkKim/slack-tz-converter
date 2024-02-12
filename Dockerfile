FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY app/ .
CMD ["python3", "-u", "main.py"]