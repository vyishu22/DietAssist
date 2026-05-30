import re
from app.services.gemini_recommender import _build_prompt


def test_prompt_contains_required_keys():
    prompt = _build_prompt('Alice', {'diabetes': '120'}, ['peanut'], 'vegetarian')

    # Must mention producing JSON only
    assert 'valid JSON' in prompt.lower() or 'json' in prompt.lower()

    # Must request breakfast, lunch, dinner, snacks, and drinks keys
    assert 'breakfast' in prompt.lower()
    assert 'drinks' in prompt.lower()

    # Must mention generating recommendations
    assert 'recommend' in prompt.lower()

    # Must include allergies
    assert 'allergies' in prompt.lower() or 'allerg' in prompt.lower()

    # Prompt should contain the patient name and health info
    assert 'Alice' in prompt
    assert 'diabetes' in prompt.lower()


