# Moritz Basel - interne_server.py
# Version 0.1.0
import atexit
from flask import Flask, url_for, request, make_response, redirect, jsonify
from Interne_Entities import Appointment, User, User_Appointment_Rel, SQLBase
import configparser
import os

from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker

from raven.contrib.flask import Sentry
from raven.handlers.logging import SentryHandler
from raven.conf import setup_logging
from werkzeug import generate_password_hash, check_password_hash
from werkzeug.security import safe_str_cmp
from flask import json
from datetime import time, timedelta, datetime
from time import strftime
from random import randint

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers import cron
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from validate_email import validate_email

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token, get_jwt_identity, get_jwt_claims, jwt_optional)
import logging

# GLOBALS:
application = Flask(__name__)
jwt = JWTManager(application)
logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()
sentry = Sentry(
    dsn='https://3fb25fb74b6c4cf48f5c0e8ff285bc51:a36099e9044e4b0ab09224bddd652489@sentry.monomo.solutions/2')
Session = sessionmaker()
__log_handler__ = None


# LOG INITIALIZER
def initialize_log():
    global __log_handler__
    now = datetime.now()
    filename = application.config['MITFAHRGELEGENHEIT_LOG'] + 'Mitfahrgelegenheit-' + \
        now.strftime("%d-%m-%y") + ".log"
    if __log_handler__ is not None:
        logger.removeHandler(__log_handler__)
        logging.getLogger('sqlalchemy').removeHandler(__log_handler__)
        logging.getLogger('apscheduler').removeHandler(__log_handler__)

    __log_handler__ = logging.FileHandler(filename)
    __log_handler__.setLevel(logging.DEBUG)
    __log_handler__.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(__log_handler__)

    logger.setLevel(application.config['LogLevel'])
    logger.info("Initialized logging to " + filename + ".")
    logging.getLogger('apscheduler').addHandler(__log_handler__)
    logging.getLogger('apscheduler').setLevel(logging.WARN)
    logging.getLogger('sqlalchemy').addHandler(__log_handler__)
    logging.getLogger('sqlalchemy').setLevel(logging.WARN)


# init function to be called from within here (Debug client), PyTest (Test Framework) or wsgi.py (Prod)
def initialize_everything():
    "Initializes EVERYTHING"
    if __name__ == "__main__":
        application.debug = True
    application.config['LogLevel'] = logging.INFO
    prod = False
    if (not application.debug and not application.testing):
        if not 'MITFAHRGELEGENHEIT_TEST' in os.environ:
            prod = True
            application.config['LogLevel'] = logging.INFO
        else:
            application.testing = True

    # LOADING CONFIG
    # is set to /etc/Mitfahrgelegenheit.conf on productionf
    application.config.from_envvar('MITFAHRGELEGENHEIT_SETTINGS')

    initialize_log()            # Important logger initialization

    logger.info('-------- STARTING UP --------')
    logger.info('Appliction is in ' +
                ('TEST' if application.testing else 'NON-TEST') + ' mode')
    logger.info('Application is in ' +
                ('DEBUG' if application.debug else 'NON-DEBUG') + ' mode')
    logger.info('Application is in ' +
                ('Prod' if prod else 'NON-Prod') + ' mode')

    logger.debug('Config Values:')
    for key, val in application.config.items():
        logger.debug(key + '  :  ' + str(val))
    # SQLALCHEMY SETUP
    engine = create_engine(
        application.config['SQL_ALCHEMY_ENGINE'], echo=False,  pool_recycle=3200)
    logger.info('Creating SQLAlchemy Engine with engine param: ' +
                application.config['SQL_ALCHEMY_ENGINE'])
    Session.configure(bind=engine)
    SQLBase.metadata.create_all(engine)

    if prod:

        apscheduleSqliteEngine = create_engine(
            'sqlite:///APSchedule.db', echo=False)
        scheduler.configure(
            jobstores={'default': SQLAlchemyJobStore(engine=apscheduleSqliteEngine)})
        scheduler.start()
        sentryhandler = SentryHandler(
            'https://3fb25fb74b6c4cf48f5c0e8ff285bc51:a36099e9044e4b0ab09224bddd652489@sentry.monomo.solutions/2')
        sentryhandler.setLevel(logging.WARNING)
        setup_logging(sentryhandler)

        sentry.init_app(application)
        #sentry.captureMessage('Setup on Flask at ' + str(datetime.now()))


if __name__ == "__main__":
    os.environ['MITFAHRGELEGENHEIT_SETTINGS'] = './Mitfahrgelegenheit.debug.conf'

initialize_everything()
if __name__ == "__main__":
    application.run(host='127.0.0.1', debug=True)


