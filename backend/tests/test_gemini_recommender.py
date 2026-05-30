import json
import types

import pytest

from app.services import gemini_recommender


def test_get_recommendations_from_gemini_success(monkeypatch):
    # Prepare a fake gemini response with strict JSON
    fake_response = {
        "Food": {
            "Morning": [{"name": "Oatmeal", "reason": "High fiber, supports blood sugar control"}],
            "Afternoon": [],
            "Evening": []
        },
        "Drinks": [{"name": "Water", "reason": "Hydration"}],
        "Snacks": [{"name": "Apple", "reason": "Low calorie fruit"}],
        "alternativeMessage": "Alternative food options are available.",
        "healthyTipsForToday": {"hydration": "Drink water regularly"}
    }

    class FakeHTTPResp:
        status_code = 200
        def json(self):
            return {
                "choices": [
                    {"message": {"content": json.dumps(fake_response)}}
                ]
            }

    # Ensure API key is present to avoid runtime errors
    monkeypatch.setenv('OPENROUTER_API_KEY', 'testkey')
    monkeypatch.setattr(gemini_recommender, 'OPENROUTER_API_KEY', 'testkey')

    # Mock requests.post
    import requests
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: FakeHTTPResp())

    result = gemini_recommender.get_recommendations_from_gemini(
        patient_name="Test Patient",
        health_conditions={"diabetes": "90"},
        allergies=[],
        food_preference="vegetarian"
    )

    # Assertions on structure
    assert 'Food' in result
    assert 'Drinks' in result
    assert 'Snacks' in result
    assert result['alternativeMessage'] == 'Alternative food options are available.'
    assert result['healthyTipsForToday']['hydration'] == 'Drink water regularly'


def test_get_recommendations_adds_doctor_alert(monkeypatch):
    # Response without doctorAlert; service should add it when multiple conditions exceed thresholds
    fake_response = {
        "Food": {"Morning": [], "Afternoon": [], "Evening": []},
        "Drinks": [],
        "Snacks": [],
        "alternativeMessage": "Alternative food options are available.",
        "healthyTipsForToday": {}
    }

    class FakeHTTPResp:
        status_code = 200
        def json(self):
            return {
                "choices": [
                    {"message": {"content": json.dumps(fake_response)}}
                ]
            }

    monkeypatch.setenv('OPENROUTER_API_KEY', 'testkey')
    monkeypatch.setattr(gemini_recommender, 'OPENROUTER_API_KEY', 'testkey')
    import requests
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: FakeHTTPResp())

    conditions = {"diabetes": "150", "cholesterol": "220"}

    result = gemini_recommender.get_recommendations_from_gemini(
        patient_name="Test",
        health_conditions=conditions,
        allergies=[],
        food_preference="non-vegetarian"
    )

    assert result.get('doctorAlert') == 'Please consult a doctor for personalized medical guidance.'
