# -*- coding: utf-8 -*-
# Moritz Basel - interne_server.py
# Version 1.0.0
# Licensed under CC-by-nc-nd
import atexit
import configparser
import logging
import os
import sys

from datetime import datetime, time, timedelta
from random import randint
from time import strftime

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers import cron
from flask import (Flask, json, jsonify, make_response, redirect, request,
                   url_for)
from flask_jwt_extended import (JWTManager, create_access_token,
                                get_jwt_claims, get_jwt_identity, jwt_optional,
                                jwt_required)
from raven.conf import setup_logging
from raven.contrib.flask import Sentry
from raven.handlers.logging import SentryHandler
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker, scoped_session
from validate_email import validate_email
from werkzeug import check_password_hash, generate_password_hash
from werkzeug.security import safe_str_cmp
from flask_mail import Message, Mail

from Interne_Entities import Appointment, SQLBase, User, User_Appointment_Rel
import Interne_helpers

# GLOBALS:
application = Flask(__name__)
jwt = JWTManager(application)
logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()
sentry = Sentry(
    dsn='https://3fb25fb74b6c4cf48f5c0e8ff285bc51:a36099e9044e4b0ab09224bddd652489@sentry.monomo.solutions/2')
Session = scoped_session(sessionmaker())
mail = Mail(application)
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
    application.config['LogLevel'] = logging.DEBUG
    application.config['JSON_AS_ASCII'] = False
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
    try:
        with open("Version.conf") as f:
            conf = configparser.RawConfigParser(allow_no_value=True)
            conf.read_file(f)
            logger.info('API Version: ' + conf.get('VERSION', 'VERSION'))
    except:
        logger.error('Could not determine Version')
    
    # SQLALCHEMY SETUP
    engine = create_engine(
        application.config['SQL_ALCHEMY_ENGINE'], echo=False,  pool_recycle=3200)
    logger.info('Creating SQLAlchemy Engine with engine param: ' +
                application.config['SQL_ALCHEMY_ENGINE'])
    Session.configure(bind=engine)
    SQLBase.metadata.create_all(engine)

    application.config['MAIL_SUPPRESS_SEND'] = True
    if prod:

        apscheduleSqliteEngine = create_engine(
            'sqlite:///APSchedule.db', echo=False)
        scheduler.configure(
            jobstores={'default': SQLAlchemyJobStore(engine=apscheduleSqliteEngine)})
        scheduler.start()
        sentryhandler = SentryHandler(
            'https://3fb25fb74b6c4cf48f5c0e8ff285bc51:a36099e9044e4b0ab09224bddd652489@sentry.monomo.solutions/2')
        sentryhandler.setLevel(logging.ERROR)
        setup_logging(sentryhandler)

        sentry.init_app(application)
        application.config['MAIL_SUPPRESS_SEND'] = False
        #sentry.captureMessage('Setup on Flask at ' + str(datetime.now()))


def UserSentryContext(originalFunction):
    def decoratedFunction(*args, **kwargs):
        prod = True if (application.testing == False and application.debug == False) else False
        if prod:
            sentry.client.context.merge({'user' : get_jwt_claims(), 'userid' : get_jwt_identity()})
        return originalFunction(*args, **kwargs)
        if prod:
            sentry.client.context.clear()
            
    #different for python2 vs python3!
    if sys.version_info >= (3,0):
        decoratedFunction.__name__ = originalFunction.__name__
    else:
        decoratedFunction.func_name = originalFunction.func_name

    return decoratedFunction

@application.teardown_appcontext
def shutdown_session(exception=None):
    Session.remove()


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
                         'status: int': 'Status of an Appointment; see docs'}

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
                sentry.captureException(extra={'tags': options})
            except:
                logger.error('Sending Sentry Event Failed')
    returnJSON['endpoints'] = routes

    return jsonify(returnJSON), 200


