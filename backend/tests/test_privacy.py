import pytest
from app.routes.patient import patient_bp


def test_delete_health_information(monkeypatch, client):
    # Mock verify_token to return a patient user
    def fake_verify(token):
        return {'user_id': 'user123', 'user_type': 'patient'}

    monkeypatch.setattr('app.routes.patient.verify_token', fake_verify)

    # Mock HealthInformation.find_by_user_id to return a fake record
    fake_health = {'user_id': 'user123', 'name': 'John Doe', 'health_conditions': {}, 'allergies': []}
    class MockHealth:
        @staticmethod
        def find_by_user_id(user_id, mongo):
            return fake_health
        @staticmethod
        def delete_by_user_id(user_id, mongo):
            return True

    monkeypatch.setattr('app.routes.patient.HealthInformation', MockHealth)

    headers = {'Authorization': 'Bearer testtoken', 'Content-Type': 'application/json'}
    resp = client.post('/api/patient/delete-data', headers=headers)
    assert resp.status_code == 200
    assert resp.get_json().get('message') == 'Health data deleted successfully'
