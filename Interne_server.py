# Moritz Basel - interne_server.py
from flask import Flask, request, send_from_directory, make_response, redirect, url_for
from flask_mysqldb import MySQL
from raven.contrib.flask import Sentry
from werkzeug import generate_password_hash, check_password_hash
from flask_jwt import JWT, jwt_required, current_identity
import json
import datetime
from werkzeug.security import safe_str_cmp

application = Flask(__name__)

#CLASS: USER
#///////////////////////////////////////////////////////////////////////////////////////////////////


class User(object):
    "The User class represents the User Object as well as the object relational mapping in the Database"

    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

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
            cur.execute("SELECT * FROM user where userID=" + str(uid) + ";")
            data = cur.fetchall()
            if len(data) > 0:
                if username != None:
                    if str(data[0][0] != username):
                        return NOUSER
                return User(int(data[0][4]), str(data[0][0]), str(data[0][2]))
                #              ID              Username       Hashed Password
            else:
                return NOUSER
        if username:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM user WHERE username='" +
                        username + "';")
            data = cur.fetchall()
            if len(data) > 0:
                return User(int(data[0][4]), str(data[0][0]), str(data[0][2]))
            else:
                return NOUSER


# Generic Return Code that is checked against indicating failure
NOUSER = User(id=0, username=None, password=None)


#///////////////////////////////////////////////////////////////////////////////////////////////////


# STATIC PART - SEE RESPECTIVE HTML FILES
#///////////////////////////////////////////////////////////////////////////////////////////////////


#///////////////////////////////////////////////////////////////////////////////////////////////////


# DYNAMIC PART - REST-API
#///////////////////////////////////////////////////////////////////////////////////////////////////
@application.route('/api/signup', methods=['POST'])
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

    if 'username' not in requestJSON or 'email' not in requestJSON or 'password' not in requestJSON:
        return make_message_response("Signup must contain (username, password, email) JSON keys", 400)

    # Check if User already exists
    testuser = User.loadUser(username=requestJSON['username'])
    if testuser != NOUSER:
        return make_message_response("User already exists", 409)

    # hash the password
    hashed_password = generate_password_hash(requestJSON['password'])
    cursor = mysql.connection.cursor()

    # OK CHECK for SQL Injection
    checkall = requestJSON['username'] + requestJSON['email']
    if 'DROP' in checkall or 'DELETE' in checkall or 'INSERT' in checkall or 'ALTER' in checkall or 'SELECT' in checkall:
        return make_message_response("Bad Term in Request Body", 404)

    # build the sql request
    sqlReq = "INSERT INTO user (`username`, `email`, `f_password`, `create_time`) "
    sqlReq = sqlReq + "VALUES ('" + requestJSON['username'] + "', '" + \
        requestJSON['email'] + "', '" + \
        hashed_password + "', CURRENT_TIMESTAMP);"

    # execute it
    cursor.execute("START TRANSACTION;")
    cursor.execute(sqlReq)
    cursor.execute("COMMIT;")

    # Respond 201 CREATED            MISSING HEADER LOCATION URI FOR USER PROFILE
    return make_message_response("User " + requestJSON['username'] + " created", 201)



@application.route('/api/check_token', methods=['GET'])
@jwt_required()
def check_token():
    retObj = {}
    retObj["Username"] = current_identity.username
    return make_json_response(retObj, 200)


@application.route('/api/appointments/<appointmentID>')
@jwt_required()
def appointment_data(appointmentID):
    #check if user has viewing priviliges or global administrative priviliges


    return make_message_response("Appointments not yet implemented", 500)




# DYNAMIC PART - REST-DEV-API
#///////////////////////////////////////////////////////////////////////////////////////////////////

@application.route('/api/dev/removeUser/<uname>', methods=['DELETE'])
@jwt_required()
def removeUser(uname):
    # check if you are the user in question ________TODO: check for administrative priviliges
    
    if uname != current_identity.username:
        return make_message_response("Can only remove self; or requires administrative priviliges. User " + str(current_identity.id) + " trying to remove " + str(UID), 401)
    cur = mysql.connection.cursor()
    cur.execute("START TRANSACTION;")
    cur.execute('DELETE FROM user WHERE userID=' + str(current_identity.id))
    cur.execute("COMMIT;")
    return make_response(("", 204, None))

@application.route('/api/dev/check-api')
def checkApi():
    return make_response("REST-API seems to work")


#///////////////////////////////////////////////////////////////////////////////////////////////////


# Helper Methods:
def authenticate(uname, pw):
    thisuser = User.loadUser(username=uname)
    if thisuser != NOUSER:
        if check_password_hash(thisuser.password, pw):
            return thisuser
        else:
            return None


def identity(payload):

    user_id = payload['identity']
    thisuser = User.loadUser(uid=user_id)
    if thisuser != NOUSER:
        return thisuser


def make_message_response(string, status):
    return make_json_response('{"message" : "' + string + '"}', status)


def make_json_response(jsonDictionary, status):
    try:
        return make_response(json.dumps(jsonDictionary), status, {'content-type': 'application/json'})
    except json.JSONDecodeError:
        return make_response('{"message" : "Internal Server Error: Some Method created invalid JSON Data"}', 500, {'content_type': 'application/json'})


application.config['SECRET_KEY'] = 'SECRET_KEY'
application.config['MYSQL_USER'] = 'flaskuser'
application.config['MYSQL_PASSWORD'] = 'software'
application.config['MYSQL_DB'] = 'interne_test'
application.config['MYSQL_HOST'] = 'localhost'
application.config['JWT_AUTH_URL_RULE']='/api/auth'

jwt = JWT(application, authenticate, identity)
mysql = MySQL(application)
sentry = Sentry(
    application, dsn='https://6ac6c6188eb6499fa2967475961a03ca:2f617eada90f478bb489cd4cf2c50663@sentry.io/232283')

if __name__ == "__main__":
    application.run(host='0.0.0.0')
