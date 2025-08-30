FROM python:3.13

WORKDIR /app

ADD . /app

RUN apt-get update && apt-get install -y gcc

RUN pip install -r requirements.txt

CMD ["uwsgi", "app.ini"]