@application.route('/api/users', methods=['GET'])  # TODO: Write Test
@jwt_required
def users():

    logger.info('User List Request by '+ get_jwt_claims()['username'])
    returnJSON = []
    session = Session()
    try:
    
        for instance in session.query(User):
            returnJSON.append(instance.getAsJSON())
    except:
        logger.exception('An Error occured while constructing user list')
        session.close()
        return jsonify(message='Serverside Error'), 500
    session.close()
    logger.info('Returning Userlist, size ' + str(len(returnJSON)))
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
        logger.exception()
        return jsonify(message="Malformed JSON"), 400

    # check for JSON keys
    if 'email' not in requestJSON or 'password' not in requestJSON:
        return make_message_response("Signup must contain (password, email) JSON keys", 400)
    if 'phoneNumber' not in requestJSON or 'username' not in requestJSON:
        return make_message_response("Signup must contain (username, phoneNumber) JSON Keys", 400)
    
    success = False
    try:
        a = int(requestJSON['username'])
    except:
        success = True
    if success == False:
        logger.warning('Username ' + requestJSON['username'] + ' is invalid')
        return jsonify(message='Invalid Username')

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
        logger.warning('User ' + requestJSON['username'] +
                       ' already exists with ID ' + str(check_for_duplicates.first().id))
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
@jwt_required
@UserSentryContext
def doSomethingWithThisUser(u_id):
    try:
        a = int(u_id)
    except ValueError:
        logger.error('Somehow an non-int slipped through! in /api/users/u_id')
        return jsonify(message="Error: " + str(u_id) + ' not an integer!')

    if request.method == 'PATCH':
        return patchUser(u_id)
    if request.method == 'PUT':
        return patchUser(u_id)
    if request.method == 'GET':
        return user_profileByID(u_id)
    if request.mehod == 'DELETE':
        return jsonify(message='This Method is not implemented here (yet)'), 405


@application.route('/api/users/<string:u_name>', methods=['GET'])
def getUserID(u_name):
    "Return id of user"
    session = Session()
    users = session.query(User).filter(User.username == u_name)
    if users.count() == 0:
        session.close()
        return jsonify(message='User ' + u_name + ' does not exist'), 404
    user = users.first()
    uid = user.id
    session.close()
    return jsonify(id = uid), 200


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
                    'User ' + uclaims['username'] + 'illegaly attempts to elevate Admin Privileges to ' + str(requestJSON['globalAdminStatus']))
                return jsonify(message='Not allowed'), 404
        except ValueError:
            return jsonify(message='Illegal Type in field "globalAdminStatus"'), 422
    if 'username' in requestJSON:
        logger.info('Username change is noe allowed!')

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
    if 'username' in requestJSON:
        logstring = logstring + 'username ' +  str(requestJSON['username']) + ', '
        thisuser.username = requestJSON['username']
        
    session.commit()
    logger.info('Changed User ' + thisuser.username +
                '. Changed Keys: ' + logstring)
    session.close()
    return json.dumps(thisuser.getAsJSON()), 200


@application.route('/api/users/<int:u_id>/distance', methods=['GET'])
@jwt_required
@UserSentryContext
def getDistance(u_id):
    "Retrieves the Distance a single User has actively driven in the past"
    d = getUserTotalDistance(u_id)
    if d == -1:
        return jsonify(message='An Error occured'), 500
    returnJSON = {}
    returnJSON['distance'] = d
    return jsonify(returnJSON), 200


def getUserAppointments(u_id):
    "Return just a User's Appointments"
    # TODO: write test

    session = Session()
    
    #retrieve the user
    users = session.query(User).filter(User.id == u_id)
    if users.count() == 0:
        logger.warning('User ' + str(u_id) + ' does not exist!')
        session.close()
        return jsonify(message='User ' + str(u_id) + ' does not exist!'), 404
    thisuser = users.first()
    logger.info('User ' + get_jwt_claims()['username'] + ' requesting Appointment List for ' + thisuser.username)

    #construct the actual list
    returnJSON = []
    for user_app_rel in thisuser.appointments:
        returnJSON.append(user_app_rel.appointment.getAsJSON())
    
    session.close()
    logger.info('Created User Appointment List for User ' + get_jwt_claims()['username'] + ', containing ' + str(len(returnJSON)) + ' entities')
    return jsonify(returnJSON), 200

@application.route('/api/users/<int:u_id>/appointments', methods=['GET'])
@jwt_required
@UserSentryContext
def userAppointments(u_id):
    # check privileges - REMOVED! Everybody is allowed to do this

    return getUserAppointments(u_id)





@application.route('/api/users/<int:u_ID>/appointments/<int:a_ID>', methods=['PUT'])
def putAppointment(u_id):
    "Add an existing appointment to a User (in the sense that he will be taking part)"
    logger.info(
        'Call to /api/users/uid/appointments/aid redirecting to /api/appointments/aid/users/uid 307', code=307)
    return redirect('/api/appointments/' + str(a_ID) + '/users/' + str(u_ID), code=307)