# DYNAMIC PART - REST-API
#///////////////////////////////////////////////////////////////////////////////////////////////////
# simple API description
@application.route('/api', methods=['GET'])
def api():
    returnJSON = {}
    try:
        with open("Version.conf") as f:
            conf = configparser.RawConfigParser(allow_no_value=True)
            conf.read_file(f)
            returnJSON['version'] = conf.get('VERSION', 'VERSION')
    except:
        returnJSON['version'] = 'invalid'
        logger.error('Error reading Version Config File')
        try:
            sentry.captureException()
        except:
            pass

    returnJSON['lastknownversion'] = '0.1.1'
    objectUser = {'username: string': 'required: login name', 'id: int': 'required: internal id', 'email: string': 'required: valid email',
                  'phoneNumber: string': 'required: Phone Number the user is available on in case of conflicts',
                  'globalAdminStatus: int': 'required: higher means more rights',
                  'password: string': 'do not send this'}
    objectAppointment = {'id: int': 'required: internal ID', 'startLocation: string': 'required: Meetup Location for Starting the Appointment',
                         'startTime: int': 'required: unix timestamp for Appointment Meetup time',
                         'repeatTime: string': 'required: as of now always none',
                         'distance: int': 'required: the distance to drive',
                         'retired: bool': 'defaults to False; changes to True once when the appointment is finished'}

    returnJSON['objects'] = {'user': objectUser,
                             'appointment': objectAppointment}
    returnJSON['relationships'] = [{'parent': 'User', 'child': 'appointment', 'drivingLevel: int': 'Enum: 0 denoting the User WILL NOT drive,' +
                                    '1 denoting he WILL definitely drive, 2 he MAY drive if need exists',
                                    'maximumPassengers: int': 'optional: Denotes the maximum amount of passengers the User can transport if he were to drive'}]

    routes = []
    for rule in application.url_map.iter_rules():
        try:
            options = {}
            for arg in rule.arguments:
                options[arg] = "[{0}]".format(arg)
            httpmethods = []
            for method in rule.methods:
                httpmethods.append(method)
            route = {'function': rule.endpoint,
                     'http-methods': httpmethods,
                     'url': url_for(rule.endpoint, **options)}
            routes.append(route)
        except:
            try:
                sentry.captureException({'tags' : options})
            except:
                logger.error('Sending Sentry Event Failed')
    returnJSON['endpoints'] = routes

    return jsonify(returnJSON), 200


@application.route('/api/users', methods=['GET'])  # TODO: Write Test
@jwt_required
def users():

    returnJSON = []
    session = Session()
    for instance in session.query(User):
        returnJSON.append(instance.getAsJSON())

    session.close()
    return jsonify(returnJSON), 200


@application.route('/api/users', methods=['POST'])  # Complete, Test complete
def signup():
    "The Endpoint URI for signing up. Takes email, username and password JSON returns 201 on success"

    logger.info("User Signup on POST /api/users")

    if not request.is_json:
        return jsonify(message='Expect JSON Request'), 400
    try:
        requestJSON = json.loads(request.data)
    except json.JSONDecoder.JSONDecodeError:
        return jsonify(message="Malformed JSON"), 400

    # check for JSON keys
    if 'email' not in requestJSON or 'password' not in requestJSON:
        return make_message_response("Signup must contain (password, email) JSON keys", 400)
    if 'phoneNumber' not in requestJSON or 'username' not in requestJSON:
        return make_message_response("Signup must contain (username, phoneNumber) JSON Keys", 400)

    # hash the password
    hashed_password = generate_password_hash(requestJSON['password'])

    # CHECK for SQL Injection
    checkall = requestJSON['username'] + requestJSON['email']
    if 'DROP' in checkall or 'DELETE' in checkall or 'INSERT' in checkall or 'ALTER' in checkall or 'SELECT' in checkall:
        return jsonify(message="Bad Term in Request Body"), 404

    session = Session()
    check_for_duplicates = session.query(User).filter(
        User.username == requestJSON['username'])
    if check_for_duplicates.count() > 0:
        session.close()
        logger.warning('User ' + requestJSON['username'] + 'already exists with ID ' + str(check_for_duplicates.first().id))
        return jsonify(check_for_duplicates.first().getAsJSON()), 409
    newuser = User(username=requestJSON['username'], email=requestJSON['email'],
                   phoneNumber=requestJSON['phoneNumber'], globalAdminStatus=0,
                   password=hashed_password)
    session.add(newuser)
    session.commit()
    newuserJSON = newuser.getAsJSON()
    session.close()
    # Respond 201 CREATED
    logger.info('User ' + requestJSON['username'] + ' created')
    return jsonify(newuserJSON), 201


