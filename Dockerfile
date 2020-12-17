FROM python:3.6-alpine

WORKDIR /app
COPY requirements.txt requirements.txt

RUN apk add --no-cache postgresql-libs libjpeg-turbo-dev zlib-dev && \
    apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev

RUN pip install -r requirements.txt --no-cache-dir

RUN apk --purge del .build-deps

COPY . /app

CMD ["python", "manage.py", "polling"]
