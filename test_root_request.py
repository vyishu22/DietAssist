import requests
try:
    r = requests.get('http://127.0.0.1:5000/')
    print('Status:', r.status_code)
    print('Length:', len(r.text))
    print('First 200 chars:\n', r.text[:200])
except Exception as e:
    print('Error:', e)