@application.route('/api/users/<int:u_id>', methods=['GET', 'PUT', 'DELETE', 'PATCH'])
@jwt_optional
def doSomethingWithThisUser(u_id):
    if request.method == 'PATCH':
        return patchUser(u_id)
    if request.method == 'PUT':
        return patchUser(u_id)
    if request.method == 'GET':
        return user_profileByID(u_id)
    if request.mehod == 'DELETE':
        return jsonify(message='This Method is not implemented here (yet)'), 405


@application.route('/api/users/<string:u_name>', methods=['GET', 'PUT', 'DELETE', 'PATCH'])
@jwt_optional
def redirectToIdCall(u_name):
    "User redirect Username --> UserID"
    session = Session()
    users = session.query(User).filter(User.username == u_name)
    if users.count() == 0:
        session.close()
        return jsonify(message='User ' + u_name + ' does not exist'), 404
    user = users.first()
    session.close()
    return redirect('/api/users/' + str(user.id)), 307


def user_profileByID(u_id):
    "User Profile Endpoint - ID"
    session = Session()
    users = session.query(User).filter(User.id == u_id)
    if users.count() == 0:
        session.close()
        return jsonify(message='User does not exist'), 404
    user = users.first()
    session.close()
    return jsonify(user.getAsJSON()), 200


def patchUser(user_id):
    "Update an existing user, similar but not completely compliant to RFC7396"
    uclaims = get_jwt_claims()
    logger.info('User Patch Request by ' +
                uclaims['username'] + ' on UserID ' + str(user_id))
    if not request.is_json:
        return jsonify(message='Malformed JSON or Wrong headers (expect applcation/json)'), 400
    requestJSON = json.loads(request.data)

    # check if user is allowed to change requested user profile
    try:
        if int(uclaims['globalAdminStatus'] < 1):
            if get_jwt_identity() != user_id:
                logger.warn(
                    'User ' + uclaims['username'] + '(Non-Admin) tried to patch user other than himself')
                return jsonify(message='Not allowed'), 401
    except ValueError:
        logger.error('User ' + uclaims['username'] +
                     '  has an illegal globalAdminStatus: ' + str(uclaims['globalAdminStatus']))
        return jsonify(message='ye weird'), 500
    if 'globalAdminStatus' in requestJSON:
        try:
            if int(requestJSON['globalAdminStatus']) > uclaims['globalAdminStatus']:
                logger.warn(
                    'User ' + uclaims['username'] + 'illegaly attempts to elevate Admin Privileges to ' + requestJSON['globalAdminStatus'])
                return jsonify(message='Not allowed'), 404
        except ValueError:
            return jsonify(message='Illegal Type in field "globalAdminStatus"'), 422
    if 'username' in requestJSON:
        logger.info('Username change is not allowed')
        return jsonify(message='Username change is not allowed'), 403
    # end permission checks

    session = Session()
    users = session.query(User).filter(User.id == user_id)
    if users.count() == 0:
        session.close()
        logger.info('User ' + user_id + ' does not exist. No Change executed')
        return jsonify('User ' + user_id + ' does not exist'), 404
    thisuser = users.first()
    logstring = ''
    if 'globalAdminStatus' in requestJSON:
        logstring = logstring + 'globalAdminStatus: ' + \
            str(requestJSON['globalAdminStatus']) + ', '
        thisuser.globalAdminStatus = requestJSON['globalAdminStatus']
    if 'email' in requestJSON:
        logstring = logstring + 'email: ' + str(requestJSON['email']) + ', '
        thisuser.email = requestJSON['email']
    if 'phoneNumber' in requestJSON:
        logstring = logstring + 'phoneNumber: ' + \
            str(requestJSON['phoneNumber']) + ', '
        thisuser.phoneNumber = requestJSON['phoneNumber']
    if 'password' in requestJSON:
        hashed_password = generate_password_hash(requestJSON['password'])
        logger.info('Set new Password on User ' + thisuser.username)
        thisuser.password = hashed_password

    session.commit()
    logger.info('Changed User ' + thisuser.username +
                '. Changed Keys: ' + logstring)
    session.close()
    return json.dumps(thisuser.getAsJSON()), 200


@application.route('/api/users/<int:u_id>/appointments', methods=['GET'])
@jwt_required
def userAppointments(u_id):
    # check privileges
    uclaims = get_jwt_claims()
    if int(uclaims['globalAdminStatus']) < 1:
        caller_id = get_jwt_identity()
        if caller_id != u_id:
            return jsonify(message='Not allowed'), 401

    return getAppointments(u_id)


