# Moritz Basel - interne_server.py
from flask import Flask, request, send_from_directory, make_response, redirect, jsonify

from flask_mysqldb import MySQL
from raven.contrib.flask import Sentry
from werkzeug import generate_password_hash, check_password_hash
from flask import json
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers import cron


from werkzeug.security import safe_str_cmp
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token, get_jwt_identity, get_jwt_claims, jwt_optional)
import logging



application = Flask(__name__)
startup=1
active_logfile=''
jwt = JWTManager(application)
mysql = MySQL(application)
logger=logging.getLogger(__name__)
scheduler=BackgroundScheduler()
scheduler.start()

#LOGGING INITIALIZER
def initialize_log():
    if startup==0:
        logger.removeHandler(log_handler)
    filename= "/var/log/Mitfahrgelegenheit/Mitfahrgelegenheit-"+time.strftime("%d-%m-%y")+".log"
    active_logfile=filename
    log_handler=logging.FileHandler(filename)
    log_handler.setLevel(logging.INFO)
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(log_handler)
    logger.setLevel(logging.INFO)


if not application.debug and not application.testing:
    initialize_log()
    scheduler.add_job(func=initialize_log,
    trigger=cron.CronTrigger(hour=0),
    id='Logger_Restart',
    name='Change the logger file every day',
    replace_existing=True)


application.config['MYSQL_USER'] = 'flaskuser'
application.config['MYSQL_PASSWORD'] = 'Test1234'
application.config['MYSQL_DB'] = 'Interne_Mitfahrgelegenheit'
application.config['MYSQL_HOST'] = '127.0.0.1'
application.config['JWT_SECRET_KEY'] = 'SomethingSomethingSecretSecret'


if __name__ == "__main__":
    sentry = Sentry(
        application, dsn='https://6ac6c6188eb6499fa2967475961a03ca:2f617eada90f478bb489cd4cf2c50663@sentry.io/232283')
    application.run(host='127.0.0.1')


startup=0
#CLASS: USER
#///////////////////////////////////////////////////////////////////////////////////////////////////


class User(object):
    "The User class represents the User Object as well as the object relational mapping in the Database"
    # Fields:
    # id                     //The MySQL autoincreasing ID
    #username               //Username
    # password               //Hashed Password
    # email                  //Email Address
    # phoneNumber            //Phone Number
    # globalAdminStatus      //Global Admin Status, currently 0 or 1

    def __init__(self, id, username, password, email, phoneNumber, globalAdminStatus):
        self.id = id
        self.username = username
        self.password = password
        self.email = email
        self.phoneNumber = phoneNumber
        self.globalAdminStatus = globalAdminStatus

    def __str__(self):
        return "User(id=%s)" % self.id

    @staticmethod
    def loadUser(uid=None, username=None):
        "returns the corresponding user. If both parameters are given returns NOUSER if they do not match. Returns NOUSER on nonexisting"
        if username == None and uid == None:
            return NOUSER
        if uid:
            # Start MYSQL connection
            cur = mysql.connection.cursor()
            cur.execute(
                "SELECT * FROM t_Users WHERE c_ID_Users='" + str(uid) + "';")
            data = cur.fetchall()
            if len(data) > 0:
                if username != None:
                    if str(data[0][0] != username):
                        return NOUSER
                return User(int(data[0][5]), str(data[0][0]), str(data[0][4]), str(data[0][2]), str(data[0][3]), int(data[0][1]))
                #              ID              Username       Hashed Password       Email           Phone Number    Global Admin Status
            else:
                return NOUSER
        if username:
            cur = mysql.connection.cursor()
            cur.execute(
                "SELECT * FROM t_Users WHERE c_name_Users= '" + username + "';")
            data = cur.fetchall()
            if len(data) > 0:
                return User(int(data[0][5]), str(data[0][0]), str(data[0][4]), str(data[0][2]), str(data[0][3]), int(data[0][1]))
                #              ID              Username       Hashed Password       Email           Phone Number    Global Admin Status
            else:
                return NOUSER


