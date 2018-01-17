# -*- coding: utf-8 -*- 
import configparser
import requests
with open("Version.conf") as f:
    conf = configparser.RawConfigParser(allow_no_value=True)
    conf.read_file(f)
import json

print(conf.get('VERSION', 'version'))

postData = {
    'version' : conf.get('VERSION', 'version'),
    'url' : 'https://monomo.solutions/api',
    'projects' : ['softwarepraktikum/Mitfahrgelegenheit']

}
r = requests.post('https://sentry.monomo.solutions/api/hooks/release/builtin/2/d8be77d2398a1f8ddb4bcc3bb5be7969a13965408cd469b848579b2186b57271/',
                headers = {'content-type' : 'application/json'},
                data = json.dumps(postData))
if r.status_code != 201:
    raise Exception('Not Created new Release')