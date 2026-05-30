import json

from app.services import gemini_recommender


def test_genai_route_success(monkeypatch, client):
    # Mock verify_token to accept any token
    def fake_verify(token):
        return {'user_id': 'user123', 'user_type': 'patient'}

    monkeypatch.setattr('app.routes.recommendations.verify_token', fake_verify)

    # Mock HealthInformation.find_by_user_id
    fake_health = {
        'name': 'Jane Doe',
        'health_conditions': {'diabetes': '140'},
        'allergies': [],
        'food_preference': 'vegetarian'
    }
    monkeypatch.setattr('app.routes.recommendations.HealthInformation',
                        type('H', (), {'find_by_user_id': staticmethod(lambda user_id, mongo: fake_health)}) )

    # Mock the Gemini service function
    fake_genai_output = {
        'Food': {'Morning': [{'name': 'Oats', 'reason': 'Fiber helps'}], 'Afternoon': [], 'Evening': []},
        'Drinks': [{'name': 'Water', 'reason': 'Hydration'}],
        'Snacks': [{'name': 'Apple', 'reason': 'Low sugar'}],
        'foods_to_avoid': [{'name': 'Fried rice', 'reason': 'High fat'}],
        'alternativeMessage': 'Alternative food options are available.',
        'healthyTipsForToday': {'hydration': 'Drink water'}
    }

    monkeypatch.setattr(gemini_recommender, 'get_recommendations_from_gemini', lambda *args, **kwargs: fake_genai_output)

    headers = {'Authorization': 'Bearer sometoken', 'Content-Type': 'application/json'}
    resp = client.post('/api/recommendations/genai', headers=headers, data=json.dumps({}))

    assert resp.status_code == 200
    data = resp.get_json()
    # genai endpoint still returns detailed structure
    assert data['Food']['Morning'][0]['name'] == 'Oats'
    assert data['Drinks'][0]['name'] == 'Water'


def test_get_route_aliases_genai(monkeypatch, client):
    # Reuse same setup as genai test to verify /get uses the LLM path
    def fake_verify(token):
        return {'user_id': 'user123', 'user_type': 'patient'}
    monkeypatch.setattr('app.routes.recommendations.verify_token', fake_verify)
    fake_health = {
        'name': 'Jane Doe',
        'health_conditions': {'diabetes': '140'},
        'allergies': [],
        'food_preference': 'vegetarian'
    }
    monkeypatch.setattr('app.routes.recommendations.HealthInformation',
                        type('H', (), {'find_by_user_id': staticmethod(lambda user_id, mongo: fake_health)}) )
    # local copy of fake output (was defined in another test)
    fake_genai_output = {
        'Food': {'Morning': [{'name': 'Oats', 'reason': 'Fiber helps'}], 'Afternoon': [], 'Evening': []},
        'Drinks': [{'name': 'Water', 'reason': 'Hydration'}],
        'Snacks': [{'name': 'Apple', 'reason': 'Low sugar'}],
        'foods_to_avoid': [{'name': 'Fried rice', 'reason': 'High fat'}],
        'alternativeMessage': 'Alternative food options are available.',
        'healthyTipsForToday': {'hydration': 'Drink water'}
    }
    monkeypatch.setattr(gemini_recommender, 'get_recommendations_from_gemini_uncached', lambda *args, **kwargs: fake_genai_output)

    headers = {'Authorization': 'Bearer sometoken', 'Content-Type': 'application/json'}
    resp = client.post('/api/recommendations/get', headers=headers, data=json.dumps({}))
    assert resp.status_code == 200
    data = resp.get_json()
    # simplified response should contain names only
    assert data == {
        'Food': {'morning': [{'name': 'Oats', 'reason': 'Fiber helps'}], 'afternoon': [], 'evening': []},
        'Drinks': [{'name': 'Water', 'reason': 'Hydration'}],
        'Snacks': [{'name': 'Apple', 'reason': 'Low sugar'}],
        'foods_to_avoid': [{'name': 'Fried rice', 'reason': 'High fat'}],
        'alternativeMessage': 'Alternative food options are available.',
        'healthyTipsForToday': {'hydration': 'Drink water'}
    }


