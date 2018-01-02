# Moritz Basel - interne_serverTest.py
# Version 0.0.1

import json
import unittest
import os
import logging
from datetime import datetime

now = datetime.now()
hndlr = logging.FileHandler('./test_logs/Mitfahrgelegenheit_test-' + now.strftime("%d-%m-%y %H-%M-%S") + '.log')
hndlr.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'))
hndlr.setLevel(logging.DEBUG)
logging.getLogger(__name__).addHandler(hndlr)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

os.environ['MITFAHRGELEGENHEIT_SETTINGS'] = './Mitfahrgelegenheit.debug.conf'
os.environ['MITFAHRGELEGENHEIT_TEST'] = '1'
import Interne_server


class InterneServerTestCase(unittest.TestCase):
    "Defines the Test-Case Class for the 'Interne Mitfahrgelegenheit' Backend Flask Webservice"

    def setUp(self):
        
        self.application = Interne_server.application
        Interne_server.application.debug = False
        Interne_server.application.testing = True
        self.app = self.application.test_client()

        putData = {}
        putData['username'] = 'UnitTest'
        putData['email'] = 'testemail@test.test'
        putData['password'] = '1234'
        putData['phoneNumber'] = '093710000000'
        logger.info("Creating TestUser:")
        logger.info(json.dumps(putData))
        self.app.post('/api/users', data=json.dumps(putData),
                      headers={'content-type': 'application/json'})

        logger.info("Running Test method " + self._testMethodName)
        return
    
    def tearDown(self):

        token = self.login('UnitTest', '1234')
        if token == None:
            return

        self.app.delete('/api/dev/removeUser/UnitTest', data="", \
                        headers={'content-type': 'application/json', 'Authorization': token})
        return

    def login(self, username, password):
        reqData = {}
        reqData["username"] = username
        reqData["password"] = password

        responseLogin = self.app.post('/api/auth', data=json.dumps(reqData),
                                      headers={'content-type': 'application/json'}, follow_redirects=True)
        try:
            responseJSON = json.loads(responseLogin.data)
        except json.JSONDecodeError:
            logger.info(responseLogin)
            self.fail()

        if 'access_token' in responseJSON:
            return 'Bearer ' + responseJSON["access_token"]
        else:
            return None

    def validateResponse(self, response, status_code=200, keys = []):
        returnData = {}
        
        if response.status_code != status_code:
            return returnData, 1
        try:
            returnData = json.loads(response.data)
        except json.JSONDecodeError:
            return returnData, 1
        for key in keys:
            if key not in returnData:
                return returnData,1
        return returnData, 0
        




        
    def test_login(self):
        "Tests login of existing user monomo+monomomo"
        token = self.login('monomo', 'monomomo')
        self.assertFalse(token == None, msg="Login monomo+monomomo Failure")
        responseJSON = {}
        try:
            responseCheck = self.app.get(
                '/api/dev/check_token', data="{}", headers={'Authorization': token}, follow_redirects=True)
            responseJSON = json.loads(responseCheck.data)
        except Exception:
            logger.info(Exception)
            logger.info("On Get Request: /api/dev/check_token " +
                  "{Authorization : " + token + " | Data: " + "{}")
            logger.info("Returned: ")
            logger.info(responseCheck.data)
        self.assertTrue(responseJSON['username'] == 'monomo',
                        msg='Authorization Failure: monomo+monomomo')

        token = self.login('thisuserdoesnotexist', 'nope')
        self.assertTrue(
            token == None, msg="Login thisuserdoesnotexist+nope returned a Token")

        responseCheck = self.app.post(
            '/api/check-token', data="{}", headers={'content-type': 'application/json', 'Authorization': "Bearer wrong_token.bad_claims.illegal_signature"})
        self.assertFalse(responseCheck.status == 200,
                         msg="JWT Wrong Token returned HTTP 200 OK")

    def test_signup(self):
        "Tests Signup on /api/users/, login on the new account on /api/auth, checks the token, then deletes the new account on /api/dev/removeUser/<id>"

        putData = {}

        putData['username'] = 'temptest'
        putData['email'] = 'testemail@test.test'
        putData['password'] = '1234'
        putData['phoneNumber'] = '093710000000'

        rq = self.app.post('/api/users', data=json.dumps(putData),
                           headers={'content-type': 'application/json'})

        if rq.status_code != 409:  # 409 : User already exists; not an error
            try:
                self.assertTrue(rq.status_code == 201,
                                msg="User temptest+1234 could not be created;")
            except AssertionError:
                logger.info(rq.status_code)
                logger.info(rq.data)
                self.fail()

        token = self.login('temptest', '1234')
        self.assertFalse(
            token == None, msg="Login temptest+1234 Failure (test-based account)")

        responseCheck = self.app.get(
            '/api/dev/check_token', data="{}",
            headers={'content-type': 'application/json',
                     'Authorization': token},
            follow_redirects=False)
        self.assertTrue(len(responseCheck.data) > 0,
                        msg="/api/check_token returned no Data")

        try:
            responseJSON = json.loads(responseCheck.data)
        except json.JSONDecodeError:
            logger.info("/api/dev/check_token Data irregular. (No JSON)")
            logger.info("Data received was:")
            logger.info(str(responseCheck))
            self.assertTrue(False)
        self.assertTrue(responseJSON['username'] == 'temptest',
                        msg='Authorization Failure: temptest+1234')

        response = self.app.delete(
            '/api/dev/removeUser/temptest', headers={'Authorization': token})
        if response.status_code != 204:
            logger.info("/api/dev/removeUser/" + str(id) +
                  " did not return status 204. Message is: " + response.status)
            logger.info(response.data)
        self.assertTrue(response.status_code == 204)
        token = self.login('temptest', '1234')
        self.assertTrue(
            token == None, msg='Login temptest+1234 still successful after deleting User')

    def test_patchUser(self):
        token = self.login('UnitTest', '1234')
        if token == None:
            self.fail(msg = 'UnitTest Login Failure')
        
        getStr = self.app.get('/api/users/UnitTest', follow_redirects = True, headers = {'Authorization' : token})
        getData, err = self.validateResponse(getStr, keys = ['id'], status_code = 200)
        if err != 0:
            self.fail('Error on UPDATE /api/users/UnitTest')
        
        userid = getData['id']

        data = {'email' : 'newemail@test.com', 'password' : '12345'}
        logger.info('Patching User with ID ' + str(userid))
        updateData = self.app.put('/api/users/' + str(userid), data = json.dumps(data), 
                                    headers = {'content-type' : 'application/json', 'Authorization' : token})
        logger.info(updateData.data)

        token = self.login('UnitTest', '12345')
        if token == None:
            self.fail('UnitTest updated Login Failure')
        getStr = self.app.get('/api/users/UnitTest', follow_redirects = True, headers = {'Authorization' : token})
        getData, err = self.validateResponse(getStr, keys = ['email'], status_code = 200)
        if err != 0: 
            self.fail('Error on Updated GET /api/users/UnitTest')
        self.assertTrue(getData['email'] == 'newemail@test.com', 'UnitTest Email does not reflect updated value')

        data = {'password' : '1234' }
        logger.info('Patching UnitTest to restore PW to 1234')
        self.app.put('/api/users/' + str(userid), data = json.dumps(data), 
                                    headers = {'content-type' : 'application/json', 'Authorization' : token})
        token = self.login('UnitTest', '1234')
        if token == None:
            self.fail('After changing the UnitTest User Password from 1234 to 12345 and back, the second Login was a failure')



    def test_makeAndGetAppointment(self):
        token = self.login('UnitTest', '1234')
        if token == None:
            self.fail('UnitTest Login Failure')
        
        postData = {'startLocation' : 'Berlin', 'startTime' : 1614847559}

        resp = self.app.post('/api/appointments', 
                data = json.dumps(postData), headers = {'content-type' : 'application/json', 'Authorization' : token})
        self.assertEqual(resp.status_code, 201 , 'Appointment Creation returned ' +  str(resp.status_code))


if __name__ == '__main__':
    unittest.main()
