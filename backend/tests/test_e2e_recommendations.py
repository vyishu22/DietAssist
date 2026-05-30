import json

import pytest


def test_full_recommendation_flow(monkeypatch, client):
    """End-to-end style test using Flask test_client to simulate a patient flow:
    1) Save health information via patient endpoint
    2) Call GenAI endpoint and assert structured response
    """
    # Mock verify_token to return a patient user
    def fake_verify(token):
        return {'user_id': 'user123', 'user_type': 'patient'}

    monkeypatch.setattr('app.routes.recommendations.verify_token', fake_verify)

    headers = {'Authorization': 'Bearer sometoken', 'Content-Type': 'application/json'}

    # Save health information
    health_payload = {
        'name': 'E2E Patient',
        'health_conditions': {'diabetes': '140', 'cholesterol': '210'},
        'allergies': [],
        'food_preference': 'vegetarian'
    }

    # The patient route is under /api/patient/health-information - POST
    resp = client.post('/api/patient/health-information', headers=headers, data=json.dumps(health_payload))
    assert resp.status_code in (200, 201)

    # Mock the GenAI service to return a valid response (avoid network calls)
    from app.services import gemini_recommender
    fake_output = {
        'Food': {'Morning': [{'name': 'Oats', 'reason': 'Fiber helps'}], 'Afternoon': [], 'Evening': []},
        'Drinks': [{'name': 'Water', 'reason': 'Hydration'}],
        'Snacks': [{'name': 'Apple', 'reason': 'Low sugar'}],
        'alternativeMessage': 'Alternative food options are available.',
        'healthyTipsForToday': {'hydration': 'Drink water'}
    }
    monkeypatch.setattr(gemini_recommender, 'get_recommendations_from_gemini', lambda *args, **kwargs: fake_output)

    resp2 = client.post('/api/recommendations/genai', headers=headers, data=json.dumps({}))
    assert resp2.status_code == 200
    data = resp2.get_json()

    assert 'Food' in data and 'Drinks' in data and 'Snacks' in data
    assert data['Food']['Morning'][0]['name'] == 'Oats'
    # doctorAlert should be present because two conditions exceed thresholds
    assert data.get('doctorAlert') == 'Please consult a doctor for personalized medical guidance.'
