#!/bin/bash

if [ "$(id -u)" != "0" ]; then
  exec sudo "$0" "$@" 
fi

cd /var/git/Mitfahrgelegenheit
git pull
/bin/cp /var/git/Mitfahrgelegenheit/Interne_server.py /var/WebSrv/Interne_server.py
/bin/cp /var/git/Mitfahrgelegenheit/Mitfahrgelegenheit_nginx.conf /var/WebSrv/Mitfahrgelegenheit_nginx.conf
/bin/cp /var/git/Mitfahrgelegenheit/uwsgi.ini /var/WebSrv/uwsgi.ini
/bin/cp /var/git/Mitfahrgelegenheit/wsgi.py /var/WebSrv/wsgi.py
/bin/cp /var/git/Mitfahrgelegenheit/Interne_Entities.py /var/WebSrv/Interne_Entities.py
/bin/cp /var/git/Mitfahrgelegenheit/Version.conf /var/WebSrv/Version.conf
/bin/cp /var/git/Mitfahrgelegenheit/Interne_helpers.py /var/WebSrv/Interne_helpers.py

sudo systemctl daemon-reload
touch /tmp/uwsgi_reload
sudo systemctl restart nginx