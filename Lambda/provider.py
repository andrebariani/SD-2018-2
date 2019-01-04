import json
from bottle import request, route, run
import requests
import sys

url = 'https://a8kojphqfk.execute-api.sa-east-1.amazonaws.com/default/CloudBroker'
headers = {'x-api-key': 'API-KEY-HERE'}
if (len(argv) > 2):
    provider_key = sys.argv[2]
else:
    provider_key = ''

@route('/notify', method='POST')
def access_notification():
    params = json.loads(request.body.getvalue().decode('utf-8'))

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