def test_genai_route_no_health_info(monkeypatch, client):
    def fake_verify(token):
        return {'user_id': 'user123', 'user_type': 'patient'}

    monkeypatch.setattr('app.routes.recommendations.verify_token', fake_verify)
    # Return None to simulate missing health info
    monkeypatch.setattr('app.routes.recommendations.HealthInformation',
                        type('H', (), {'find_by_user_id': staticmethod(lambda user_id, mongo: None)}) )

    headers = {'Authorization': 'Bearer sometoken', 'Content-Type': 'application/json'}
    resp = client.post('/api/recommendations/genai', headers=headers, data=json.dumps({}))

    assert resp.status_code == 404
    data = resp.get_json()
    assert 'error' in data


# additional tests for gemini response handling

def test_flat_response_structure(monkeypatch, client):
    # simulate the log example where AI returned breakfast/lunch/dinner keys
    def fake_verify(token):
        return {'user_id': 'user123', 'user_type': 'patient'}
    monkeypatch.setattr('app.routes.recommendations.verify_token', fake_verify)
    fake_health = {
        'name': 'Alice',
        'health_conditions': {},
        'allergies': [],
        'food_preference': 'non-veg'
    }
    monkeypatch.setattr('app.routes.recommendations.HealthInformation',
                        type('H', (), {'find_by_user_id': staticmethod(lambda user_id, mongo: fake_health)}) )

    fake_call = lambda *args, **kwargs: json.dumps({
        'breakfast': [
            {'name': 'Scrambled eggs with spinach', 'reason': 'Protein rich'}
        ],
        'lunch': [
            {'name': 'Grilled chicken salad', 'reason': 'Lean protein'}
        ],
        'dinner': [
            {'name': 'Baked salmon', 'reason': 'Omega-3s'}
        ],
        'snacks': [],
        'foods_to_avoid': [{'name': 'Fried rice', 'reason': 'High fat'}]
    })

    monkeypatch.setattr('app.services.gemini_recommender._call_openrouter_raw', lambda p: fake_call(p))
    headers = {'Authorization': 'Bearer sometoken', 'Content-Type': 'application/json'}
    resp = client.post('/api/recommendations/get', headers=headers, data=json.dumps({}))
    assert resp.status_code == 200
    result = resp.get_json()
    # simplified output should mirror names-only structure
    assert result == {
        'Food': {
            'morning': [{'name': 'Scrambled eggs with spinach', 'reason': 'Protein rich'}],
            'afternoon': [{'name': 'Grilled chicken salad', 'reason': 'Lean protein'}],
            'evening': [{'name': 'Baked salmon', 'reason': 'Omega-3s'}]
        },
        'Drinks': [],
        'Snacks': [],
        'foods_to_avoid': [{'name': 'Fried rice', 'reason': 'High fat'}],
        'alternativeMessage': 'Alternative food options are available.',
        'healthyTipsForToday': {}
    }


def test_simplifier_limits_to_one(monkeypatch, client):
    # if the raw AI output contains multiple items per meal, simplifier should
    # truncate to the first one only
    def fake_verify(token):
        return {'user_id': 'user123', 'user_type': 'patient'}
    monkeypatch.setattr('app.routes.recommendations.verify_token', fake_verify)
    fake_health = {
        'name': 'Bob',
        'health_conditions': {},
        'allergies': [],
        'food_preference': 'non-veg'
    }
    monkeypatch.setattr('app.routes.recommendations.HealthInformation',
                        type('H', (), {'find_by_user_id': staticmethod(lambda user_id, mongo: fake_health)}) )

    # output has two breakfast items and two drinks/snacks
    def fake_call(prompt):
        return json.dumps({
            'Food': {
                'Morning': [
                    {'name': 'Item1', 'reason': 'r1'},
                    {'name': 'Item2', 'reason': 'r2'}
                ],
                'Afternoon': [],
                'Evening': []
            },
            'Drinks': [
                {'name': 'Drink1', 'reason': 'd1'},
                {'name': 'Drink2', 'reason': 'd2'}
            ],
            'Snacks': [
                {'name': 'Snack1', 'reason': 's1'},
                {'name': 'Snack2', 'reason': 's2'}
            ],
            'foods_to_avoid': []
        })
    monkeypatch.setattr('app.services.gemini_recommender._call_openrouter_raw', lambda p: fake_call(p))

    headers = {'Authorization': 'Bearer sometoken', 'Content-Type': 'application/json'}
    resp = client.post('/api/recommendations/get', headers=headers, data=json.dumps({}))
    result = resp.get_json()
    assert result['Food']['morning'] == [{'name': 'Item1', 'reason': 'r1'}]
    assert result['Drinks'] == [{'name': 'Drink1', 'reason': 'd1'}]
    assert result['Snacks'] == [{'name': 'Snack1', 'reason': 's1'}]


