FROM debian
MAINTAINER Guillaume Abrioux <guillaume@abrioux.info>

RUN apt-get update && apt-get install -y git nginx-full gettext-base python-setuptools python-dev gcc && easy_install pip && pip install uwsgi python-magic flask && apt-get clean
RUN git clone https://github.com/guits/pastefile.git /var/www/pastefile && mkdir /opt/pastefile && chown www-data:www-data /opt/pastefile
COPY ./configs/nginx.conf.template /opt/pastefile/nginx.conf.template
COPY ./configs/vhost.conf.template /opt/pastefile/vhost.conf.template
COPY ./configs/pastefile.cfg.template /etc/pastefile.cfg
COPY ./scripts/entrypoint /entrypoint

ENTRYPOINT ["/entrypoint"]