@application.route('/api/appointments/<appointmentID>', methods=['GET', 'DELETE'])
@jwt_required
@UserSentryContext
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
        User_Appointment_Rel.__table__.delete().where(User_Appointment_Rel.appointment_id == appointmentID)
        session.delete(appointment)
        session.commit()
        logger.info('Appointment ' + appointmentID + ' deleted')
    except:
        logger.exception('Deletion of Appointment ID' +
                     str(appointmentID) + ' unsuccessful')
    finally:
        session.close()

    try:
        scheduler.remove_job('Appointment Notify Job ' + str(appointmentID))
    except:
        logger.error(
            'Could not remove Appointment Notify Job to Appointment #' + str(appointmentID))

    return '', 204


@application.route('/api/appointments/<int:a_ID>/retire', methods=['POST'])
@jwt_required
@UserSentryContext
def api_retire_appointment(a_ID):
    "API Endpoint to retire and appointment after it has been run and fix the driver list"
    try:
        requestJSON = json.loads(request.data)
    except:
        sentry.captureException()
        return jsonify('JSON syntax Error'), 400

    
    logger.info('Retire Command on Appointment #' + str(a_ID) +
                ' by User ' + get_jwt_claims()['username'])
    
    driverList = requestJSON['drivers']
    try:
        retireAppointment(a_ID, driverList)
    except:
        logger.error('Retiring Appointment #' + str(a_ID) + ' unsuccessful!')
        return jsonify(message='An Internal Error occured'), 500

    return jsonify(message='Success'), 200


@application.route('/api/appointments/<int:a_ID>/drivingDistribution', methods=['GET'])
@jwt_required
@UserSentryContext
def getDrivingDistribution(a_ID):
    "Retrieves the driving distribution for an appointment, if it is locked already"

    logger.info('Driving Distribution request for appointment #' +
                str(a_ID) + ' from User ' + get_jwt_claims()['username'])

    # query the Appointment
    session = Session()
    appointments = session.query(Appointment).filter(Appointment.id == a_ID)
    if appointments.count() == 0:
        logger.warning('Appointment #' + str(a_ID) + ' does not exist')
        session.close()
        return jsoinfy(message='Appointment does not exist'), 404
    thisappointment = appointments.first()

    returnJSON = dict()
    # check the appointment is in a valid state for driver list retrieval
    if thisappointment.status == Interne_helpers.APPOINTMENT_UNFINISHED:
        session.close()
        message = 'Appointment #' + str(a_ID) + ' not locked yet. Driver List Retrieval Impossible.'
        logger.warning(message)
        returnJSON['status'] = False
        returnJSON['message'] = message
        return jsonify(returnJSON), 422

    if thisappointment.status == Interne_helpers.APPOINTMENT_RETIRED:
        session.close()
        message='Appointment #' + str(a_ID) + ' already retired. Driver List Retrieval Impossible.'
        logger.warning(message)
        returnJSON['status'] = False
        returnJSON['message'] = message
        return jsonify(returnJSON), 422

    if thisappointment.status == Interne_helpers.APPOINTMENT_LOCKED_NO_FIT:
        session.close()
        message='Appointment #' + str(a_ID) + ' has no viable driving Configuration.'
        logger.warning(message)
        returnJSON['status'] = False
        returnJSON['message'] = message
        return jsonify(returnJSON), 422

    if thisappointment.status == Interne_helpers.APPOINTMENT_BROKEN:
        session.close()
        message = 'Appointment #' + str(a_ID) + ' broken. Driver List Retrieval Impossible.'
        logger.warning(message)
        returnJSON['status'] = False
        returnJSON['message'] = message
        return jsonify(returnJSON), 422

    returnJSON = {}
    drivingGroups = {}
    try:
        for user_app_rel in thisappointment.users:
            driver = user_app_rel.designatedDriverUser
            if driver.id not in drivingGroups:
                drivingGroups[driver.id] = []
            drivingGroups[driver.id].append(user_app_rel.user_id)
    except:
        logger.exception('Error construction drivingGroups for Appointment #' + str(a_ID))
        session.close()
        return jsonify(message='Error construction drivingGroups for Appointment #' + str(a_ID)), 500

    returnJSON['status'] = True
    returnJSON['message'] = 'Generated Driving Group for Appointment #' + str(a_ID)
    returnJSON['participationList'] = drivingGroups
    logger.info('Generated Driving Group for Appointment #' + str(a_ID))
    session.close()
    return jsonify(returnJSON), 200


