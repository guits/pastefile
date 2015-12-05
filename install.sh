#!/bin/bash

[ -z $NGINX_WORKER_PROCESSES ] && export NGINX_WORKER_PROCESSES=auto
[ -z $NGINX_WORKER_CONNECTIONS ] && export NGINX_WORKER_CONNECTIONS=1024
[ -z $NGINX_KEEPALIVE_TIMEOUT ] && export NGINX_KEEPALIVE_TIMEOUT=1
[ -z $NGINX_DEFAULT_PORT ] && export NGINX_DEFAULT_PORT=80
[ -z $NGINX_APP_NAME ] && export NGINX_APP_NAME=pastefile
[ -z $UWSGI_SOCK ] && export UWSGI_SOCK=/tmp/uwsgi.sock

if [[ -x $(which lsb_release 2>/dev/null) ]]; then
	os_VENDOR=$(lsb_release -i -s)
	if [[ "Debian" =~ $os_VENDOR ]]; then
	apt-get update
	apt-get install -y python-pip python-dev git gcc nginx-full gettext-base uwsgi
	git clone https://github.com/guits/pastefile /var/www/pastefile
	pip install -r requirements.txt
	envsubst '$NGINX_WORKER_PROCESSES $NGINX_WORKER_CONNECTIONS $NGINX_KEEPALIVE_TIMEOUT' < ./extra/Docker/configs/nginx.conf.template > /etc/nginx/nginx.conf
	envsubst '$NGINX_DEFAULT_PORT $NGINX_APP_NAME $UWSGI_SOCK' < ./extra/Docker/configs/vhost.conf.template > /etc/nginx/conf.d/pastefile.conf
	cp ./extra/uwsgi_pastefile.ini /etc/uwsgi/apps-available/pastefile.ini
	cp ./extra/Docker/configs/pastefile.cfg.template /etc/pastefile.cfg
	mkdir /opt/pastefile
	chown www-data:www-data /opt/pastefile
	ln -s /etc/uwsgi/apps-available/pastefile.ini /etc/uwsgi/apps-enabled/pastefile.ini
	fi
elif [[ -r /etc/redhat-release ]]; then
  echo "Not supported yet."
fi