def getAppointments(u_id):
    # TODO: Implement and write test
    return jsonify(message='Not yet implemented'), 404


@application.route('/api/users/<int:u_ID>/appointments/<int:a_ID>', methods=['PUT'])
def putAppointment(u_id):
    "Add an existing appointment to a User (in the sense that he will be taking part)"
    logger.info(
        'Call to /api/users/uid/appointments/aid redirecting to /api/appointments/aid/users/uid 307', code=307)
    return redirect('/api/appointments/' + str(a_ID) + '/users/' + str(u_ID), code=307)


@application.route('/api/appointments/<appointmentID>', methods=['GET', 'DELETE'])
@jwt_required
def appointment(appointmentID):
    if request.method == 'GET':
        return appointment_data(appointmentID)
    if request.method == 'DELETE':
        return deleteAppointment(appointmentID)


def appointment_data(appointmentID):
    "Appointment functionailty"
    uclaims = get_jwt_claims()
    logger.info("User: " + uclaims['username'] +
                " accessing appointment: " + str(appointmentID))
    session = Session()
    appointments = session.query(Appointment).filter(
        Appointment.id == appointmentID)
    if appointments.count() == 0:
        session.close()
        return jsonify(message="Appointment does not exist"), 404
    appointment = appointments.first()
    appointmentJSON = appointment.getAsJSON()
    session.close()
    return jsonify(appointmentJSON), 200


def deleteAppointment(appointmentID):
    logger.info('Trying to delete Appointment ' + str(appointmentID) +
                ' from User ' + get_jwt_claims()['username'])

    session = Session()
    appointments = session.query(Appointment).filter(
        Appointment.id == appointmentID)
    if appointments.count() == 0:
        session.close()
        return jsonify(message="Appointment does not exist"), 404
    try:
        appointment = appointments.first()
        session.delete(appointment)
        session.commit()
        logger.info('Appointment ' + appointmentID + ' deleted')
    except:
        logger.error('Deletion of Appointment ID' +
                     str(appointmentID) + ' unsuccessful')
    finally:
        session.close()

    try:
        scheduler.remove_job('Appointment Notify Job ' + str(appointmentID))
    except:
        logger.error(
            'Could not remove Appointment Notify Job to Appointment #' + str(appointmentID))

    return '', 204


@application.route('/api/appointments/<int:a_ID>/users', methods=['GET'])
@jwt_required
def getAppUsers(a_ID):
    logger.info('User ' + get_jwt_claims()
                ['username'] + ' requesting User List to Appointment ' + str(a_ID))
    session = Session()

    appointments = session.query(Appointment).filter(Appointment.id == a_ID)
    if appointments.count() == 0:
        return jsonify(message="No Such Appointment"), 404

    returnJSON = []
    thisappointment = appointments.first()
    for user_app_rel in thisappointment.users:
        appendJSON = user_app_rel.user.getAsJSON()
        appendJSON['drivingLevel'] = user_app_rel.drivingLevel
        returnJSON.append(appendJSON)

    logger.info('Returning Appointment ' + str(a_ID) +
                ' User List, containing ' + str(len(thisappointment.users)) + ' entities')
    session.close()
    return jsonify(returnJSON), 200