@application.route('/api/appointments/<int:a_ID>/users', methods=['GET'])
@jwt_required
@UserSentryContext
def getAppUsers(a_ID):
    logger.info('User ' + get_jwt_claims()
                ['username'] + ' requesting User List to Appointment ' + str(a_ID))
    
    try:
        session = Session()
        thisappointment = session.query(Appointment).get(a_ID)
        if thisappointment == None:
            session.close()
            return jsonify(message="No Such Appointment"), 404

        returnJSON = []
        for user_app_rel in session.query(User_Appointment_Rel).join(User, User_Appointment_Rel.user_id == User.id).filter(User_Appointment_Rel.appointment_id == a_ID):
            appendJSON = user_app_rel.user.getAsJSON()
            appendJSON['drivingLevel'] = user_app_rel.drivingLevel
            appendJSON['actualDrivingParticipation'] = user_app_rel.actualDrivingParticipation
            appendJSON['maximumPassengers'] = user_app_rel.maximumPassengers
            returnJSON.append(appendJSON)

        logger.info('Returning Appointment ' + str(a_ID) +
                        ' User List, containing ' + str(len(returnJSON)) + ' entities')
    except:
        logger.exception('An Error occured constructing participant list to Appointment ' + str(a_ID))
        session.close()
        return jsonify(message='An Error has occured while constructing participant List to Appointment ' + str(a_ID)), 500

    session.close()
    return jsonify(returnJSON), 200


@application.route('/api/appointments/<int:a_ID>/users/<int:u_ID>', methods=['PUT', 'GET'])
@jwt_required
@UserSentryContext
def putAppUser(a_ID, u_ID):
    "Add an existing appointment to a User (in the sense that he will be taking part)"
    if request.method == 'GET':
        logger.info(
            'GET on /api/appointments/a_ID/users/u_ID redirecting to user profile')
        return redirect('/api/users/' + str(u_ID))

    session = Session()

    # check if Appointment exists:
    thisappointment = session.query(Appointment).get(a_ID)
    if thisappointment is None:
        session.close()
        return jsonify(message='No such Appointment exists'), 404

    #check appointment status:
    if thisappointment.status != Interne_helpers.APPOINTMENT_UNFINISHED:
        session.close()
        logger.info('Appointment #' + str(a_ID) + ' is not unfinished')
        return jsonify(message='Can only add participants to unfinished Appointmetns'), 409

    # check if user exists:
    users = session.query(User).filter(User.id == u_ID)
    if users.count() == 0:
        return jsonify(message='No such User exists'), 404
    thisuser = users.first()

    logger.info('User ' + get_jwt_claims()
                ['username'] + ' attempts to add ' + thisuser.username + ' to Appointment #' + str(a_ID))
    logger.debug('Request:')
    logger.debug(request.data)
    # Some basic checks for request syntax and semantics
    if not request.is_json:
        logger.info('Invalid Request on putAppuser')
        return jsonify(message='Expect JSON Body'), 400
    try:
        requestJSON = json.loads(request.data)
    except:
        logger.warn('Illegal Request Syntax in putAppUser')
        return jsoinfy('Expect JSON Body'), 400

    if 'drivingLevel' not in requestJSON:
        return jsonify('Expect drivingLevel Integer JSON key'), 409

    try:
        drivingLevel = int(requestJSON['drivingLevel'])
    except ValueError:
        logger.info('Illegal Value for drivingLevel: ' + str(requestJSON['drivingLevel']))
        return jsonify(message='Illegal Value for drivingLevel', drivingLevel=requestJSON['drivingLevel'])

    if drivingLevel != 0:
        if 'maximumPassengers' not in requestJSON:
            logger.warning(
                'maximumPassengers not in Request for adding User to Appointment')
            return jsonify(message='If drivingLevel is not 0, supply maximumPassengers key'), 422
        if requestJSON['maximumPassengers'] < 1:
            logger.info('maximumPassengers ' + str(requestJSON['maximumPassengers']) + ' is smaller than one')
            return jsonify(message='maximumPassengers ' + str(requestJSON['maximumPassengers']) + ' is smaller than one'), 422

    # check priviliges:
    if get_jwt_claims()['globalAdminStatus'] < 1:
        if get_jwt_identity() != u_ID:
            logger.warning('User ' + get_jwt_claims()['username'] + ' tried to add ' +
                        thisuser.username + ' to an Appointment as Non-Admin')
            return jsonify('Non-Admin can only add him/herself to Appointments'), 403


    # check if relationship already exists
    try:
        rel = session.query(User_Appointment_Rel).get((thisuser.id, thisappointment.id))
        if rel is not None:
            # Relationship already exists
            rel.drivingLevel = drivingLevel
            if drivingLevel != 0:
                rel.maximumPassengers = int(requestJSON['maximumPassengers'])
            session.commit()
            name = thisuser.username
            session.close()
            return jsonify(message='Updated User ' + name + ' to Appointment #' + str(a_ID)), 200
    except:
        logger.exception("Error updating User Driving Participation")
        try:
            session.close()
        except:
            pass
        return jsonify(message='An Error occured updating User Driving Participation'), 500


    # build the relationshio column
    try:
        if requestJSON['drivingLevel'] == 0:
            rel = User_Appointment_Rel(drivingLevel = drivingLevel)
        else:
            rel = User_Appointment_Rel(drivingLevel=
                drivingLevel, maximumPassengers = int(requestJSON['maximumPassengers']))
    except ValueError:
        logger.warn('drivingLevel was not an Integer: drivingLevel : ' +
                    str(drivingLevel))
        return jsonify('Expect integer drivingLevel'), 409
    try:

        rel.appointment = thisappointment
        thisuser.appointments.append(rel)
        session.add(rel)
        session.commit()
    except:
        logger.exception(
            'SQLAlchemy Error on building User_Takes_Part')
        session.close()
        return jsonify(message='Unfortunately, an error occured'), 500

    logger.info('Added User ' + thisuser.username +
                ' to Appointment ' + str(a_ID))

    session.close()
    return jsonify(message='Success'), 200  # TODO: Add test


