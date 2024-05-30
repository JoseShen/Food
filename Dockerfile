FROM python:3.12.3-alpine

COPY requirements.txt requirements.txt 

RUN pip install -r requirements.txt

COPY . . 

CMD ["python", "main.py"]