@application.route('/api/appointments/<int:a_ID>/users/<int:u_ID>', methods=['PUT', 'GET'])
@jwt_required
def putAppUser(a_ID, u_ID):
    "Add an existing appointment to a User (in the sense that he will be taking part)"
    if request.method == 'GET':
        logger.info(
            'GET on /api/appointments/a_ID/users/u_ID redirecting to user profile')
        return redirect('/api/users/' + str(u_ID))

    session = Session()

    # check if Appointment exists:
    appointments = session.query(Appointment).filter(Appointment.id == a_ID)
    if appointments.count() == 0:
        return jsonify(message='No such Appointment exists'), 404
    thisappointment = appointments.first()

    # check if user exists:
    users = session.query(User).filter(User.id == u_ID)
    if users.count() == 0:
        return jsonify(message='No such User exists'), 404
    thisuser = users.first()

    logger.info('User ' + get_jwt_claims()
                ['username'] + ' attempts to add ' + thisuser.username + ' to Appointment ' + str(a_ID))

    # Some basic checks for request syntax and semantics
    if not request.is_json:
        return jsonify(message='Expect JSON Body'), 400
    try:
        requestJSON = json.loads(request.data)
    except:
        logger.warn('Illegal Request Syntax')
        return jsoinfy('Expect JSON Body'), 400

    if 'drivingLevel' not in requestJSON:
        return jsonify('Expect drivingLevel Integer JSON key'), 409

    if requestJSON['drivingLevel'] != 0:
        if 'maximumPassengers' not in requestJSON:
            logger.warning(
                'maximumPassengers not in Request for adding User to Appointment')
            return jsonify(message='If drivingLevel is not 0, supply maximumPassengers key'), 422

    # check priviliges:
    if get_jwt_claims()['globalAdminStatus'] < 1:
        if get_jwt_identity() != u_ID:
            logger.warn('User ' + get_jwt_claims()['username'] + ' tried to add ' +
                        thisuser.username + ' to an Appointment as Non-Admin')
            return jsonify('Non-Admin can only add him/herself to Appointments'), 403

    # build the relationshio column
    try:
        rel = User_Appointment_Rel(drivingLevel=(
            int(requestJSON['drivingLevel'])))
    except ValueError:
        logger.warn('drivingLevel was not an Integer: drivingLevel : ' +
                    requestJSON['drivingLevel'])
        return jsonify('Expect integer drivingLevel'), 409
    try:

        rel.appointment = thisappointment
        thisuser.appointments.append(rel)
        session.add(rel)
        session.commit()
    except exc.SQLAlchemyError:
        logger.error(
            'SQLAlchemy Error on building User_Takes_Part Row: %s', exc_info=True)
        session.close()
        return jsonify(message='Unfortunately, an error occured'), 500

    logger.info('Added User ' + thisuser.username +
                ' to Appointment ' + str(a_ID))

    session.close()
    return jsonify(message='Success'), 200  # TODO: Add test


@application.route('/api/appointments', methods=['GET', 'POST'])
@jwt_required
def appointments():
    if request.method == 'GET':
        return getAppointments
    if request.method == 'POST':
        return makeAppointment()
    return jsonify(message='Method not allowed'), 405


def getAppointments():
    "Get a list of appointments"
    # request argument parsing
    log.info('User ' + get_jwt_claims()
             ['username'] + 'requesting appointment List')
    showFinished = False
    if 'showFinished' in request.args:
        showFinished = True if request.args['showFinished'] == 'true' else False
    appointments = session.query(
        Appointment).all().order_by(Appointment.startTime)
    retListJSON = []

    for app in appointments:
        retListJSON.append(app.getAsJSON())

    return jsonify(retListJSON), 200


def makeAppointment():
    "Creates a new Appointment"
    logger.info('Access to "Make new Appointment" by user ' +
                get_jwt_claims()['username'])
    uclaims = get_jwt_claims()
    if not request.is_json:
        return jsonify(message='Illegal Format'), 400
    try:
        requestJSON = json.loads(request.data)
    except json.JSONDecodeError:
        return jsonify(message='Illegal JSON'), 400

    requiredKeys = ['startLocation', 'startTime', 'distance']
    for key in requiredKeys:
        if key not in requestJSON:
            return jsonify(message='Missing JSON key: ' + key), 422

    if 'repeatTime' in requestJSON:
        rTime = requestJSON['repeatTime']
    else:
        rTime = 'None'

    newappointment = Appointment(startLocation=requestJSON['startLocation'],
                                 startTime=datetime.fromtimestamp(
                                     requestJSON['startTime']),
                                 repeatTime=rTime,
                                 retired=False,
                                 distance=requestJSON['distance'],
                                 everyoneFits=0)
    session = Session()
    session.add(newappointment)
    session.commit()

    try:
        logger.info('Added new Appointment on ' +
                    str(newappointment.startTime))
    except ValueError:
        logger.error(
            'Could not print Date of newly created Appointment! ID: ' + str(newappointment.id))

    startAppointmentScheduledEvent(newappointment.id, timedelta(hours=1))
    returnJSON = newappointment.getAsJSON()
    session.close()

    return jsonify(returnJSON), 201


@application.route('/api/auth', methods=['POST'])  # complete, Test Complete
def authenticate_and_return_accessToken():
    "Authentication endpoint, returns 200 {access_token : xyz} on success"
    logger.info('User Access Token Request')
    if not request.is_json:
        logger.info("Invalid Request in /api/auth. header content-type is: " +
                    request.headers['content-type'])
        return jsonify('No JSON'), 400
    requestJSON = json.loads(request.data)
    if ('username' not in requestJSON and 'email' not in requestJSON) or 'password' not in requestJSON:
        logger.info('Malformed JSON in User Access Token Request')
        return jsonify(message='Missing JSON Keys'), 422

    session = Session()

    users = session.query(User).filter((
        User.username == requestJSON['username'])
        if ('username' in requestJSON)
        else (User.email == requestJSON['email']))
    if users.count() == 0:
        logger.info('Invalid Access Token Request (Username ' +
                    (requestJSON['username'] if 'username' in requestJSON else requestJSON['email']) + ' does not exist)')
        session.close()
        return jsonify(message='Invalid Username or Password'), 404
    thisuser = users.first()
    if check_password_hash(thisuser.password, requestJSON['password']):
        logger.info('Creating Access Token for ' + requestJSON['username'])
        token = create_access_token(identity=thisuser)
        logger.debug('Access Token: Bearer ' + token)
        session.close()
        return jsonify(access_token=token, username=thisuser.username, email=thisuser.email, globalAdminStatus=thisuser.globalAdminStatus, phoneNumber=thisuser.phoneNumber), 200
    else:
        session.close()
        logger.info(
            'Invalid Password in Access Token Request for user: ' + requestJSON['username'])
        return jsonify(message='Invalid Username or Password')


