# Moritz Basel - interne_server.py
from flask import Flask, request, send_from_directory, make_response, redirect, jsonify
from flask_mysqldb import MySQL
from raven.contrib.flask import Sentry
from werkzeug import generate_password_hash, check_password_hash
import json
import datetime
from werkzeug.security import safe_str_cmp
from flask_jwt_extended import (JWTManager, jwt_required, create_access_token, get_jwt_identity, get_jwt_claims)

application = Flask(__name__)
jwt = JWTManager(application)
mysql = MySQL(application)
#CLASS: USER
#///////////////////////////////////////////////////////////////////////////////////////////////////


class User(object):
    "The User class represents the User Object as well as the object relational mapping in the Database"
    #Fields:
    #id                     //The MySQL autoincreasing ID
    #username               //Username
    #password               //Hashed Password
    #email                  //Email Address
    #phoneNumber            //Phone Number
    #globalAdminStatus      //Global Admin Status, currently 0 or 1

    def __init__(self, id, username, password, email, phoneNumber, globalAdminStatus):
        self.id = id
        self.username = username
        self.password = password
        self.email = email
        self.phoneNumber=phoneNumber
        self.globalAdminStatus=globalAdminStatus
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
            cur.execute("SELECT * FROM t_Users WHERE c_ID_Users='" + str(uid) + "';")
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
            cur.execute("SELECT * FROM t_Users WHERE c_name_Users= '"+username + "';")
            data = cur.fetchall()
            if len(data) > 0:
                return User(int(data[0][5]), str(data[0][0]), str(data[0][4]), str(data[0][2]), str(data[0][3]), int(data[0][1]))
                #              ID              Username       Hashed Password       Email           Phone Number    Global Admin Status
            else:
                return NOUSER


# Generic Return Code that is checked against indicating failure
NOUSER = User(id=0, username=None, password=None, email=None, phoneNumber=None, globalAdminStatus=None)




# DYNAMIC PART - REST-API
#///////////////////////////////////////////////////////////////////////////////////////////////////
@application.route('/api/users', methods=['POST'])
def signup():
    "The Endpoint URI for signing up. Takes email, username and password JSON returns 201 on success"

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
        return make_message_response("Unknown Server Error, The Sentry Error Code is: "+g.sentry_event_id, 500)
    
    # hash the password
    hashed_password = generate_password_hash(requestJSON['password'])
    

    # OK CHECK for SQL Injection
    checkall = requestJSON['username'] + requestJSON['email']
    if 'DROP' in checkall or 'DELETE' in checkall or 'INSERT' in checkall or 'ALTER' in checkall or 'SELECT' in checkall:
        return make_message_response("Bad Term in Request Body", 404)

    # build the sql request
    sqlReq = "INSERT INTO t_Users (`c_nameUsers`, `c_globalAdmin_Users`, `c_email_Users`, `c_phoneNumber_Users`, `c_passwordHash_Users`) "
    sqlReq = sqlReq + "VALUES ('" + requestJSON['username'] + "', '0', '" + \
        requestJSON['email'] + "', '" + requestJSON['phoneNumber'] + "', '" +\
        hashed_password + "');"
    
    # execute it
    cursor = mysql.connection.cursor()
    cursor.execute("START TRANSACTION;")
    cursor.execute(sqlReq)
    cursor.execute("COMMIT;")

    # Respond 201 CREATED            MISSING HEADER LOCATION URI FOR USER PROFILE
    return make_response("User " + uname + " created", 201,  {'content-type': 'application/json', 'Location' : ['/api/auth', '/api/users/'+requestJSON['username']]})



@application.route('/api/users/<UidOrName>', methods=['GET'])   #TODO add auth checking and user profile
def user_profileByID(UidOrName):
    "User Profile Endpoint"
    id=0
    try:
        id=int(UidOrName)
    except (TypeError, ValueError):
        thisuser=User.loadUser(username=UidOrName)
        if thisuser==NOUSER:
            return make_message_response("User not found", 404)
        return redirect('/api/users/'+thisuser.username)
    #check for authorization: Only a global Admin or the User itself can access this resource





    return make_message_response("Not yet implemented", 500)