@application.route('/api/appointments', methods=['GET', 'POST'])
@jwt_required
@UserSentryContext
def appointments():
    if request.method == 'GET':
        return getAppointments()
    if request.method == 'POST':
        return makeAppointment()
    return jsonify(message='Method not allowed'), 405


def getAppointments():
    "Get a list of appointments"
    # request argument parsing
    logger.info('User ' + get_jwt_claims()
             ['username'] + ' requesting Appointment List')
    showFinished = False
    if 'finished' in request.args:
        showFinished = True if request.args['finished'] == 'true' else False
    logger.info('Showing finished Appointments: ' + str(showFinished))
    session = Session()
    if showFinished == True:
        appointments = session.query(
            Appointment).all()
    else:
        appointments = session.query(Appointment).filter(
            Appointment.status != Interne_helpers.APPOINTMENT_RETIRED).all()
    retListJSON = []

    for app in appointments:
        retListJSON.append(app.getAsJSON())
    session.close()
    logger.info('Generated Appointment List; size: ' + str(len(retListJSON)))
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

    requiredKeys = ['startLocation', 'distance']
    for key in requiredKeys:
        if key not in requestJSON:
            logger.warning('Missing JSON key: ' + key + ' in makeAppointment')
            return jsonify(message='Missing JSON key: ' + key), 422
    if 'repeatTime' in requestJSON:
        rTime = requestJSON['repeatTime']
    else:
        rTime = 'None'
    try:
        logger.info('repeatTime: ' + str(requestJSON['repeatTime']) + ' rTime: ' + str(rTime))
    except KeyError:
        logger.info('rTime: ' + str(rTime))

    if 'startTime' not in requestJSON and 'startTimeTimestamp' not in requestJSON:
        logger.warning('Missing JSON key: startTime or startTimeTimestamp in makeAppointment')
        return jsonify(message='Missing JSON key: startTime or startTimeTimestamp'), 422


    #to maintain backwards compatibility, startTime is also a timestamp
    if 'startTimeTimestamp' in requestJSON:
        appTime = datetime.fromtimestamp(requestJSON['startTimeTimestamp'])
    else:
        appTime = datetime.fromtimestamp(requestJSON['startTime'])
    
    now = datetime.now()
    if appTime < now:
        logger.info('Appointment Time is in the past: ' + str(appTime) +' before ' + str(now))
        return jsonify(message='Appointment Time is in the Past: ' + str(appTime) + ' before ' + str(now)), 422
    
    if appTime < (now + timedelta(hours=1)):
        logger.info('Appointment Time is too close in the future'  + str(appTime) +' before ' + str(now))
        return jsonify(message='Appointment Time is too close in the future'  + str(appTime) +' before ' + str(now)), 422
    session = Session()
    try:
        newappointment = Appointment(startLocation=requestJSON['startLocation'],
                                 startTime=appTime,
                                 repeatTime=rTime,
                                 status=Interne_helpers.APPOINTMENT_UNFINISHED,
                                 distance=requestJSON['distance'],
                                 targetLocation=requestJSON['targetLocation'])
    except:
        logger.exception('Error creating Appointment')
        session.close()
        return jsonify(message='An Error Occured'), 500
    
    session.add(newappointment)
    session.commit()

    try:
        logger.info('Added new Appointment on ' +
                    str(newappointment.startTime))
    except ValueError:
        logger.error(
            'Could not print Date of newly created Appointment! ID: ' + str(newappointment.id))

    try:
        startAppointmentScheduledEvent(newappointment.id, timedelta(hours=1))
    except:
        logger.exception('Error adding scheduled Job for terminateEvent for Appointment ' + str(newappointment.id))
        session.close()
        return jsonify(message='An Error occured'), 500
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
        token = create_access_token(identity=thisuser, expires_delta = timedelta(days=365))
        logger.debug('Access Token: Bearer ' + token)
        session.close()
        return jsonify(access_token=token, username=thisuser.username, email=thisuser.email, globalAdminStatus=thisuser.globalAdminStatus, phoneNumber=thisuser.phoneNumber), 200
    else:
        session.close()
        logger.info(
            'Invalid Password in Access Token Request for user: ' + requestJSON['username'])
        return jsonify(message='Invalid Username or Password'), 403


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
    User_Appointment_Rel.__table__.delete().where(User_Appointment_Rel.user_id == thisuser.id)

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


