# Moritz Basel - interne_server.py
# Version 0.0.1
from flask import Flask, request, make_response, redirect, jsonify


from sqlalchemy import create_engine, Column, Integer, String, Table, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship


from raven.contrib.flask import Sentry
from werkzeug import generate_password_hash, check_password_hash
from flask import json
from datetime import time, timedelta, datetime
from time import strftime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers import cron
import atexit

from werkzeug.security import safe_str_cmp
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token, get_jwt_identity, get_jwt_claims, jwt_optional)
import logging


application = Flask(__name__)

if __name__ == "__main__":
    application.debug = True

jwt = JWTManager(application)
mysql = 123
logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()
scheduler.start()

log_handler = logging.FileHandler('/var/log/Emergency_Logging.log')

# LOGGING INITIALIZER


def initialize_log():
    now=datetime.now()
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
    logger.setLevel(logging.INFO)
    logger.info("Initialized logging to " + filename + ".")
    logging.getLogger('apscheduler').addHandler(log_handler)
    logging.getLogger('apscheduler').setLevel(logging.DEBUG)
    logging.getLogger('sqlalchemy').addHandler(log_handler)
    logging.getLogger('sqlalchemy').setLevel(logging.DEBUG)


# LOGGING INITIALIZATION ON STARTUP
initialize_log()

# DEFINING THE Scheduled Trigger for Log Rollover IF NOT TESTING
if not application.debug and not application.testing:
    logger.info('Setting Log Rollover CronTrigger')
    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(initialize_log,
            'cron',
            second=0)
    atexit.register(lambda: scheduler.shutdown())

# LOADING CONFIG
if application.debug or application.testing:  # Testing somehow, loading config from working directory
    application.config['JWT_SECRET_KEY'] = 'SECRET'
    application.config['SQLAlchemyEngine'] = 'sqlite:///:memory:'
else:
    # Not Testing ot Debugging, loading config from Environment variable
    application.config.from_envvar('MITFAHRGELEGENHEIT_SETTINGS')
    #TODO: ADD MYSQL CONFIG HERE OR IN SETTINGS FILE IN /etc/Mitfahrgelegnehit.conf


logger.info('-------- STARTING UP --------')
logger.info('Appliction is in ' + ('TEST' if application.testing else 'NON-TEST') + ' mode')
logger.info('Application is in ' + ('DEBUG' if application.debug else 'NON-DEBUG') + ' mode')
if __name__ == "__main__":
    application.run(host='127.0.0.1', debug=True)


#SQLALCHEMY SETUP
engine= create_engine(application.config['SQLAlchemyEngine'], echo=True)
logger.info('Creating SQLAlchemy Engine with engine param: '+application.config['SQLAlchemyEngine'])
SQLBase = declarative_base()
Session = sessionmaker(bind = engine)

#SENTRY SETUP

#empty, TODO: Find out why?
#CLASS: USER
#///////////////////////////////////////////////////////////////////////////////////////////////////


    
class User(SQLBase):
    "The User class represents the User Object as well as the object relational mapping in the Database"
    # Fields:
    # id                     //The MySQL autoincreasing ID
    #username               //Username
    # password               //Hashed Password
    # email                  //Email Address
    # phoneNumber            //Phone Number
    # globalAdminStatus      //Global Admin Status, currently 0 or 1
    __tablename__ = 'users'
    id = Column(Integer, primary_key = True)
    username = Column(String)
    password = Column(String)
    email = Column(String)
    phonenumber = Column(String)
    globalAdminStatus = Column(Integer)

    appointments = relationship("User_Appointment_Rel", back_populates="user")

    def getAsJSON(self):
        "Returns a JSON representation of a User"
        return { 'id' : self.id, 'username' : self.username, 'email' : self.email, 'phonenumber' : self.phonenumber,
             'globalAdminStatus' : self.globalAdminStatus}


#CLASS: APPOINTMENT
#///////////////////////////////////////////////////////////////////////////////////////////////////


