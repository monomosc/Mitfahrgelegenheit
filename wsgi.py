# Moritz Basel - wsgi.py
from Interne_server import application, initialize_everything
from raven.contrib.flask import Sentry

if __name__ == "__main__":
    initialize_everything()
    sentry = Sentry(
    application, dsn='https://6ac6c6188eb6499fa2967475961a03ca:2f617eada90f478bb489cd4cf2c50663@sentry.io/232283')
    application.run()
