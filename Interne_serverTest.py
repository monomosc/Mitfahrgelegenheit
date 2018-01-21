# Moritz Basel - interne_serverTest.py
# Version 0.1.0

import json
import unittest
import os
import logging
from datetime import datetime

now = datetime.now()
hndlr = logging.FileHandler(
    './test_logs/Mitfahrgelegenheit_test-' + now.strftime("%d-%m-%y %H-%M-%S") + '.log')
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

        self.app.delete('/api/dev/removeUser/UnitTest', data="",
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

    def validateResponse(self, response, status_code=200, keys=[]):
        returnData = {}

        if response.status_code != status_code:
            return returnData, 1
        try:
            returnData = json.loads(response.data)
        except json.JSONDecodeError:
            return returnData, 1
        for key in keys:
            if key not in returnData:
                return returnData, 1
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
        "Tests whether an existing user can be changed"
        token = self.login('UnitTest', '1234')
        if token == None:
            self.fail(msg='UnitTest Login Failure')

        getStr = self.app.get(
            '/api/users/UnitTest', follow_redirects=True, headers={'Authorization': token})
        getData, err = self.validateResponse(
            getStr, keys=['id'], status_code=200)
        if err != 0:
            self.fail('Error on UPDATE /api/users/UnitTest')

        userid = getData['id']

        data = {'email': 'newemail@test.com', 'password': '12345'}
        logger.info('Patching User with ID ' + str(userid))
        updateData = self.app.put('/api/users/' + str(userid), data=json.dumps(data),
                                  headers={'content-type': 'application/json', 'Authorization': token})
        logger.info(updateData.data)

        token = self.login('UnitTest', '12345')
        if token == None:
            self.fail('UnitTest updated Login Failure')
        getStr = self.app.get(
            '/api/users/' + str(userid), follow_redirects=True, headers={'Authorization': token})
        getData, err = self.validateResponse(
            getStr, keys=['email'], status_code=200)
        if err != 0:
            self.fail('Error on Updated GET /api/users/UnitTest')
        self.assertTrue(getData['email'] == 'newemail@test.com',
                        'UnitTest Email does not reflect updated value')

        data = {'password': '1234'}
        logger.info('Patching UnitTest to restore PW to 1234')
        self.app.put('/api/users/' + str(userid), data=json.dumps(data),
                     headers={'content-type': 'application/json', 'Authorization': token})
        token = self.login('UnitTest', '1234')
        if token == None:
            self.fail(
                'After changing the UnitTest User Password from 1234 to 12345 and back, the second Login was a failure')

    def test_makeAndGetAppointment(self):
        "Tests Creaton and Deleteion of an Appointment as normal User"
        token = self.login('UnitTest', '1234')
        if token == None:
            self.fail('UnitTest Login Failure')

        # create an appointment
        postData = {'startLocation': 'Wuerzburg',
                    'startTime': 1614847559, 'distance': 100,
                    'targetLocation' : 'Berlin'}
        resp = self.app.post('/api/appointments',
                             data=json.dumps(postData), headers={'content-type': 'application/json', 'Authorization': token})
        self.assertEqual(resp.status_code, 201,
                         'Appointment Creation returned ' + str(resp.status_code))
        respJSON = json.loads(resp.data)
        appID = respJSON['id']

        resp = self.app.get('/api/appointments/' + str(appID),
                            headers={'content-type': 'application/json', 'Authorization': token})
        self.assertEqual(resp.status_code, 200,
                         'Appointment apprently does not exist: 200 expected, returned ' + str(resp.status_code))
        respJSON = json.loads(resp.data)
        self.assertEqual(respJSON['startLocation'], 'Wuerzburg',
                         'Newly created appointment has a different startLocation! Expected Wuerzburg but got: ' + respJSON['startLocation'])

        # delete the appointment
        resp = self.app.delete('/api/appointments/' + str(appID), data='',
                               headers={'content-type': 'application/json', 'Authorization': token})
        self.assertEqual(resp.status_code, 204,
                         'Appointment Deleteion returned ' + str(resp.status_code))

        # check if appointment still exists anyway:
        resp = self.app.get('/api/appointments/' + str(appID),
                            headers={'content-type': 'application/json', 'Authorization': token})
        self.assertEqual(resp.status_code, 404,
                         'Appointment apprently still exists: 404 expected, returned ' + str(resp.status_code))

    def test_addUserToAppointment(self):
        "Tests Adding a User to an Appointment"
        token = self.login('UnitTest', '1234')
        self.assertIsNotNone(token, 'UnitTest Login Failure')
        authHeader = {'content-type' : 'application/json',
                      'Authorization' : token}

        # Get UID
        resp = self.app.get('/api/users/UnitTest',
                            headers=authHeader, follow_redirects=True)
        respJSON, err = self.validateResponse(resp, 200, ['id'])
        self.assertEqual(err, 0, 'response was: ' + str(resp.data))
        uID = int(respJSON['id'])

        # create Appointment
        postData = {'startLocation': 'Berlin',
                    'startTime': 1614847559, 'distance': 100,
                    'targetLocation' : 'Berlin'}  # future
        resp = self.app.post('/api/appointments',
                             data=json.dumps(postData), headers=authHeader)
        respJSON, err = self.validateResponse(resp, 201, ['id'])
        self.assertEqual(err, 0)
        appID = int(respJSON['id'])

        # add UnitTest to Appointment
        putData = {'drivingLevel': 2, 'maximumPassengers': 4}
        resp = self.app.put('/api/appointments/' + str(appID) + '/users/' + str(uID),
                            data=json.dumps(putData), headers=authHeader)
        abc, err = self.validateResponse(resp, 200, [])
        self.assertEqual(err, 0)

        # check appointment data
        resp = self.app.get('/api/appointments/' +
                            str(appID) + '/users', headers=authHeader)
        self.assertEqual(resp.status_code, 200)
        respJSON = json.loads(resp.data)
        self.assertGreaterEqual(len(respJSON), 1)
        firstEntry = respJSON[0]

        self.assertTrue('id' in firstEntry)
        self.assertTrue('drivingLevel' in firstEntry)

        self.assertEqual(2, firstEntry['drivingLevel'])
        self.assertEqual('UnitTest', firstEntry['username'])

    def test_jobForAppointments(self):
        "Tests the existence of a notifying job for an appointment; does not test the correct execution of that job"
        token = self.login('UnitTest', '1234')
        self.assertIsNotNone(token, 'UnitTest Login Failure')
        authHeader = {'content-type': 'application/json',
                      'Authorization': token}

        # Get UID
        resp = self.app.get('/api/users/UnitTest',
                            headers=authHeader, follow_redirects=True)
        respJSON, err = self.validateResponse(resp, 200, ['id'])
        self.assertEqual(err, 0)
        uID = int(respJSON['id'])

        # create Appointment
        postData = {'startLocation': 'Berlin',
                    'startTime': 1614847559, 'distance': 100,
                    'targetLocation' : 'Berlin'}  # future
        resp = self.app.post('/api/appointments',
                             data=json.dumps(postData), headers=authHeader)
        respJSON, err = self.validateResponse(resp, 201, ['id'])
        self.assertEqual(err, 0)
        appID = int(respJSON['id'])

        # add UnitTest to Appointment
        putData = {'drivingLevel': 2, 'maximumPassengers': 4}
        resp = self.app.put('/api/appointments/' + str(appID) + '/users/' + str(uID),
                            data=json.dumps(putData), headers=authHeader)
        abc, err = self.validateResponse(resp, 200, [])
        self.assertEqual(err, 0)

        # check the job exists
        # Job checking is an admin operation
        token = self.login('monomo', 'monomomo')
        authHeader = {'content-type': 'application/json',
                      'Authorization': token}
        resp = self.app.get('/api/dev/jobs', headers=authHeader)
        respJSON = json.loads(resp.data)
        self.assertTrue(('Appointment Notify Job ' + str(appID))
                        in respJSON, 'Appointment notify job not in Serverside jobs')

        # remove appointment - this will remove the corresponding scheduler job
        self.app.delete('/api/appointments/' + str(appID), headers=authHeader)

        # check the job now doesn't exist
        resp = self.app.get('/api/dev/jobs', headers=authHeader)
        respJSON = json.loads(resp.data)
        self.assertFalse(('Appointment Notify Job ' + str(appID))
                         in respJSON, 'Appointment notify job still in Serverside jobs')


    def test_distributePassengersToDefiniteDrivers(self):
        "Tests a creation of Appointment, adds a few users as drivers, and checks if everything works as intended"

        token = self.login('UnitTest', '1234')
        authHeader = {'content-type' : 'application/json', 'Authorization' : token}

        adminToken = self.login('monomo', 'monomomo')
        adminHeader = {'content-type' : 'application/json', 'Authorization' : adminToken}

        #create Appointment
        postData = {'startLocation': 'Berlin',
                    'startTime': 1614847559, 'distance': 100,
                    'targetLocation' : 'Berlin'}  # future
        resp = self.app.post('/api/appointments',
                             data=json.dumps(postData), headers=authHeader)
        respJSON, err = self.validateResponse(resp, 201, ['id'])
        self.assertEqual(err, 0)
        appID = int(respJSON['id'])

        # Get UnitTest UID
        resp = self.app.get('/api/users/UnitTest',
                            headers=authHeader, follow_redirects=True)
        respJSON, err = self.validateResponse(resp, 200, ['id'])
        self.assertEqual(err, 0)
        uID = int(respJSON['id'])



        #add UnitTest as driver
        putData = {'drivingLevel': 1, 'maximumPassengers' : 5}
        resp = self.app.put('/api/appointments/' + str(appID) + '/users/' + str(uID),
                            data=json.dumps(putData), headers=authHeader)
        

        #create a bunch of users and add them to our appointment
        for i in range(1,4):
            #create User
            putData = { 'username' : 'User' + str(i),
                        'password' : '1234',
                        'email' : 'mo@mo',
                        'phoneNumber' : '1234'}
            resp = self.app.post('/api/users', data = json.dumps(putData), headers = {'content-type' : 'application/json'})
            self.assertTrue(resp.status_code == 201 or resp.status_code == 409) # 409 if user already exists
            respJSON = json.loads(resp.data)
            try:
                uID = respJSON['id']
            except:
                logger.info(str(respJSON))
                self.fail('Check logs - some response KeyError')


            putData = {'drivingLevel': 0}
            resp = self.app.put('/api/appointments/' + str(appID) + '/users/' + str(uID),
                            data=json.dumps(putData), headers=adminHeader)
            respJSON = json.loads(resp.data)
            if resp.status_code != 200:
                logger.error('message: ' + respJSON['message'])
                self.fail('Could not add User to Appointment')
            
        
        #execute the distribution code!!
        Interne_server.terminateAppointment(appID)
        #Hopefully nothing went wrong

        #delete a bunch of users and then delete the appointmetn:
        for  i in range(1,4):
            token = self.login('User' + str(i), '1234')
            resp = self.app.delete('/api/dev/removeUser/User' + str(i), headers={'Authorization': token})
            self.assertEquals(resp.status_code, 204)
        
        resp = self.app.delete('/api/appointments/' + str(appID), headers=authHeader)
        self.assertEquals(resp.status_code, 204)
        


        def test_totalDistance(self):
            token = self.login('UnitTest', '1234')
            
            #create Appointment
        postData = {'startLocation': 'Berlin',
                    'startTime': 1614847559, 'distance': 100,
                    'targetLocation' : 'Berlin'}  # future
        resp = self.app.post('/api/appointments',
                             data=json.dumps(postData), headers=authHeader)
        respJSON, err = self.validateResponse(resp, 201, ['id'])
        self.assertEqual(err, 0)
        appID = int(respJSON['id'])

        # Get UnitTest UID
        resp = self.app.get('/api/users/UnitTest',
                            headers=authHeader, follow_redirects=True)
        respJSON, err = self.validateResponse(resp, 200, ['id'])
        self.assertEqual(err, 0)
        uID = int(respJSON['id'])

        #add UnitTest as driver
        putData = {'drivingLevel': 1, 'maximumPassengers' : 5}
        resp = self.app.put('/api/appointments/' + str(appID) + '/users/' + str(uID),
                            data=json.dumps(putData), headers=authHeader)
        
        #execute the distribution code
        Interne_server.terminateAppointment(appID)

        #retire the appointment with UnitTest as only driver
        Interne_server.retireAppointment(appID, [uID])
        #Hopefully nothing went wront!

        distance = Interne_server.getUserTotalDistance(uID)

        self.assertEqual(distance, 100)
        #delete the appointment again
        resp = self.app.delete('/api/appointments/' + str(appID), headers=authHeader)
        self.assertEqual(resp.status_code, 204)



    def test_correctDrivingDistributionWithDefiniteDrivers(self):
        """
        Tests whether the driving distribution of an appointment is managed correctly
        This will only test the configuration where DefiniteDrivers pass
        """

        token = self.login('UnitTest', '1234')
        authHeader = {'content-type' : 'application/json', 'Authorizaion' : token}
        adminToken = self.login('monomo', 'monomomo')
        adminHeader =  authHeader
        adminHeader['Authorization'] = adminToken

        #get monomo UID
        resp = self.app.get('/api/users/monomo',
                                 headers = adminHeader, follow_redirects=True)
        respJSON, err = self.validateResponse(resp, 200, ['id'])
        self.assertEqual(err,0)
        monomoID = int(respJSON['id'])
        logger.info('monomo ID: ' + str(monomoID))

        #get UnitTest UID:
        resp = self.app.get('/api/users/UnitTest',
                            headers=authHeader, follow_redirects=True)
        respJSON, err = self.validateResponse(resp, 200, ['id'])
        self.assertEqual(err, 0)
        unittestID = int(respJSON['id'])
        logger.info('UnitTest ID: ' + str(unittestID))

        # create Appointment
        postData = {'startLocation': 'Berlin',
                    'startTime': 1614847559, 'distance': 100,
                    'targetLocation' : 'Berlin'}  # future
        resp = self.app.post('/api/appointments',
                             data=json.dumps(postData), headers=authHeader)
        respJSON, err = self.validateResponse(resp, 201, ['id'])
        self.assertEqual(err, 0)
        appID = int(respJSON['id'])
        
        #add UnitTest as driver
        putData = {'drivingLevel': 1, 'maximumPassengers' : 5}
        resp = self.app.put('/api/appointments/' + str(appID) + '/users/' + str(unittestID),
                            data=json.dumps(putData), headers=authHeader)

        self.assertEqual(resp.status_code, 200)
        #add monomo as driver
        resp = self.app.put('/api/appointments/' + str(appID) + '/users/' + str(monomoID),
                                    data = json.dumps(putData), headers = adminHeader)       
        self.assertEqual(resp.status_code, 200)
        for i in range(1,4):
            #create User
            putData = { 'username' : 'User' + str(i),
                        'password' : '1234',
                        'email' : 'mo@mo',
                        'phoneNumber' : '1234'}
            resp = self.app.post('/api/users', data = json.dumps(putData), headers = {'content-type' : 'application/json'})
            self.assertTrue(resp.status_code == 201 or resp.status_code == 409) # 409 if user already exists
            respJSON = json.loads(resp.data)
            try:
                uID = respJSON['id']
            except:
                logger.info(str(respJSON))
                self.fail('Check logs - some response KeyError')

            #add new user to appointment
            putData = {'drivingLevel': 0}
            resp = self.app.put('/api/appointments/' + str(appID) + '/users/' + str(uID),
                            data=json.dumps(putData), headers=adminHeader)
            respJSON = json.loads(resp.data)
            if resp.status_code != 200:
                logger.error('message: ' + respJSON['message'])
                self.fail('Could not add User to Appointment')

        
        #execute the distribution code
        Interne_server.terminateAppointment(appID)


        resp = self.app.get('/api/appointments/' + str(appID) + '/drivingDistribution',
                                headers = authHeader)
        
        respJSON, err = self.validateResponse(resp, 200, [str(monomoID), str(unittestID)])
        if err != 0:
            logger.error('Driving Distribution Response Content:')
            logger.error(resp.data)
            logger.error('Expect monomo (#' + str(monomoID) + ') and UnitTest (#' + str(unittestID) + ') as drivers.')
            for driverID in respJSON:
                logger.error('Found #' +str(driverID))
            self.fail('Driving Distribution Error!')
            
        #retire the appointment with UnitTest as only driver
        Interne_server.retireAppointment(appID, [uID])
        #Hopefully nothing went wront!


        
        
        #delete a bunch of users and then delete the appointmetn:
        for  i in range(1,4):
            token = self.login('User' + str(i), '1234')
            resp = self.app.delete('/api/dev/removeUser/User' + str(i), headers={'Authorization': token})
            self.assertEquals(resp.status_code, 204)
        
        resp = self.app.delete('/api/appointments/' + str(appID), headers=authHeader)
        self.assertEquals(resp.status_code, 204)


    def test_maxDefiniteDriverConfiguration(self):
        token = self.login('UnitTest', '1234')
        adminToken = self.login('monomo','monomomo')
        authHeader = {'content-type' : 'application/json', 'Authorization' : token}
        adminHeader = authHeader
        adminHeader['Authorization'] = adminToken

        #get user id's

        #get monomo UID
        resp = self.app.get('/api/users/monomo',
                                 headers = adminHeader, follow_redirects=True)
        respJSON, err = self.validateResponse(resp, 200, ['id'])
        self.assertEqual(err,0)
        monomoID = int(respJSON['id'])
        logger.info('monomo ID: ' + str(monomoID))

        #get UnitTest UID:
        resp = self.app.get('/api/users/UnitTest',
                            headers=authHeader, follow_redirects=True)
        respJSON, err = self.validateResponse(resp, 200, ['id'])
        self.assertEqual(err, 0)
        unittestID = int(respJSON['id'])
        logger.info('UnitTest ID: ' + str(unittestID))

        # create Appointment
        postData = {'startLocation': 'Berlin',
                    'startTime': 1614847559, 'distance': 100,
                    'targetLocation' : 'Berlin'}  # future
        resp = self.app.post('/api/appointments',
                             data=json.dumps(postData), headers=authHeader)
        respJSON, err = self.validateResponse(resp, 201, ['id'])
        self.assertEqual(err, 0)
        appID = int(respJSON['id'])


        #add drivers - total Slots: 4
        #add UnitTest as driver
        putData = {'drivingLevel': 1, 'maximumPassengers' : 2}
        resp = self.app.put('/api/appointments/' + str(appID) + '/users/' + str(unittestID),
                            data=json.dumps(putData), headers=authHeader)

        self.assertEqual(resp.status_code, 200)
        #add monomo as driver
        resp = self.app.put('/api/appointments/' + str(appID) + '/users/' + str(monomoID),
                                    data = json.dumps(putData), headers = adminHeader)       
        self.assertEqual(resp.status_code, 200)

        #create 2 more Users
        for i in range(1,3):
            #create User
            putData = { 'username' : 'User' + str(i),
                        'password' : '1234',
                        'email' : 'mo@mo',
                        'phoneNumber' : '1234'}
            resp = self.app.post('/api/users', data = json.dumps(putData), headers = {'content-type' : 'application/json'})
            self.assertTrue(resp.status_code == 201 or resp.status_code == 409) # 409 if user already exists
            respJSON = json.loads(resp.data)
            try:
                uID = respJSON['id']
            except:
                logger.info(str(respJSON))
                self.fail('Check logs - some response KeyError')

            #add new user to appointment
            putData = {'drivingLevel': 0}
            resp = self.app.put('/api/appointments/' + str(appID) + '/users/' + str(uID),
                            data=json.dumps(putData), headers=adminHeader)
            respJSON = json.loads(resp.data)
            if resp.status_code != 200:
                logger.error('message: ' + respJSON['message'])
                self.fail('Could not add User to Appointment')



        Interne_server.terminateAppointment(appID)
        resp = self.app.get('/api/appointments/' + str(appID) + '/drivingDistribution',
                                headers = authHeader)
        
        respJSON, err = self.validateResponse(resp, 200, [str(monomoID), str(unittestID)])
        if err !=0:
            logger.error(resp.data)
            self.fail('Terminate Appointment Error')
        
        self.assertTrue(len(respJSON[str(monomoID)]) == 2)
        self.assertTrue(len(respJSON[str(unittestID)]) == 2)
        
        



        #delete a bunch of users and then delete the appointmetn:
        for  i in range(1,3):
            token = self.login('User' + str(i), '1234')
            resp = self.app.delete('/api/dev/removeUser/User' + str(i), headers={'Authorization': token})
            self.assertEquals(resp.status_code, 204)
        
        resp = self.app.delete('/api/appointments/' + str(appID), headers=authHeader)
        self.assertEquals(resp.status_code, 204)


    def test_TooManyPassengersConfiguration(self):
        token = self.login('UnitTest', '1234')
        authHeader = {'content-type' : 'application/json', 'Authorizaion' : token}
        adminToken = self.login('monomo', 'monomomo')
        adminHeader =  authHeader
        adminHeader['Authorization'] = adminToken

        #get monomo UID
        resp = self.app.get('/api/users/monomo',
                                 headers = adminHeader, follow_redirects=True)
        respJSON, err = self.validateResponse(resp, 200, ['id'])
        self.assertEqual(err,0)
        monomoID = int(respJSON['id'])
        logger.info('monomo ID: ' + str(monomoID))

        #get UnitTest UID:
        resp = self.app.get('/api/users/UnitTest',
                            headers=authHeader, follow_redirects=True)
        respJSON, err = self.validateResponse(resp, 200, ['id'])
        self.assertEqual(err, 0)
        unittestID = int(respJSON['id'])
        logger.info('UnitTest ID: ' + str(unittestID))

        # create Appointment
        postData = {'startLocation': 'Berlin',
                    'startTime': 1614847559, 'distance': 100,
                    'targetLocation' : 'Berlin'}  # future
        resp = self.app.post('/api/appointments',
                             data=json.dumps(postData), headers=authHeader)
        respJSON, err = self.validateResponse(resp, 201, ['id'])
        self.assertEqual(err, 0)
        appID = int(respJSON['id'])
        
        #add UnitTest as driver with only one slot
        putData = {'drivingLevel': 1, 'maximumPassengers' : 1}
        resp = self.app.put('/api/appointments/' + str(appID) + '/users/' + str(unittestID),
                            data=json.dumps(putData), headers=authHeader)
        self.assertEqual(resp.status_code, 200)

        #add monomo as Passenger
        putData = {'drivingLevel' : 0}
        resp = self.app.put('/api/appointments/' + str(appID) + '/users/' + str(monomoID),
                            data=json.dumps(putData), headers=authHeader)
        self.assertEqual(resp.status_code, 200)

        Interne_server.terminateAppointment(appID)

        resp = self.app.get('/api/appointments/' + str(appID), headers = authHeader)
        respJSON, err = self.validateResponse(resp, 200, ['id', 'status'])
        if err != 0:
            logger.error(resp.data)
            self.fail()

        self.assertEqual(respJSON['status'], 'APPOINTMENT_LOCKED_NO_FIT')

        resp = self.app.delete('/api/appointments/' + str(appID), headers=authHeader)
       
        self.assertEquals(resp.status_code, 204)

if __name__ == '__main__':
    unittest.main()
