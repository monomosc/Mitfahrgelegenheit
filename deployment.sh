#!/bin/bash
./git pull

/bin/cp ./Interne_Server.py /var/WebSrv/Interne_Server.py
/bin/cp ./Mitfahrgelegenheit_nginx.conf /var/WebSrv/Mitfahrgelegenheit_nginx.conf
/bin/cp ./uwsgi.ini /var/WebSrv/uwsgi.ini
/bin/cp ./wsgi.py /var/WebSrv/wsgi.py

sudo systemctl restart uwsgi_Mitfahrgelegenheit
sudo systemctl restart nginx