class Appointment(SQLBase):
    "Object to Entity Appointment in Database"
    # Fields:
    #id : int
    #startLocation : string
    #endLocation: string
    #time : datetime            // TBD
    #repeatPeriodDays : int
    # owningOrganization  : int       //Foreign (unused) key to an organizaztion
    # userDriverDic : dict            // JSON Dict, syntax:
    # "Guaranteed Drivers" :
    # [id, id, id, id, ...],
    # "Possible Drivers" :
    # [id, id, id, id, id, ....],
    # "Passengers :
    # [id, id, id, id, ..]
    __tablename__='appointments'
    id = Column (Integer, primary_key = True)
    users = relationship("User_Appointment_Rel", back_populates="appointment")


class User_Appointment_Rel(SQLBase):
    __tablename__ = 'user_takesPart_appointment'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    appointment_id = Column(Integer, ForeignKey('appointments.id'), primary_key = True)
    drivingLevel = Column(Integer)
    appointment = relationship("Appointment", back_populates = "users")
    user = relationship("User", back_populates = "appointments")

# CREATE THE TABLES IF NONEXISTENT

SQLBase.metadata.create_all(engine)


# DYNAMIC PART - REST-API
#///////////////////////////////////////////////////////////////////////////////////////////////////
@application.route('/api/users', methods=['GET'])  # TODO: Write Test
@jwt_required
def users():
    if get_jwt_claims()['GlobalAdminStatus'] != 1:
        return make_message_response("Not allowed", 403)

    offset = 1
    amount = 10
    if 'offset' in request.args:
        offset = request.args['offset']
    if 'amount' in request.args:
        amount = request.args['amount']

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM t_Users LIMIT " +
                   str(offset), "," + str(amount) + ";")
    logger.info('Selecting all users from N'+str(offset)+', numbering '+str(amount))
    data = cursor.fetchall()
    returnList = []
    for i in (0, amount - 1):
        returnList[i] = {'id': data[i][5], 'username': data[i]
                         [0], 'email': data[i][2], 'phoneNumber': data[i][3]}
    return jsonify(returnList), 200


@application.route('/api/users', methods=['POST'])  # Complete, Test complete
def signup():
    "The Endpoint URI for signing up. Takes email, username and password JSON returns 201 on success"

    logger.info("User Signup on /api/users")

    if not request.is_json:
        return jsonify(message='Expect JSON Request'), 400
    requestJSON = json.loads(request.data)

    # check for JSON keys
    if 'email' not in requestJSON or 'password' not in requestJSON:
        return make_message_response("Signup must contain (password, email) JSON keys", 400)
    if 'phoneNumber' not in requestJSON or 'username' not in requestJSON:
        return make_message_response("Signup must contain (username, phoneNumber) JSON Keys", 400)

    # Check if User already exists
    try:
        testuser = User.loadUser(username=requestJSON['username'])
        if testuser != NOUSER:
            return make_message_response("User already exists", 409)
    except Exception:
        sentry.captureException()
        return make_message_response("Unknown Server Error, The Sentry Error Code is: " + sentry_event_id, 500)

    # hash the password
    hashed_password = generate_password_hash(requestJSON['password'])

    # CHECK for SQL Injection
    checkall = requestJSON['username'] + requestJSON['email']
    if 'DROP' in checkall or 'DELETE' in checkall or 'INSERT' in checkall or 'ALTER' in checkall or 'SELECT' in checkall:
        return make_message_response("Bad Term in Request Body", 404)

    # build the sql request
    newuser = User( username=requestJSON['username'], email = requestJSON['email'],
                    phonenumber = requestJSON['phoneNumber'], globalAdminStatus = 0,
                    password = hashed_password)
    session = Session()
    session.add(newuser)
    session.commit()
    # Respond 201 CREATED
    return jsonify(message="User " + requestJSON['username'] + " created"), 201


@application.route('/api/users/<int:u_id>', methods=['GET'])
@jwt_optional
def user_profileByID(u_id):  # Profile itself NYI
    "User Profile Endpoint - ID"
    session = Session()
    user = session.query(User).filter_by(id = u_id).first()
    return jsonify(user.getAsJSON()), 200