# DYNAMIC PART - REST-DEV-API
#///////////////////////////////////////////////////////////////////////////////////////////////////

@application.route('/api/dev/check_token', methods=['GET'])
@jwt_required
def check_token():

    retObj = {}
    retObj = get_jwt_claims().copy()
    retObj['id'] = get_jwt_identity()
    return make_json_response(retObj, 200)


@application.route('/api/dev/removeUser/<uname>', methods=['DELETE'])
@jwt_required
def removeUser(uname):
    # check if you are the user in question or have Administrative Privileges
    try:
        uclaims = get_jwt_claims()
        if uname != uclaims['username'] and uclaims['globalAdminStatus'] < 1:
            logger.warning('User : ' + uclaims['username'] + ' tried to remove ' +
                           uname + '. This Endpoint should not be generally known')
            return make_message_response("Can only remove self; or requires administrative priviliges. User " + str(uclaims['username']) + " trying to remove " + uname, 401)
    except KeyError as e:
        logger.error(
            'An invalid Key got into RemoveUser!: KeyError on JWTClaims: ' + str(e))
        return jsonify(message='An Error has occured. This is the programmers fault'), 500

    session = Session()
    users = session.query(User).filter(User.username == uname)
    if users.count() == 0:
        logger.info('Invalid User Removal Request: (Username ' +
                    uname + ' does not exist')
        return jsonify(message='Invalid Username or Password'), 404
    thisuser = users.first()
    session.delete(thisuser)
    session.commit()
    session.close()
    logger.warning('Removed User : ' +
                   uclaims['username'] + ' - Was this intended?')
    return ('', 204)


@application.route('/api/dev/check_api')
def checkApi():
    logger.info('/api/dev/check_api test run')
    return make_response("REST-API seems to work")


@application.route('/api/dev/check-api')
def chc():
    return checkApi()


@application.route('/api/dev/protected')
@jwt_required
def protected():
    logger.info('/api/dev/protected Test Run')
    return make_message_response('This is protected', 200)


@application.route('/api/dev/optional')
@jwt_optional
def optional():
    logger.info('/api/dev/optional Test Run')
    if get_jwt_identity() == None:
        return make_message_response('Optional Protection, you had no Token', 200)
    else:
        return make_message_response('Optional Protection, you had a token', 200)


@application.route('/api/dev/log', methods=['GET'])
@jwt_required
def logfile():
    logger.info('Logfile Request from User: ' + get_jwt_claims()['username'])
    if get_jwt_claims()['globalAdminStatus'] < 1:
        return jsonify(message="Illegal Non-Admin Operation"), 401

    now = datetime.now()
    filename = application.config['MITFAHRGELEGENHEIT_LOG'] + 'Mitfahrgelegenheit-' + \
        now.strftime("%d-%m-%y") + ".log"
    logger.info('Sending Logfile: ' + filename)
    latest = request.args.get('latest')
    if latest == 'true':
        try:
            logstr = open(filename, 'r').read()
            return jsonify(log=logstr, time=now.strftime("%d-%m-%y"))
        except Exception as ex:
            return jsonify(exception=str(ex)), 500
    return jsonify(message="Only ?latest=true allowed"), 422


@application.route('/api/dev/jobs', methods=['GET'])
@jwt_required
def jobs():
    logger.info('Jobs Request from User: ' + get_jwt_claims()['username'])
    if get_jwt_claims()['globalAdminStatus'] < 1:
        logger.warning(
            'Illegal Operation: Jobs Request from User: ' + get_jwt_claims()['username'])
        return jsonify(message="Illegal Non-Admin Operation"), 401

    returnJSON = []
    jobs = scheduler.get_jobs()
    for job in jobs:
        returnJSON.append(job.id)

    logger.info('Sending Joblist containing ' +
                str(len(returnJSON)) + ' entities')
    return jsonify(returnJSON)