# Generic Return Code that is checked against indicating failure
NOUSER = User(id=0, username=None, password=None, email=None,
              phoneNumber=None, globalAdminStatus=None)


# DYNAMIC PART - REST-API
#///////////////////////////////////////////////////////////////////////////////////////////////////
@application.route('/api/users', methods=['POST'])  # Complete, Test complete
def signup():
    "The Endpoint URI for signing up. Takes email, username and password JSON returns 201 on success"


    logger.info("User Signup on /api/users")
    
    # Check for Sortof Valid Data
    if 'content-type' in request.headers:
        if request.headers['content-type'] != 'application/json':
            return make_message_response("Expecting application/json. Request Content-type was: " + request.headers['content-type'], 415)
    else:
        return make_message_response("No Content Type", 400)
    try:
        requestJSON = json.loads(request.data)
    except json.JSONDecodeError:
        return make_message_response("Malformed JSON in Request Body", 400)

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
        return make_message_response("Unknown Server Error, The Sentry Error Code is: " + g.sentry_event_id, 500)

    # hash the password
    hashed_password = generate_password_hash(requestJSON['password'])

    # CHECK for SQL Injection
    checkall = requestJSON['username'] + requestJSON['email']
    if 'DROP' in checkall or 'DELETE' in checkall or 'INSERT' in checkall or 'ALTER' in checkall or 'SELECT' in checkall:
        return make_message_response("Bad Term in Request Body", 404)

    # build the sql request
    sqlReq = "INSERT INTO t_Users (`c_name_Users`, `c_globalAdmin_Users`, `c_email_Users`, `c_phoneNumber_Users`, `c_passwordHash_Users`) "
    sqlReq = sqlReq + "VALUES ('" + requestJSON['username'] + "', '0', '" + \
        requestJSON['email'] + "', '" + requestJSON['phoneNumber'] + "', '" +\
        hashed_password + "');"

    # execute it
    cursor = mysql.connection.cursor()
    cursor.execute("START TRANSACTION;")
    cursor.execute(sqlReq)
    cursor.execute("COMMIT;")

    # Respond 201 CREATED
    return make_response("User " + requestJSON['username'] + " created", 201,  {'content-type': 'application/json', 'Location': ['/api/auth', '/api/users/' + requestJSON['username']]})


@application.route('/api/users/<int:u_id>', methods=['GET'])
@jwt_optional
def user_profileByID(u_id):  # Profile itself NYI
    "User Profile Endpoint - ID"
    # check for authorization: Only a global Admin or the User itself can access this resource
    activeUserID = get_jwt_identity()
    if activeUserID == None:
        return make_message_response("Cannot be accessed by Anon User", 401)
    if (get_jwt_claims()['GlobalAdminStatus'] != 1):
        if get_jwt_identity() != u_id:
            return make_message_response('Not allowed', 403)


    logger.info("Userprofile for User: ")
    # get user data from mysql db and return it
    # this will probably take the form of a JSON list of appointments
    return make_message_response("Not yet implemented", 500)



@application.route('/api/users/<string:user_name>', methods=['GET'])
@jwt_optional
def userByName(user_name):
    "User profile redirect Username --> UserID"
    thisuser=User.loadUser(username=user_name)
    if thisuser==NOUSER:
        return make_message_response("User not found", 404)
    return redirect(location='/api/users/' + str(thisuser.id))


