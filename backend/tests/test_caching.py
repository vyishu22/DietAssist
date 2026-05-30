import json
import types

from app.services import gemini_recommender


def test_caching_uses_cache(monkeypatch):
    calls = {'count': 0}

    fake_response = {
        'Food': {'Morning': [], 'Afternoon': [], 'Evening': []},
        'Drinks': [],
        'Snacks': [],
        'alternativeMessage': 'Alternative food options are available.',
        'healthyTipsForToday': {}
    }

    class FakeHTTPResp:
        status_code = 200
        def json(self):
            return {
                "choices": [
                    {"message": {"content": json.dumps(fake_response)}}
                ]
            }

    def fake_post(*args, **kwargs):
        calls['count'] += 1
        return FakeHTTPResp()

    # Ensure API key exists
    monkeypatch.setenv('OPENROUTER_API_KEY', 'testkey')
    monkeypatch.setattr(gemini_recommender, 'OPENROUTER_API_KEY', 'testkey')

    # Mock requests.post to count calls
    import requests
    monkeypatch.setattr(requests, 'post', fake_post)

    # Run twice with same inputs
    res1 = gemini_recommender.get_recommendations_from_gemini('A', {'diabetes': '100'}, [], 'vegetarian')
    res2 = gemini_recommender.get_recommendations_from_gemini('A', {'diabetes': '100'}, [], 'vegetarian')

    # If cache works, requests.post should be called only once (or at most once depending on caching availability)
    assert calls['count'] <= 1