#//////////////////////////////////////////////////////////////////////////////////////////////////


def make_message_response(string, status):
    return make_json_response('{"message" : "' + string + '"}', status)


def make_json_response(jsonDictionary, status):
    try:
        return make_response(json.dumps(jsonDictionary), status, {'content-type': 'application/json'})
    except json.JSONDecodeError:
        return make_response('{"message" : "Internal Server Error: Some Method created invalid JSON Data"}', 500, {'content_type': 'application/json'})


#/////////////////////////////////////////////////////////////////////////////////////////////////
# Error 500 general handler

@application.errorhandler(500)
def internal_server_error(error):
    logger.error("Internal Server Error: " + error)
    return jsonify(message="Internal Server Error"), 500
#/////////////////////////////////////////////////////////////////////////////////////////////////
# Error 404 general handler


@application.errorhandler(404)
def resource_not_found_error(error):
    logger.warning("404: error")
    return jsonify(message='Resource does not exist'), 404


#//////////////////////////////////////////////////////////////////////////////////////////////////
# JWT CALLBACK FUNCTIONS:

@jwt.user_claims_loader
def add_claims_to_access_token(user):
    "Defines all fields to be remembered and recovered in the JSON Token"
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'phoneNumber': user.phoneNumber,
        'globalAdminStatus': user.globalAdminStatus}


@jwt.user_identity_loader
def user_identity_lookup(user):
    "UID for a Token Identity"
    return user.id


@jwt.claims_verification_failed_loader
def claims_verification_failed_loader():
    logger.warning("User Claims Verification Failed")
    return make_message_response("User Claims Verification Failed - Probably an Illegal Token", 400)


@jwt.expired_token_loader
def expired_token_loader():
    logger.info("Someone used an expired Token")
    return jsonify(message="Token Expired"), 401


@jwt.needs_fresh_token_loader
def needs_fresh_token_loader():
    return make_message_response("Fresh Token required", 401)


@jwt.invalid_token_loader
def invalid_token_loader(msgstring):
    logger.warning("Invalid Token: " + msgstring)
    return make_message_response(msgstring, 401)


@jwt.revoked_token_loader
def revoked_token_loader():
    logger.warning("Someone used a revoked Token")
    return make_message_response("Token has been revoked", 401)


@jwt.unauthorized_loader
def unauthorized_loader(msg):
    logger.info("Unauthorized Request: " + msg)
    return jsonify(message=msg), 401