def getUserTotalDistance(u_ID):
    "Retrieves the total traveled distance"
    session = Session()
    users = session.query(User).filter(User.id == u_ID)
    if users.count() == 0:
        logger.error('getUserTotalDistance: User #' + str(u_ID) +
                     ' does not exist', extra={'tags': 'getUserTotalDistance'})
        return -1

    thisuser = users.first()

    totaldistance = 0
    for user_app_rel in thisuser.appointments:
        if user_app_rel.actualDrivingParticipation == True:
            totaldistance = totaldistance + user_app_rel.appointment.distance

    logger.info('Calculated total driven distance of User ' +
                thisuser.username + ' to be ' + str(totaldistance))
    return totaldistance


def distributePassengersOnDrivers(listOfAllDrivers, listOfAllPassengers, appointmentID, session):
    

    totalNumberOfDrivers = len(listOfAllDrivers)

    
    # alright, so now an algorithmic challenge...
    # distribute all passengers onto their drivers!


    drivingDict = dict()
    for user_id in listOfAllDrivers:
        drivingDict[user_id] = list()

            
    finishedPassengers = set()
    for user_id in listOfAllPassengers:
        if user_id in listOfAllDrivers:
            drivingDict[user_id].append(user_id)
            finishedPassengers.add(user_id)

    for user_id in finishedPassengers:
        listOfAllPassengers.remove(user_id)
    finishedPassengers.clear()
    # we now have handled all drivers (who will of course have themselves as passenger)
    logger.debug('drivingDict after distributing only drivers')
    logger.debug(drivingDict)


    # randomly distribute passengers on cars
    for user_id in listOfAllPassengers:
        k = randint(0, len(listOfAllDrivers) - 1)
        drivingDict[listOfAllDrivers[k]].append(user_id)

        datuser = session.query(User_Appointment_Rel).get((listOfAllDrivers[k], appointmentID))
        if len(drivingDict[listOfAllDrivers[k]]) == datuser.maximumPassengers:
            del listOfAllDrivers[k]
    # drivingDict now holds a dictionary containing a valid configuration of drivers to cars
    logger.debug('drivingDict after distributing everyone drivers')
    logger.debug(drivingDict)

    # write to DB
    for driver in drivingDict:
        driverUser = session.query(User).get(driver)
        for passenger in drivingDict[driver]:
            passengerUserAppRel = session.query(User_Appointment_Rel).get((passenger, appointmentID))
            passengerUserAppRel.designatedDriverUser = driverUser

    logger.info('Distributed ' + str(len(listOfAllPassengers)) + ' Participants onto ' +
                        str(len(listOfAllDrivers)) + ' drivers on Appointment # ' + str(appointmentID))
    logger.info('Writing Driver Distribution Information for Appointment #' +
                        str(appointmentID) + ' to DB.')
    session.commit()



