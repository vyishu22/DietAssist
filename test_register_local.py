from app import create_app
import json

app = create_app()
client = app.test_client()

resp = client.post('/api/auth/patient/register', json={
    'name': 'Local Test',
    'age': 30,
    'email': 'localtest@example.com',
    'password': 'secret123'
})
print('Status code:', resp.status_code)
try:
    print('Response JSON:', resp.get_json())
except Exception as e:
    print('Response data:', resp.data)
