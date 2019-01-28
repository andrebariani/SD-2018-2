import json
from bottle import request, route, run
from tinydb import TinyDB, Query
import requests
import sys

Access_Request = Query()
url = 'https://a8kojphqfk.execute-api.sa-east-1.amazonaws.com/default/CloudBroker'
headers = {'x-api-key': 'API-KEY-HERE'}

if (len(sys.argv) > 2):
    provider_key = sys.argv[2]
    db = TinyDB('db/' + provider_key + '.json', sort_keys=True, indent=4, separators=(',', ': '))
    requests_table = db.table('requests')
    resources_table = db.table('resources')
else:
    print('Must provide a provider key!')
    provider_key = ''
    exit()

@route('/notify', method='POST')
def access_notification():
    params = json.loads(request.body.getvalue().decode('utf-8'))
    print('NOTIFICATION RECEIVED:')
    print(params)
    db.insert(params)

@route('/access', method='POST')
def access_request():
    params = json.loads(request.body.getvalue().decode('utf-8'))
    changelog = []
    #r = requests.put(url, data={'type': 'access', 'key': provider_key}, headers=headers)
    req = requests_table.search(Access_Request.access_key == params['access_key'])
    if len(req) == 0:
        return 'Wrong access_key!'
    req_resources = req['resources'].sort(key=lambda x: x['id'])
    db_resources = resources_table.search(Access_Request.resources.any([x['id'] for x in req_resources])).sort(key=lambda x: x['id'])
    
    new_resources = [{'id': x['id'], 'amount': x['amount'] - y['amount']} for x, y in zip(req_resources, db_resources)]
    if any(i['amount'] < 0 for i in new_amounts):
        return 'Resources already in use, try again!'
    
    for i in new_resources:
        resources_table.update(set('amount', i['amount']), doc_id=i.doc_id)
        changelog.append({'type': 'update', 'id': item['id'], 'resource': resources_table.get(doc_id=i.doc_id)})

    # update Lambda
    r = requests.put(url, data={'api_key': provider_key, 'changes': changelog}, headers=headers)
    
    return 'Resources acquired!'


@route('/free', method='POST')
def free_request():
    params = json.loads(request.body.getvalue().decode('utf-8'))
    req = requests_table.search(Access_Request.access_key == params['access_key'])
    if len(req) == 0:
        return 'Wrong access_key!'
    req_resources = req['resources'].sort(key=lambda x: x['id'])
    db_resources = resources_table.search(Access_Request.resources.any([x['id'] for x in req_resources])).sort(key=lambda x: x['id'])
    
    new_resources = [{'id': x['id'], 'amount': x['amount'] + y['amount']} for x, y in zip(req_resources, db_resources)]
    
    for i in new_resources:
        resources_table.update(set('amount', i['amount']), doc_id=i.doc_id)
        changelog.append({'type': 'update', 'id': item['id'], 'resource': resources_table.get(doc_id=i.doc_id)})
    
    r = requests.put(url, data={'changes': changelog}, headers=headers)
    requests_table.remove(doc_ids=[req.doc_id])
    return 'Resources freed!'

def update_doc(vCPUs, memory, disk, price, amount):
     def transform(doc):
         doc['vCPUs'] = vCPUs
         doc['memory'] = memory
         doc['price'] = price
         doc['amount'] = amount
     return transform

@route('/update', method='POST')
def update_database():
    params = json.loads(request.body.getvalue().decode('utf-8'))
    print(requests_table.get(doc_id=1))
    changelog = []
    for item in params['update_list']:
        if item['type'] == 'remove':
            if (resources_table.get(doc_id=item['id']) is None):
                return 'Resource with id ' + str(item['id']) + 'not found.'
            else:
                resources_table.remove(doc_ids=[item['id']])
                changelog.append({'type': 'remove', 'resource_id': item['id']})
        elif item['type'] == 'add':
            r = resources_table.insert(item['resource'])
            changelog.append({'type': 'add', 'id': r, 'resource': resources_table.get(doc_id=r)})
        else:
            res = item['resource']
            resources_table.update(update_doc(res['vCPUs'], res['memory'], res['disk'], res['price'], res['amount']), doc_ids=[item['id']])
            changelog.append({'type': 'update', 'id': item['id'], 'resource': resources_table.get(doc_id=item['id'])})
            
    
    r = requests.put(url, data={'changes': changelog}, headers=headers)

    return json.dumps({'api_key': provider_key, 'changes': changelog})

run(host='0.0.0.0',port=sys.argv[1],debug=True)
