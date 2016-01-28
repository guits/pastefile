Pastefile           [![Build Status](https://travis-ci.org/guits/pastefile.svg?branch=master)](https://travis-ci.org/guits/pastefile)
=========

Little daemon written with python flask for sharing any files quickly via http
------------------------------------------------------------------------------

- [Installation](#Installation)
  - [Quick run for test purpose](#Quick-run-for-test-purpose)
  - [Standard](#Standard)
  - [Docker](#Docker)
- [Options](#Options)
- [Usage](#Usage)


# Installation
You can either install by yourself with nginx or apache and use a custom configuration for uwsgi or build a docker image with the Dockerfile provided.


## Quick run for test purpose

If you just want to test pastefile quickly, we provide `pastefile-run.py` script only for test purpose.

```bash
apt-get install git python-dev python-pip
pip install -r https://raw.githubusercontent.com/guits/pastefile/master/requirements.txt
git clone https://github.com/guits/pastefile.git
cd pastefile && cp pastefile.cfg.sample pastefile.cfg
# Modify pastefile.cfg config to adapt pastefile directories
./pastefile-run.py -c $PWD/pastefile.cfg
```

## Standard
```bash
apt-get install git nginx-full python-pip python-dev
pip install -r https://raw.githubusercontent.com/guits/pastefile/master/requirements.txt
```

```bash
git clone https://github.com/guits/pastefile.git /var/www/pastefile
```

> **note** that ```/var/www/pastefile``` must be writable by the uwsgi process that will be launched later. You may have to ```chown <uid>:<gid>``` it with right user/group.

Write the configuration file:

```bash
curl -s -o/etc/pastefile.cfg  https://raw.githubusercontent.com/guits/pastefile/doc/pastefile.cfg.sample
```

Change parameters as you need:

```bash
vim /etc/pastefile.cfg
```
**Nginx configuration:**

> /etc/nginx/nginx.conf :

```
user www-data;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;
  
events {
    worker_connections 1024;
}
  
http {
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';
  
    access_log  /var/log/nginx/access.log  main;
  
    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   1;
    types_hash_max_size 2048;
  
    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;
  
    include /etc/nginx/conf.d/*.conf;
}
```


> /etc/nginx/conf.d/pastefile.conf :
  
```
server {
    listen 80 default_server;


        location / { try_files $uri @pastefile; }

        location @pastefile {
            include uwsgi_params;
            uwsgi_pass unix:///tmp/pastefile.sock;
        }
}
```

**uwsgi configuration:**

> /etc/uwsgi/apps-available/pastefile.ini :

```
[uwsgi]
socket = /tmp/uwsgi.sock
module = app:app
chdir  = /var/www/pastefile/pastefile
uid = 33
gid = 33
env = PASTEFILE_SETTINGS=/etc/pastefile.cfg
processes = 1
threads = 1
```

You now just have to launch nginx and uwsgi via systemd:

```bash
systemctl start nginx.service uwsgi.service
```


## Docker

First, clone the repo where you want:
```bash
git clone https://github.com/guits/pastefile.git
```
Go to the `extra/Docker` directory :
```bash
cd pastefile/extra/Docker
```
Build the image:
```bash
docker build --rm -t pastefile ./
```
You can then run a container:
```bash
docker run -t -d -i --name=pastefile pastefile
```
this is the easiest way to get a pastefile application running quickly.


# Options

|Parameters       | Usage                                                                                                                                      |
|-----------------|--------------------------------------------------------------------------------------------------------------------------------------------|
|UPLOAD_FOLDER    | Where the files are stored.                                                                                                                |
|FILE_LIST        | The file that act as the db (jsondb)                                                                                                       |
|TMP_FOLDER       | The folder where the files are stored during the transfer                                                                                  |
|EXPIRE           | How many long the files are stored (in seconds)                                                                                            |
|DEBUG_PORT       | The port used for debugging mode                                                                                                           |
|LOG              | The path to the log file                                                                                                                   |
|DISABLED_FEATURE | List of features you want to disable. Allowed value : `delete`, `ls`                                                                       |

> **Note**:

> **The directory and the db file must be writable by uwsgi.**

> the format must be KEY = VALUE.

> the KEY must be in uppercase

> if the parameter is a string, you must quote it with **""**


# Usage
Upload a file:
```bash
curl -F file=@</path/to/the/file> http://pastefile.fr
```

View all uploaded files:
```bash
curl http://pastefile.fr/ls
```

Get infos about one file:
```bash
curl http://pastefile.fr/<id>/infos
```

Get a file:
```bash
curl -JO http://pastefile.fr/<id>
```

Delete a file:
```bash
curl -XDELETE http://pastefile.fr/<id>
```

You can use this tips by adding this line in your ```.bashrc``` :
```bash
pastefile() { curl -F file=@"$1" http://pastefile.fr; }
```
so you can just type:
```bash
pastefile /my/file
```
to easily upload a file.
