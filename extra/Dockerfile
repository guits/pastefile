FROM debian
MAINTAINER Guillaume Abrioux <guillaume@abrioux.info>

RUN apt-get update && apt-get install -y nginx-full python-setuptools && easy_install pip && pip install uwsgi python-magic flask