def test_old_style_gemini_response(monkeypatch, client):
    # stub out verification and health info as before
    def fake_verify(token):
        return {'user_id': 'user123', 'user_type': 'patient'}
    monkeypatch.setattr('app.routes.recommendations.verify_token', fake_verify)
    fake_health = {
        'name': 'Bob',
        'health_conditions': {},
        'allergies': [],
        'food_preference': 'non-veg'
    }
    monkeypatch.setattr('app.routes.recommendations.HealthInformation',
                        type('H', (), {'find_by_user_id': staticmethod(lambda user_id, mongo: fake_health)}) )

    def fake_call(prompt):
        inner = json.dumps({
                'Food': {
                    'Morning': [{'name': 'Steak', 'reason': 'protein'}],
                    'Afternoon': [],
                    'Evening': []
                },
                'Drinks': [{'name': 'Juice', 'reason': 'vitamin'}],
                'Snacks': [{'name': 'Cheese', 'reason': 'calcium'}],
                'alternativeMessage': '',
                'healthyTipsForToday': {}
        })
        return json.dumps({
            'candidates': [
                {'content': {'parts': [{'text': inner}]}}
            ]
        })

    monkeypatch.setattr('app.services.gemini_recommender._call_openrouter_raw', lambda p: fake_call(p))
    headers = {'Authorization': 'Bearer sometoken', 'Content-Type': 'application/json'}
    resp = client.post('/api/recommendations/get', headers=headers, data=json.dumps({}))
    assert resp.status_code == 200
    body = resp.get_json()
    # simplified output should convert breakfast to morning list of names
    # the service injects a default alternativeMessage when it's missing/empty
    assert body == {
        'Food': {'morning': [{'name': 'Steak', 'reason': 'protein'}], 'afternoon': [], 'evening': []},
        'Drinks': [{'name': 'Juice', 'reason': 'vitamin'}],
        'Snacks': [{'name': 'Cheese', 'reason': 'calcium'}],
        'foods_to_avoid': [],
        'alternativeMessage': 'Alternative food options are available.',
        'healthyTipsForToday': {}
    }


def test_gemini_response_missing_keys(monkeypatch, client):
    def fake_verify(token):
        return {'user_id': 'user123', 'user_type': 'patient'}
    monkeypatch.setattr('app.routes.recommendations.verify_token', fake_verify)
    fake_health = {
        'name': 'Cara',
        'health_conditions': {},
        'allergies': [],
        'food_preference': 'vegan'
    }
    monkeypatch.setattr('app.routes.recommendations.HealthInformation',
                        type('H', (), {'find_by_user_id': staticmethod(lambda user_id, mongo: fake_health)}) )

    monkeypatch.setattr('app.services.gemini_recommender._call_openrouter_raw', lambda p: json.dumps({'unexpected': 'value'}))
    headers = {'Authorization': 'Bearer sometoken', 'Content-Type': 'application/json'}
    resp = client.post('/api/recommendations/get', headers=headers, data=json.dumps({}))
    # the routine tolerates missing keys by supplying defaults rather than failing
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {
        'Food': {'morning': [], 'afternoon': [], 'evening': []},
        'Drinks': [],
        'Snacks': [],
        'foods_to_avoid': [],
        'alternativeMessage': 'Alternative food options are available.',
        'healthyTipsForToday': {}
    }
