# Moritz Basel - interne_server.py
# Version 0.0.1
import atexit
from flask import Flask, request, make_response, redirect, jsonify
from Interne_Entities import Appointment, User, User_Appointment_Rel, SQLBase

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from raven.contrib.flask import Sentry
from werkzeug import generate_password_hash, check_password_hash
from werkzeug.security import safe_str_cmp
from flask import json
from datetime import time, timedelta, datetime
from time import strftime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers import cron
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token, get_jwt_identity, get_jwt_claims, jwt_optional)
import logging

# GLOBALS:
application = Flask(__name__)
jwt = JWTManager(application)
logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()
sentry = Sentry(
    dsn='https://6ac6c6188eb6499fa2967475961a03ca:2f617eada90f478bb489cd4cf2c50663@sentry.io/232283')
Session = sessionmaker()


# LOG INITIALIZER
def initialize_log():
    now = datetime.now()
    filename = "/var/log/Mitfahrgelegenheit/Mitfahrgelegenheit-" + \
        now.strftime("%d-%m-%y") + ".log"
    try:
        logger.removeHandler(log_handler)
    except UnboundLocalError:
        pass

    log_handler = logging.FileHandler(filename)
    log_handler.setLevel(logging.DEBUG)
    log_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(log_handler)
    sql_handler = logging.FileHandler(
        '/var/log/Mitfahrgelegenheit/SQLAlchemy.log')
    logger.setLevel(application.config['LogLevel'])
    logger.info("Initialized logging to " + filename + ".")
    logging.getLogger('apscheduler').addHandler(log_handler)
    logging.getLogger('apscheduler').setLevel(logging.DEBUG)
    logging.getLogger('sqlalchemy').addHandler(sql_handler)
    logging.getLogger('sqlalchemy').setLevel(logging.DEBUG)


# init function to be called from within here (Debug client), PyTest (Test Framework) or wsgi.py (Prod)
@application.before_first_request
def initialize_everything():
    "Initializes EVERYTHING"
    if __name__ == "__main__":
        application.debug = True
    application.config['LogLevel'] = logging.DEBUG
    prod = False
    if not application.debug and not application.testing:
        prod = True
        application.config['LogLevel'] = logging.INFO

    initialize_log()            # Important logger initialization

    # LOADING CONFIG
    if prod:  # Testing somehow, loading config from working directory
        application.config.from_envvar('MITFAHRGELEGENHEIT_SETTINGS')
    else:
        application.config['JWT_SECRET_KEY'] = 'SECRET'
        application.config['SQL_ALCHEMY_ENGINE'] = 'mysql://flask_testuser:weak@monomo.solutions/Mitfahrgelegenheit'
        # TODO: ADD MYSQL CONFIG HERE OR IN SETTINGS FILE IN /etc/Mitfahrgelegnehit.conf

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
        application.config['SQL_ALCHEMY_ENGINE'], echo=False if prod else True,  pool_recycle=3200)
    logger.info('Creating SQLAlchemy Engine with engine param: ' +
                application.config['SQL_ALCHEMY_ENGINE'])
    Session.configure(bind=engine)
    SQLBase.metadata.create_all(engine)

    if prod:
        scheduler.configure(jobstores = {'default' : SQLAlchemyJobstore(engine = engine, tablename = 'APScheduler', tableschema= 'Mitfahrgelegenheit')})
        scheduler.start()
        # DEFINING THE Scheduled Trigger for Log Rollover IF NOT TESTING
        logger.info('Setting Log Rollover CronTrigger')
        scheduler.add_job(initialize_log,
                          'cron',
                          hour=0,
                          id = 'Log Rollover')
        atexit.register(lambda: scheduler.shutdown())
        sentry.init_app(application)




if __name__ == "__main__":
    application.run(host='127.0.0.1', debug=True)


# SENTRY SETUP
# empty, TODO: Find out why?


# DYNAMIC PART - REST-API
#///////////////////////////////////////////////////////////////////////////////////////////////////
@application.route('/api/users', methods=['GET'])  # TODO: Write Test
@jwt_required
def users():
    if get_jwt_claims()['globalAdminStatus'] != 1:
        return jsonify(message="Not allowed as Non-Admin"), 403

    offset = 1
    amount = 10
    if 'offset' in request.args:
        offset = request.args['offset']
    if 'amount' in request.args:
        amount = request.args['amount']

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
        return make_message_response("Bad Term in Request Body", 404)

    session = Session()
    check_for_duplicates = session.query(User).filter(
        User.username == requestJSON['username'])
    if check_for_duplicates.count() > 0:
        session.close()
        return jsonify(message="User " + requestJSON['username'] + ' already exists'), 409
    newuser = User(username=requestJSON['username'], email=requestJSON['email'],
                   phoneNumber=requestJSON['phoneNumber'], globalAdminStatus=0,
                   password=hashed_password)
    session.add(newuser)
    session.commit()
    session.close()
    # Respond 201 CREATED
    return jsonify(message="User " + requestJSON['username'] + " created"), 201


@application.route('/api/users/<int:u_id>', methods=['GET'])
@jwt_optional
def user_profileByID(u_id):  # Profile itself NYI
    "User Profile Endpoint - ID"
    session = Session()
    users = session.query(User).filter(User.id == u_id)
    if users.count() == 0:
        session.close()
        return jsonify(message='User does not exist'), 404
    user = users.first()
    session.close()
    return jsonify(user.getAsJSON()), 200


@application.route('/api/users/<string:user_name>', methods=['GET'])
@jwt_optional
def userByName(user_name):
    "User profile redirect Username --> UserID"
    session = Session()
    users = session.query(User).filter(User.username == user_name)
    if users.count() == 0:
        session.close()
        return jsonify(message='User does not exist'), 404
    user = users.first()
    session.close()
    return redirect('/api/users/' + user.id)


@application.route('/api/appointments/<appointmentID>')  # Not yet implemented
@jwt_required
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
    session.close()
    return jsonify(appointment.getAsJSON()), 200


@application.route('/api/auth', methods=['POST'])  # complete, Test Complete
def authenticate_and_return_accessToken():
    "Authentication endpoint, returns 200 {access_token : xyz} on success"
    logger.info('User Access Token Request')
    if not request.is_json:
        logger.info("Invalid Request in /api/auth. header content-type is: " +
                    request.headers['content-type'])
        return make_message_response("Missing JSON request", 400)
    requestJSON = json.loads(request.data)
    if 'username' not in requestJSON or 'password' not in requestJSON:
        return make_message_response("Missing username or password fields", 400)

    session = Session()
    users = session.query(User).filter(
        User.username == requestJSON['username'])
    if users.count() == 0:
        logger.info('Invalid Access Token Request (Username ' +
                    requestJSON['username'] + ' does not exist')
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
        if uname != uclaims['username'] and uclaims['globalAdminStatus'] != 1:
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
    return 204


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
    if get_jwt_claims()['globalAdminStatus'] == 0:
        return jsonify(message="Illegal Non-Admin Operation"), 401

    now = datetime.now()
    filename = "/var/log/Mitfahrgelegenheit/Mitfahrgelegenheit-" + \
        now.strftime('%d-%m-%y') + ".log"
    logger.info('Sending Logfile: ' + filename)
    latest = request.args.get('latest')
    if latest == 'true':
        try:
            logstr = open(filename, 'r').read()
            return jsonify(log=logstr, time=now.strftime("%d-%m-%y"))
        except Exception as ex:
            return jsonify(exception=str(ex)), 500
    return jsonify(message="Only ?latest=true allowed"), 422

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
    return make_json_response(msg, 401)
