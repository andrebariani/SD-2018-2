import json
from bottle import request, route, run
from tinydb import TinyDB, Query
import requests
import sys

url = 'https://a8kojphqfk.execute-api.sa-east-1.amazonaws.com/default/CloudBroker'
headers = {'x-api-key': 'API-KEY-HERE'}
if (len(sys.argv) > 2):
    provider_key = sys.argv[2]
    db = TinyDB('db/' + provider_key + '.json')
else:
    print('Must provide a provider key!')
    provider_key = ''
    exit()

@route('/notify', method='POST')
def access_notification():
    params = json.loads(request.body.getvalue().decode('utf-8'))
    print(params)

@route('/access', method='POST')
def access_request():
    params = json.loads(request.body.getvalue().decode('utf-8'))
    r = requests.put(url, data={'type': 'access', 'key': provider_key}, headers=headers)
    return r.text


@route('/free', method='POST')
def free_request():
    params = json.loads(request.body.getvalue().decode('utf-8'))
    r = requests.put(url, data={'type': 'free', 'key': provider_key}, headers=headers)
    vm_requests.pop(params['access_key'])
    return r.text


run(host='localhost',port=sys.argv[1],debug=True)
