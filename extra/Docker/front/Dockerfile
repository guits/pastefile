FROM nginx:alpine
MAINTAINER Guillaume Abrioux <guillaume@abrioux.info>

COPY ./configs/nginx.conf.template /etc/nginx/nginx.conf.template
COPY ./configs/vhost.conf.template /etc/nginx/vhost.conf.template
COPY ./scripts/entrypoint /entrypoint

ENTRYPOINT ["/entrypoint"]