@application.route('/api/users/<string:user_name>', methods=['GET'])
@jwt_optional
def userByName(user_name):
    "User profile redirect Username --> UserID"
    session = Session()
    user = session.query(User).filter_by(username = user_name).first()
    return redirect('/api/users/'+user.id)


@application.route('/api/appointments/<appointmentID>')  # Not yet implemented
@jwt_required
def appointment_data(appointmentID):
    if get_jwt_claims()['GlobalAdminStatus'] != 1:
        uid = get_jwt_identity()
        cur = mysql.connection.cursor()
        cur.execute("SELECT EXISTS(SELECT 1 FROM t_relation_Users_isAPartOf_Organization WHERE 'c_ID_Users' = '" +
                    uid + "' AND 'c_ID_Organizations' = '" + appointmentID + "';")
        data = cur.fetchall()
        if (data == 0):
            return make_message_response("Either the Appointment does not exist or you are not a part of its Organization", status=404)

    uclaims = get_jwt_claims()
    logger.info("User: " + uclaims['username'] +
                " accessing appointment: " + str(appointmentID))
    return make_message_response("Appointments not yet implemented", 500)



@application.route('/api/auth', methods=['POST'])  # complete, Test Complete
def authenticate_and_return_accessToken():
    "Authentication endpoint"
    logger.info('User Access Token Request')
    if not request.is_json:
        logger.info("Invalid Request in /api/auth. header content-type is: " +
                    request.headers['content-type'])
        return make_message_response("Missing JSON request", 400)
    requestJSON = json.loads(request.data)
    if 'username' not in requestJSON or 'password' not in requestJSON:
        return make_message_response("Missing username or password fields", 400)

    session = Session()
    users = session.query(User).filter(User.username == requestJSON['username'])
    if users.count() == 0:
        logger.info('Invalid Access Token Request (Username '+requestJSON['username']+' does not exist')
        return jsonify(message = 'Invalid Username or Password'), 404
    thisuser = users.first()
    if check_password_hash(thisuser.password, requestJSON['password']):
        logger.info('Creating Access Token for '+ requestJSON['username'])
        token = create_access_token(identity = thisuser)
        return jsonify(access_token=token, username=thisuser.username, email=thisuser.email, globalAdminStatus=thisuser.globalAdminStatus, phoneNumber=thisuser.phoneNumber), 200
    else:
        logger.info
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

    uclaims = get_jwt_claims()
    if uname != uclaims['username'] and uclaims['GlobalAdminStatus'] != 1:
        logger.warning('User : ' + uclaims['username'] + ' tried to remove ' +
                       uname + '. This Endpoint should not be generally known')
        return make_message_response("Can only remove self; or requires administrative priviliges. User " + str(uclaims['username']) + " trying to remove " + uname, 401)
    cur = mysql.connection.cursor()
    cur.execute("START TRANSACTION;")
    cur.execute('DELETE FROM t_Users WHERE c_ID_Users=' +
                str(get_jwt_identity()))
    cur.execute("COMMIT;")
    logger.warning('Removed User : ' +
                   uclaims['username'] + ' - Was this intended?')
    return make_response(("", 204, None))


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
    logger.info('Logfile Request from User: ' + get_jwt_claims()['Username'])
    if get_jwt_claims()['GlobalAdminStatus'] == 0:
        return jsonify(message="Illegal Non-Admin Operation"), 401

    now=datetime.now()
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
    return jsonify(message='Resource does not exist'),404


#//////////////////////////////////////////////////////////////////////////////////////////////////
# JWT CALLBACK FUNCTIONS:

@jwt.user_claims_loader
def add_claims_to_access_token(user):
    "Defines all fields to be remembered and recovered in the JSON Token"
    return {'Username': user.username,
            'Email': user.email,
            'PhoneNumber': user.phoneNumber,
            'GlobalAdminStatus': user.globalAdminStatus}


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
