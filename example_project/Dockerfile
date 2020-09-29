FROM python:3.8-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update && apk add libpq && \
    apk update && apk add --virtual .build-deps gcc \
                                                libxml2-dev \
                                                libxslt-dev \
                                                python3-dev \
                                                musl-dev \
                                                postgresql-dev && \
    pip install -U setuptools psycopg2-binary && \
    pip install -U django djangorestframework && \
    apk del .build-deps

#RUN python -m pip install https://github.com/terentjew-alexey/django-bot-engine/archive/develop.zip
RUN python -m pip install PySocks requests[socks] django-sortedm2m viberbot pyTelegramBotAPI

WORKDIR /usr/src/app
COPY . .

EXPOSE 8800

CMD ["python", "manage.py", "runserver", "0.0.0.0:8800"]