@application.route('/api/appointments/<appointmentID>')
@jwt_required
def appointment_data(appointmentID):
    #check if user has viewing priviliges or global administrative priviliges


    return make_message_response("Appointments not yet implemented", 500)

@application.route('/api/auth', methods=['POST'])
def authenticate_and_return_accessToken():
    "Authentication endpoint"
    if not request.is_json:
        return make_message_response("Missing JSON request", 400)
    requestJSON=json.loads(request.data)
    if 'username' not in requestJSON or 'password' not in requestJSON:
        return make_message_response("Missing username or password fields", 400)
    
    thisuser=User.loadUser(username=requestJSON['username'])
    if thisuser!=NOUSER:
        if check_password_hash(thisuser.password, requestJSON['password']):
            #authentication OK!
            access_token=create_access_token(identity=thisuser)
            return make_json_response({'access_token' : access_token}, 200)
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
    retObj=get_jwt_claims().copy()
    retObj['id']=get_jwt_identity()
    return make_json_response(retObj, 200)


@application.route('/api/dev/removeUser/<uname>', methods=['DELETE'])
@jwt_required
def removeUser(uname):
    # check if you are the user in question ________TODO: check for administrative priviliges
    
    if uname != get_jwt_claims['username'] and get_jwt_claims['GlobalAdminStatus']!=1:
        return make_message_response("Can only remove self; or requires administrative priviliges. User " + str(get_jwt_claims['username']) + " trying to remove " + uname, 401)
    cur = mysql.connection.cursor()
    cur.execute("START TRANSACTION;")
    cur.execute('DELETE FROM t_Users WHERE c_ID_Users=' + str(get_jwt_identity()))
    cur.execute("COMMIT;")
    return make_response(("", 204, None))

@application.route('/api/dev/check-api')
def checkApi():
    return make_response("REST-API seems to work")


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
    return make_json_response({"message" : "General Server Error", "Event ID" : str(sentry.event_id)}, 500)





#//////////////////////////////////////////////////////////////////////////////////////////////////
# JWT CALLBACK FUNCTIONS:

@jwt.user_claims_loader
def add_claims_to_access_token(user):
    "Defines all fields to be remembered and recovered in the JSON Token"
    return {'Username' : user.username,
            'Email'    : user.email,
            'PhoneNumber' : user.phoneNumber,
            'GlobalAdminStatus' : user.globalAdminStatus}
    
@jwt.user_identity_loader
def user_identity_lookup(user):
    "UID for a Token Identity"
    return user.id

@jwt.claims_verification_failed_loader
def claims_verification_failed_loader():
    return make_message_response("User Claims Verification Failed - Probably an Illegal Token", 400)

@jwt.expired_token_loader
def expired_token_loader(msgstring):
    return make_message_response(msgstring, 401)

@jwt.needs_fresh_token_loader
def needs_fresh_token_loader():
    return make_message_response("Fresh Token required", 401)

@jwt.invalid_token_loader
def invalid_token_loader(msgstring):
    return make_message_response(msgstring, 401)

@jwt.revoked_token_loader
def revoked_token_loader():
    return make_message_response("Token has been revoked")

@jwt.unauthorized_loader
def unauthorized_loader(msgstring):
    return make_message_response(msgstring, 401)


application.config['MYSQL_USER'] = 'flaskuser'
application.config['MYSQL_PASSWORD'] = 'Test1234'
application.config['MYSQL_DB'] = 'Interne_Mitfahrgelegenheit'
application.config['MYSQL_HOST'] = '127.0.0.1'
application.config['JWT_SECRET_KEY']= 'SomethingSomethingSecretSecret'






if __name__ == "__main__":
    sentry = Sentry(
    application, dsn='https://6ac6c6188eb6499fa2967475961a03ca:2f617eada90f478bb489cd4cf2c50663@sentry.io/232283')
    application.run(host='0.0.0.0')
