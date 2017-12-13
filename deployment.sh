#!/bin/bash


/bin/cp /var/git/Mitfahrgelegenheit/Interne_Server.py /var/WebSrv/Interne_Server.py
/bin/cp /var/git/Mitfahrgelegenheit/Mitfahrgelegenheit_nginx.conf /var/WebSrv/Mitfahrgelegenheit_nginx.conf
/bin/cp /var/git/Mitfahrgelegenheit/uwsgi.ini /var/WebSrv/uwsgi.ini
/bin/cp /var/git/Mitfahrgelegenheit/wsgi.py /var/WebSrv/wsgi.py



systemctl daemon-reload
systemctl restart uwsgi_Mitfahrgelegenheit
systemctl restart nginx