def terminateAppointment(appointmentID):
    "terminateAppointment is called by the scheduler 1 hour before the appointment takes place"
    #get Number of total possible Passengers including only 
    #Definite Drivers - drivingLevel #1
    definiteDriversPassengerAmount = 0
    #Possible Drivers - drivingLevel #2
    possibleDriversPassengerAmount = 0

    #totalParticipants holds the total number of Users that want to take part in this appointment
    totalParticipants = 0

    session = Session()
    try:
        appointments = session.query(Appointment).filter(Appointment.id == appointmentID)
        if appointments.count() == 0:
            raise Exception('terminateAppointment called on a nonexisting Appointment!!(#'+str(appointmentID)+') This is bad news!')
        thisappointment = appointments.first()
        for user_app_rel in thisappointment.users:
            if user_app_rel.drivingLevel == 1:
                definiteDriversPassengerAmount = definiteDriversPassengerAmount + user_app_rel.maximumPassengers
                possibleDriversPassengerAmount = possibleDriversPassengerAmount + user_app_rel.maximumPassengers
            if user_app_rel.drivingLevel == 2:
                possibleDriversPassengerAmount = possibleDriversPassengerAmount + user_app_rel.maximumPassengers
            totalParticipants = totalParticipants + 1
        
        #good News !! Everyone fits!
        if totalParticipants <= definiteDriversPassengerAmount:
            logger.info('Everyone fits into Definite Driver Seats on Appointment #' + str(thisappointment.id))
        
            thisappointment.everyoneFits = 1

            listOfAllDrivers = []
            listOfAllPassengers = []
            for user_app_rel in thisappointment.users:
                listOfAllPassengers.append(user_app_rel)
                if user_app_rel.drivinLevel == 1:
                    listOfAllDrivers.append(user_app_rel)
            
            totalNumberOfDrivers = len(listOfAllDrivers)

            #alright, so now an algorithmic challenge...
            #distribute all passengers onto their drivers!

                    #list.sort(listOfAllDrivers, key = lambda user_app_rel: user_app_rel.maximumPassengers, reverse = True)
            
            drivingDict = {}
            for user_app_rel in listOfAllDrivers:
                drivingDict[user_app_rel] = []
            
            finishedPassengers = []
            for user_app_rel in listOfAllPassengers:
                if user_app_rel in listOfAllDrivers:
                    drvingDict[user_app_rel].append(user_app_rel)
                    finishedPassengers.append(user_app_rel)
            
            for user_app_rel in finishedPassengers:
                listOfAllPassengers.remove(user_app_rel)
            finishedPassengers.clear()
            
            #we now have handled all drivers (who will of course have themselves as passenger)
            
            #randomly distribute passengers on cars
            for user_app_rel in listOfAllPassengers:
                k = randint(0, len(listOfAllDrivers))
                drivingDict[listOfAllDrivers[k]].append(user_app_rel)
                if len(drivingDict[listOfAllDrivers[k]])> listOfAllDrivers[k].maximumPassengers:
                    del listOfAllDrivers[k]
            #drivingDict now holds a dictionary containing a valid configuration of drivers to cars

            #write to DB
            for driver, passenger in drivingDict:
                passenger.designatedDriverUser = driver.user
            
            logger.info('Distributed ' + str(totalParticipants) + ' Participants onto ' + str(totalNumberOfDrivers) + ' on Appointment # ' + str(thisappointment.id))
            logger.info('Writing Driver Distribution Information for Appointment #' + str(thisappointment.id) + ' to DB.')
            session.commit()
        
        #sortof good News !! everyone fits..at least including the may-drivers
        if totalParticipants > definiteDriversPassengerAmount and totalParticipants <= possibleDriversPassengerAmount:
            logger.info('Not everyone fits into Definite Driver Seats. Taking Possible Drivers into Account on Appointment #' + str(thisappointment.id))
            logger.fatal('Not yet Implemented! Distribution onto possible drivers!')

        if totalParticipants > possibleDriversPassengerAmount:
            logger.warning('Not everyone even fits onto Possible Driver Seats on Appointment #' + str(thisappointment.id) +'!')
            logger.fatal('Not yet Implemented! Failed Distribution !!')

    except:
        try:
            sentry.captureException()
        except:
            pass
        logger.fatal('Something went wrong in terminateAppointment!!!')
    finally:
        session.close()

    logger.info('Exiting terminateAppointment on Appointment #' + str(appointmentID))

# schedule an event to be run
#appointment: Appointment
#time: timedelta
def startAppointmentScheduledEvent(appointmentID, timediff):
    logger.info('Adding Scheduler Job for Appointment #' + str(appointmentID))
    # check for Appointment Retiredness
    session = Session()
    appointments = session.query(Appointment).filter(
        Appointment.id == appointmentID)
    if appointments.count() == 0:
        logger.warning('No such Appointment #' + str(appointmentID))
        return
    thisappointment = appointments.first()
    if thisappointment.retired == True:
        log.error('Appointment #' + appointmentID +
                  ' sent to Scheduler despite it being retired!')
        return

    # check if runtime is in the past
    now = datetime.now()
    if (thisappointment.startTime - timediff) < now:
        logger.error('Appointment #' + ' scheduled Event cannot be in the past! Trying to schedule for ' +
                     thisappointment.startTime - timediff)
        return
    scheduler.add_job(terminateAppointment, trigger='date', args=[
                      appointmentID], id='Appointment Notify Job ' + str(appointmentID), run_date=thisappointment.startTime - timediff)
    logger.info('Added Scheduler Job for Appointment #' +
                str(appointmentID) + ' on ' + str(thisappointment.startTime - timediff))


def refreshAppointmentRepetition(appointment):
    logger.error('Unimplemented Method called: refreshAppointmentRepetition')
    pass

#actual Drivers is a List of the form [uid1, uid2, uid3, ...]
def retireAppointment(appointmentID, actualDrivers):
    "Called when a User wishes to retire an appointment"
    log.info('Retiring Appointment #' + appointmentID)
    session = Session()
    appointments = session.query(Appointment).filter(
        Appointment.id == appointment.id)
    if appointments.count() == 0:
        log.warning('No Appointment #' + appointment.id + 'exists')
        session.close()
        return
    thisappointment = appointments.first()
    if thisappointment.retired == True:
        logger.error('Appointment #' + appointmentID +
                     ' retiring, but is already retired!')
        session.close()
        return

    for user_app_rel in thisappointment.users:
        if user_app_rel.user_id in actualDrivers:
            user_app_rel.actualDrivingParticipation = True
        else:
            user_app_rel.actualDrivingParticipation = False
    
    thisappointment.retired = True

    logger.info('Appointment #' + str(thisappointment.id) + ' retired')
    session.commit()
    session.close()