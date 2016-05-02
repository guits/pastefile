FROM debian
MAINTAINER Guillaume Abrioux <guillaume@abrioux.info>

RUN apt-get update && apt-get install -y -q git python-dev python-pip && apt-get clean
RUN pip install -r https://raw.githubusercontent.com/guits/pastefile/master/requirements.txt
RUN git clone https://github.com/guits/pastefile.git /var/www/pastefile && mkdir /opt/pastefile
RUN mkdir -p /opt/pastefile/files/ /opt/pastefile/tmp && chmod -R 777 /opt/pastefile
#RUN chown -R www-data:www-data /opt/pastefile

COPY ./configs/pastefile.cfg.template /etc/pastefile.cfg
COPY ./scripts/entrypoint /entrypoint

ENTRYPOINT ["/entrypoint"]
