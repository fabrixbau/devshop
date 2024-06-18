#imagen original
FROM python:3.9.6-alpine

#set work directory
WORKDIR /usr/src/app

#configurar variables entorno
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk add --update --no-cache mariadb-connector-c-dev \
    && apk add --no-cache --virtual .build-deps \
    mariadb-dev \
    gcc \
    musl-dev \
    && pip install mysqlclient==1.4.2.post1 \
    && apk del .build-deps \
    && apk add libffi-dev openssl-dev libgcc

#instalar dependencias
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

#copiamos todo el proyecto
COPY . .

# Comando para ejecutar la aplicación
CMD ["gunicorn", "developershop.wsgi:application", "--bind", "0.0.0.0:8000"]

EXPOSE 8000