def terminateAppointment(appointmentID):
    "terminateAppointment is called by the scheduler 1 hour before the appointment takes place"
    logger.info('Executing terminateAppointment for Appointment #' + str(appointmentID))
    # get Number of total possible Passengers including only
    # Definite Drivers - drivingLevel #1
    definiteDriversPassengerAmount = 0
    # Possible Drivers - drivingLevel #2
    possibleDriversPassengerAmount = 0

    # totalParticipants holds the total number of Users that want to take part in this appointment
    totalParticipants = 0

    session = Session()
    appointments = session.query(Appointment).filter(
            Appointment.id == appointmentID)
    if appointments.count() == 0:
        logger.error('terminateAppointment called on a nonexisting Appointment!!(#' +
                            str(appointmentID) + ') This is bad news!')
        return
    thisappointment = appointments.first()


    try:
        
        for user_app_rel in thisappointment.users:
            if user_app_rel.drivingLevel == 1:
                definiteDriversPassengerAmount = definiteDriversPassengerAmount + \
                    user_app_rel.maximumPassengers
                possibleDriversPassengerAmount = possibleDriversPassengerAmount + \
                    user_app_rel.maximumPassengers
            if user_app_rel.drivingLevel == 2:
                possibleDriversPassengerAmount = possibleDriversPassengerAmount + \
                    user_app_rel.maximumPassengers
            totalParticipants = totalParticipants + 1

        logger.info('Appointment #' + str(appointmentID) + \
        '  definiteDriversPassengerAmount: ' + str(definiteDriversPassengerAmount) + \
        ', possibleDriversPassengerAmount: ' + str(possibleDriversPassengerAmount) + \
        ', totalParticipants: ' + str(totalParticipants))


        if possibleDriversPassengerAmount == 0 and totalParticipants == 0:
            logger.info('Appointment #' + str(appointmentID) + ' has no space for passengers and no passengers. Exiting terminateAppointment')
            thisappointment.status = Interne_helpers.APPOINTMENT_RETIRED
            session.commit()
            session.close()
            return
        
        # good News !! Everyone fits!
        if totalParticipants <= definiteDriversPassengerAmount:
            logger.info(
                'Everyone fits into Definite Driver Seats on Appointment #' + str(thisappointment.id))

            thisappointment.status = Interne_helpers.APPOINTMENT_LOCKED_EVERYONE_FITS_DEFINITE

            listOfAllDrivers = []
            listOfAllPassengers = []
            for user_app_rel in thisappointment.users:
                listOfAllPassengers.append(user_app_rel.user_id)
                if user_app_rel.drivingLevel == 1:
                    listOfAllDrivers.append(user_app_rel.user_id)
            
            logger.debug('listOfAllDrivers:')
            logger.debug(listOfAllDrivers)
            logger.debug('listOfAllPassengers')
            logger.debug(listOfAllPassengers)

            distributePassengersOnDrivers(listOfAllDrivers, listOfAllPassengers, appointmentID, session)


        # sortof good News !! everyone fits..at least including the may-drivers
        if totalParticipants > definiteDriversPassengerAmount and totalParticipants <= possibleDriversPassengerAmount:
            logger.info(
                'Not everyone fits into Definite Driver Seats. Taking Possible Drivers into Account on Appointment #' + str(thisappointment.id))
            thisappointment.status = Interne_helpers.APPOINTMENT_LOCKED_EVERYONE_FITS_POSSIBLE
            session.commit()
            listOfAllDrivers = []
            listOfAllPassengers = []
            for user_app_rel in thisappointment.users:
                listOfAllPassengers.append(user_app_rel.user_id)
                if user_app_rel.drivingLevel == 1 or user_app_rel.drivingLevel ==2:
                    listOfAllDrivers.append(user_app_rel.user_id)
            
            logger.debug('listOfAllDrivers:')
            logger.debug(listOfAllDrivers)
            logger.debug('listOfAllPassengers')
            logger.debug(listOfAllPassengers)

            distributePassengersOnDrivers(listOfAllDrivers, listOfAllPassengers, appointmentID, session)
            

        if totalParticipants > possibleDriversPassengerAmount:
            logger.warning(
                'Not everyone even fits onto Possible Driver Seats on Appointment #' + str(thisappointment.id) + '!')
            thisappointment.status = Interne_helpers.APPOINTMENT_LOCKED_NO_FIT
            session.commit()
            mailmsg = Message("Fahrerkonfiguration ueberpruefen!",
                            sender=("Errorhanlder at Mitfahrgelegenheit", "no-reply@monomo.solutions"),
                            recipients=[])
            recipientList = []
            for user_app_rel in thisappointment.users:
                recipientList.append(user_app_rel.user.username)
                mailmsg.add_recipient(user_app_rel.user.email)
            
            appointmentDate = thisappointment.startTime
            appointmentDateString = appointmentDate.strftime("%A, %d.%m.%y  %H:%M")
            mailmsg.body = "Achtung!\nIm Appointment #%s am %s nach %s gibt es zuwenige Fahrer! Folgend finden Sie alle Telefonnummern und Emails der Teilnehmer." % (str(thisappointment.id), appointmentDateString, thisappointment.targetLocation)
            
            for user_app_rel in thisappointment.users:
                user = user_app_rel.user
                mailmsg.body = mailmsg.body + "\n%s: %s %s" % (user.username, user.phoneNumber, user.email)
            
            mailmsg.body = mailmsg.body +"\n\nBitte Um Einigung!!"
            try:
                mail.send(mailmsg)
            except:
                logger.exception('Failed to send Mail')
            
            logger.info('Sent Mail to some people about OOB-Solution')
            logger.info('Mail Body:')
            logger.info(mailmsg.body)
            logger.info('Recipients:')
            logger.info(str(recipientList))
    

        if thisappointment.repeatTime == "Daily":
            logger.info('Creating new Appointment 1 day after Appointment #' + str(thisappointment.id))
            try:
                newappointment = Appointment(startLocation=thisappointment.startLocation,
                                    startTime = thisappointment.startTime + timedelta(days=1),
                                    repeatTime = "Daily",
                                    status = Interne_helpers.APPOINTMENT_UNFINISHED,
                                    distance = thisappointment.distance,
                                    targetLocation = thisappointment.targetLocation)
                session.add(newappointment)
                session.commit()
                logger.info('Added new Appointment #' + str(newappointment.id) + 'on ' + str(newappointment.startTime))
                try:
                    startAppointmentScheduledEvent(newappointment.id, timedelta(hours=1))
                except:
                    logger.exception('Error adding scheduled Job for terminateEvent #' + str(newappointment.id))
            except:
                logger.exception('Could not create repeated Appointment')

        if thisappointment.repeatTime == "Weekly":
            logger.info('Creating new Appointment 1 week after Appointment #' + str(thisappointment.id))
            try:
                newappointment = Appointment(startLocation=thisappointment.startLocation,
                                    startTime = thisappointment.startTime + timedelta(days=7),
                                    repeatTime = "Weekly",
                                    status = Interne_helpers.APPOINTMENT_UNFINISHED,
                                    distance = thisappointment.distance,
                                    targetLocation = thisappointment.targetLocation)
                session.add(newappointment)
                session.commit()
                logger.info('Added new Appointment #' + str(newappointment.id) + 'on ' + str(newappointment.startTime))
                try:
                    startAppointmentScheduledEvent(newappointment.id, timedelta(hours=1))
                except:
                    logger.exception('Error adding scheduled Job for terminateEvent #' + str(newappointment.id))
            except:
                logger.exception('Could not create repeated Appointment')


    except:
        thisappointment.status = Interne_helpers.APPOINTMENT_BROKEN
        session.commit()
        logger.exception('Something went terribly wrong in terminateAppointment! Appointment #' + str(thisappointment.id) + ' is broken!')
    finally:
        session.close()

    logger.info('Exiting terminateAppointment on Appointment #' +
                str(appointmentID))

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
        session.close()
        return
    thisappointment = appointments.first()
    if thisappointment.status == Interne_helpers.APPOINTMENT_RETIRED:
        log.error('Appointment #' + appointmentID +
                  ' sent to Scheduler despite it being retired!')
        session.close()
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

# actual Drivers is a List of the form [uid1, uid2, uid3, ...]


def retireAppointment(appointmentID, actualDrivers):
    "Called when a User wishes to retire an appointment"
    logger.info('Retiring Appointment #' + str(appointmentID))
    session = Session()
    appointments = session.query(Appointment).filter(
        Appointment.id == appointmentID)
    if appointments.count() == 0:
        log.warning('No Appointment #' + str(appointment.id) + ' exists')
        session.close()
        return
    thisappointment = appointments.first()
    if thisappointment.status == Interne_helpers.APPOINTMENT_RETIRED:
        logger.error('Appointment #' + appointmentID +
                     ' retiring, but is already retired!')
        session.close()
        return
    if thisappointment.status == Interne_helpers.APPOINTMENT_BROKEN:
        logger.warning('Retiring broken Appointment #' + str(thisappointment.id))
    for user_app_rel in thisappointment.users:
        if user_app_rel.user_id in actualDrivers:
            user_app_rel.actualDrivingParticipation = True
        else:
            user_app_rel.actualDrivingParticipation = False

    thisappointment.status = Interne_helpers.APPOINTMENT_RETIRED

    logger.info('Appointment #' + str(thisappointment.id) + ' retired')
    session.commit()
    session.close()
