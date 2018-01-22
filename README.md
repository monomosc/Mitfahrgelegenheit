Interne Mitfahrgelegenheit Backend
==================================

Mitfahrgelegenheit contains the Backend for "Mitfahrgelegenheit", an App that
manages Appointments and distributes drivers and passengers to ensure everybody
who wants to take part, can take part at appointmens.

Written in Python using Flask as a uWsgi-Backend, which is reverse-proxied and
TLS-Terminated by Nginx. It also requires a MySQL-Database which is however
abstracted away far enough to allow a different database to work with changing
just the config files. Currently Service Management is done via a Linux Systemd
Service.

Compatible with python2 and python3.

For further Documentation, consult [Technical Reference](./docs/pflichtenheft/pflichtenheft.pdf), 
[API Specification](./docs/REST_spec.pdf), [Appointment Documentation](./docs/Appointment_Lifecycle.md)
