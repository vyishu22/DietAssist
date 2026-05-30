import json
import urllib.request
import urllib.error

BASE = 'http://127.0.0.1:5000'

def post(path, payload, headers=None):
    url = BASE + path
    data = json.dumps(payload).encode('utf-8')
    hdrs = {'Content-Type': 'application/json'}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, r.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return None, str(e)

# 1) Register
import time

reg_payload = {
    'name': 'E2E Test User',
    'age': 35,
    'email': f'e2e_test_user_{int(time.time())}@example.com',
    'password': 'TestPass123'
}
status, body = post('/api/auth/patient/register', reg_payload)
print('REGISTER', status)
print(body)

if status != 201:
    print('Registration failed, aborting')
    exit(1)

reg = json.loads(body)
token = reg.get('token')
user_id = reg.get('user_id')

# 2) Submit health info
health_payload = {
    'name': 'E2E Test User',
    'health_conditions': {'diabetes': '110', 'blood_pressure': '130/85'},
    'allergies': ['Peanuts'],
    'food_preference': 'vegetarian'
}
status, body = post('/api/patient/health-information', health_payload, headers={'Authorization': 'Bearer ' + token})
print('HEALTH SAVE', status)
print(body)

# 3) Get recommendations
status, body = post('/api/recommendations/get', {}, headers={'Authorization': 'Bearer ' + token})
print('RECOMMENDATIONS', status)
print(body)
