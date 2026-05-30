import json


def _fake_verify(token):
    return {'user_id': 'user123', 'user_type': 'patient'}


def _fake_health():
    return {
        'name': 'Jane Doe',
        'health_conditions': {'diabetes': '140'},
        'allergies': [],
        'food_preference': 'vegetarian'
    }


def test_alternatives_uses_openrouter(monkeypatch, client):
    # configure auth and health info as before
    monkeypatch.setattr('app.routes.recommendations.verify_token', _fake_verify)
    monkeypatch.setattr('app.routes.recommendations.HealthInformation',
                        type('H', (), {'find_by_user_id': staticmethod(lambda user_id, mongo: _fake_health())}))

    # stub OpenRouter output to be two valid items
    def fake_raw(prompt):
        return '[{"name": "AI Food 1", "reason": "Good for diabetes"}, {"name": "AI Food 2", "reason": "Low sodium"}]'
    monkeypatch.setattr('app.routes.recommendations._call_openrouter_raw', fake_raw)

    headers = {'Authorization': 'Bearer token', 'Content-Type': 'application/json'}
    resp = client.post('/api/recommendations/alternatives', headers=headers,
                       data=json.dumps({'category': 'food'}))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['category'] == 'food'
    # only the first item should be kept per new requirement
    assert len(data['alternatives']) == 1
    assert data['alternatives'][0]['name'] == 'AI Food 1'
    assert data['alternatives'][0]['reason'] == 'Good for diabetes'


def test_alternatives_filters_allergies(monkeypatch, client):
    # user allergic to nuts; ensure any AI response containing almond milk is dropped
    monkeypatch.setattr('app.routes.recommendations.verify_token', _fake_verify)
    bad_health = _fake_health()
    bad_health['allergies'] = ['nuts']
    monkeypatch.setattr('app.routes.recommendations.HealthInformation',
                        type('H', (), {'find_by_user_id': staticmethod(lambda user_id, mongo: bad_health)}))

    # AI returns one drink with an allergen and one safe item
    def fake_raw(prompt):
        return '[{"name": "Almond Milk", "reason": "Low sugar"}, {"name": "Herbal Tea", "reason": "Caffeine-free hydration"}]'
    monkeypatch.setattr('app.routes.recommendations._call_openrouter_raw', fake_raw)

    headers = {'Authorization': 'Bearer token', 'Content-Type': 'application/json'}
    resp = client.post('/api/recommendations/alternatives', headers=headers,
                       data=json.dumps({'category': 'drinks'}))
    assert resp.status_code == 200
    data = resp.get_json()
    # almond milk should be filtered out
    assert all('Almond Milk' not in a['name'] for a in data['alternatives'])
    assert data['alternatives'][0]['name'] == 'Herbal Tea'


def test_alternatives_fallback_to_ai(monkeypatch, client):
    # make dataset call return empty by monkeypatching the engine function directly
    import app.services.alternatives_engine as _ae
    monkeypatch.setattr(_ae, 'get_alternatives', lambda *args, **kw: [])
    monkeypatch.setattr('app.routes.recommendations.verify_token', _fake_verify)
    monkeypatch.setattr('app.routes.recommendations.HealthInformation',
                        type('H', (), {'find_by_user_id': staticmethod(lambda user_id, mongo: _fake_health())}))

    # monkeypatch OpenRouter raw call to return predictable JSON (single-item AI response)
    def fake_raw(prompt):
        return '[{"name": "AI Item", "reason": "Generated"}]'
    monkeypatch.setattr('app.routes.recommendations._call_openrouter_raw', fake_raw)

    headers = {'Authorization': 'Bearer token', 'Content-Type': 'application/json'}
    resp = client.post('/api/recommendations/alternatives', headers=headers,
                       data=json.dumps({'category': 'food'}))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['alternatives'][0]['name'] == 'AI Item'
