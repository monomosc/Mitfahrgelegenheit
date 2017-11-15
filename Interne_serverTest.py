# Moritz Basel - interne_serverTest


import json
import unittest


import Interne_server


class InterneServerTestCase(unittest.TestCase):
    "Defines the Test-Case Class for the 'Interne Mitfahrgelegenheit' Backend Flask Webservice"

    def setUp(self):
        self.app = Interne_server.application.test_client()
        self.app.testing = True
        
        putData = {}
        putData['username'] = 'UnitTest'
        putData['email'] = 'testemail@test.test'
        putData['password'] = '1234'
        putData['phoneNumber'] = '093710000000'
        putData['Organization'] = 'Test Organization'
        print("Creating TestUser:")
        print(json.dumps(putData))
        self.app.post('/apu/users', data=json.dumps(putData), headers={'content-type': 'application/json'})

        print("Running Test method" + self._testMethodName)
        return

    def tearDown(self):

        token = self.login('UnitTest', '1234')
        if token == None:
            return

        self.app.delete('/api/dev/removeUser/UnitTest', data="", headers={
                        'content-type': 'application/json', 'Authorization': "JWT " + token})
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
            print(responseLogin)
            self.fail()

        if 'access_token' in responseJSON:
            return responseJSON["access_token"]
        else:
            return None

    def test_login(self):
        "Tests login of existing user monomo+monomomo"
        token = self.login('monomo', 'monomomo')
        self.assertFalse(token == None, msg="Login monomo+monomomo Failure")
        responseJSON = {}
        try:
            responseCheck = self.app.get(
                '/api/dev/check_token', data="{}", headers={'Authorization': "JWT " + token}, follow_redirects=True)
            responseJSON = json.loads(responseCheck.data)
        except Exception:
            print(Exception)
            print("On Get Request: /api/dev/check_token " +
                  "{Authorization : JWT " + token + " | Data: " + "{}")
            print("Returned: ")
            print(responseCheck.data)
        self.assertTrue(responseJSON['Username'] == 'monomo',
                        msg='Authorization Failure: monomo+monomomo')

        token = self.login('thisuserdoesnotexist', 'nope')
        self.assertTrue(
            token == None, msg="Login thisuserdoesnotexist+nope returned a Token")

        responseCheck = self.app.post(
            '/api/check-token', data="{}", headers={'content-type': 'application/json', 'Authorization': "JWT wrong_token.bad_claims.illegal_signature"})
        self.assertFalse(responseCheck.status == 200,
                         msg="JWT Wrong Token returned HTTP 200 OK")

    def test_signup(self):
        "Tests Signup on /api/users/uname, login on the new account on /api/auth, checks the token, then deletes the new account on /api/dev/removeUser/<id>"

        putData = {}

        putData['username'] = 'temptest'
        putData['email'] = 'testemail@test.test'
        putData['password'] = '1234'
        putData['phoneNumber'] = '093710000000'
        putData['Organization'] = 'Test Organization'

        rq = self.app.post('/api/users', data=json.dumps(putData),
                           headers={'content-type': 'application/json'})

        if rq.status_code != 409:  # 409 : User already exists; not an error
            try:
                self.assertTrue(rq.status_code == 201,
                                msg="User temptest+1234 could not be created;")
            except AssertionError:
                print(rq.status_code)
                print(rq.data)
                self.fail()

        token = self.login('temptest', '1234')
        self.assertFalse(
            token == None, msg="Login temptest+1234 Failure (test-based account)")

        responseCheck = self.app.get(
            '/api/dev/check_token', data="{}", headers={'content-type': 'application/json', 'Authorization': "JWT " + token}, follow_redirects=False)
        self.assertTrue(len(responseCheck.data) > 0,
                        msg="/api/check_token returned no Data")

        try:
            responseJSON = json.loads(responseCheck.data)
        except json.JSONDecodeError:
            print("/api/dev/check_token Data irregular. (No JSON)")
            print("Data received was:")
            print(str(responseCheck))
            self.assertTrue(False)
        self.assertTrue(responseJSON['Username'] == 'temptest',
                        msg='Authorization Failure: temptest+1234')

        response = self.app.delete(
            '/api/dev/removeUser/temptest', headers={'Authorization': "JWT " + token})
        if response.status_code != 204:
            print("/api/dev/removeUser/" + str(id) +
                  " did not return status 204. Message is: " + response.status)
            print(response.data)
        self.assertTrue(response.status_code == 204)
        token = self.login('temptest', '1234')
        self.assertTrue(
            token == None, msg='Login temptest+1234 still successful after deleting User')


if __name__ == '__main__':
    unittest.main()