@application.route('/api/appointments/<appointmentID>')  # Not yet implemented
@jwt_required
def appointment_data(appointmentID):
    if get_jwt_claims()['GlobalAdminStatus'] != 1:
        uid = get_jwt_identity()
        cur = mysql.connection.cursor()
        cur.execute("SELECT EXISTS(SELECT 1 FROM t_relation_Users_isAPartOf_Organization WHERE 'c_ID_Users' = '" +
                    get_jwt_identity() + "' AND 'c_ID_Organizations' = '" + appointmentID + "';")
        data = cur.fetchall()
        if (data == 0):
            return make_message_response("Either the Appointment does not exist or you are not a part of its Organization")

    uclaims=get_jwt_claims()
    logger.info("User: " + uclaims['username'] + " accessing appointment: "+str(appointmentID))
    return make_message_response("Appointments not yet implemented", 500)


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
    data = cursor.fetchall()
    returnList = []
    for i in (0, amount - 1):
        returnList[i] = {'id': data[i][5], 'username': data[i]
                         [0], 'email': data[i][2], 'phoneNumber': data[i][3]}
    return make_json_response(returnList, 200)


@application.route('/api/auth', methods=['POST'])  # complete, Test Complete
def authenticate_and_return_accessToken():
    "Authentication endpoint"
    logger.info('User Access Token Request')
    if not request.is_json:
        logger.info("Invalid Request in /api/auth. header content-type is: " + request.headers['content-type'])
        return make_message_response("Missing JSON request", 400) 
    requestJSON = json.loads(request.data)
    if 'username' not in requestJSON or 'password' not in requestJSON:
        return make_message_response("Missing username or password fields", 400)

    thisuser = User.loadUser(username=requestJSON['username'])
    if thisuser != NOUSER:
        if check_password_hash(thisuser.password, requestJSON['password']):
            # authentication OK!
            logger.info('Access token created for ' + requestJSON['username'])
            access_token = create_access_token(identity=thisuser)
            return make_json_response({'access_token': access_token}, 200)
        else:
            return make_message_response("Invalid Username or Password", 401)
    else:
        return make_message_response("User does not exist", 401)


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

    uclaims=get_jwt_claims()
    if uname != uclaims['username'] and uclaims['GlobalAdminStatus'] != 1:
        logger.warning('User : '+ uclaims['username']+ ' tried to remove '+ uname+ '. This Endpoint should not be generally known')
        return make_message_response("Can only remove self; or requires administrative priviliges. User " + str(uclaims['username']) + " trying to remove " + uname, 401)
    cur = mysql.connection.cursor()
    cur.execute("START TRANSACTION;")
    cur.execute('DELETE FROM t_Users WHERE c_ID_Users=' +
                str(get_jwt_identity()))
    cur.execute("COMMIT;")
    logger.warning('Removed User : '+uclaims['username']+' - Was this intended?')
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
    if get_jwt_identity()==None:
        return make_message_response('Optional Protection, you had no Token', 200)
    else:
        return make_message_response('Optional Protection, you had a token', 200)


@application.route('/api/dev/log', methods=['GET'])
@jwt_required
def logfile():
    if get_jwt_claims()['GlobalAdminStatus']==0:
        return jsonify(message="Illegal Non-Admin Operation")
    
    latest = request.args.get('latest')
    if lates == 'true':
        try:
            return send_file(active_logfile, attachment_filename='Mitfahrgelegenheit.log')
        except Exception as e:
            return jsonify(exception=str(e))
   

#///////////////////////////////////////////////////////////////////////////////////////////////////


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
    return make_json_response({"message": "General Server Error", "Event ID": str(sentry.event_id)}, 500)
#/////////////////////////////////////////////////////////////////////////////////////////////////
# Error 404 general handler

@application.errorhandler(404)
def resource_not_found_error(error):
    return make_message_response("Resource does not exist", 404)


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
    return make_message_response("User Claims Verification Failed - Probably an Illegal Token", 400)


@jwt.expired_token_loader
def expired_token_loader():
    return jsonify(message="Token Expired")


@jwt.needs_fresh_token_loader
def needs_fresh_token_loader():
    return make_message_response("Fresh Token required", 401)


@jwt.invalid_token_loader
def invalid_token_loader(msgstring):
    return make_message_response(msgstring, 401)


@jwt.revoked_token_loader
def revoked_token_loader():
    return make_message_response("Token has been revoked", 401)


@jwt.unauthorized_loader
def unauthorized_loader(msg):
    return make_json_response(msg, 401)
