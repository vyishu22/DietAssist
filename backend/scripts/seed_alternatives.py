"""(deprecated) script previously used to seed a local alternatives
dataset.  The project now relies exclusively on OpenRouter API calls, so
this helper no longer performs any work.
"""

import json
import os
import sys
from pathlib import Path

from app.services.gemini_recommender import _call_openrouter_raw

# categories we support
CATEGORIES = ['food', 'drinks', 'snacks']

# Items for which we want AI-generated alternatives.
# This is just an example seed; adapt to your domain.
BASE_ITEMS = {
    'food': ['Rice', 'Pasta', 'Chicken', 'Beef', 'Salad'],
    'drinks': ['Soda', 'Coffee', 'Juice'],
    'snacks': ['Chips', 'Cake', 'Cookies']
}

OUTPUT_PATH = Path(__file__).parent.parent / 'data' / 'alternatives.json'


def generate_alternatives_for(item: str, category: str) -> list:
    """Call OpenRouter to suggest two healthy alternatives for a given item."""
    prompt = f"""You are a healthcare nutritionist. The patient is used to
having {item} as a {category}. Suggest exactly two healthier alternative
{category} items they could enjoy instead. Respond with a JSON array
containing two objects, each with 'name' and 'reason' keys. Do not output
any explanatory text outside the JSON.

Example response:
[
  {{"name": "Item A", "reason": "Reason A"}},
  {{"name": "Item B", "reason": "Reason B"}}
]
"""
    try:
        raw = _call_openrouter_raw(prompt)
    except Exception as e:
        print(f"API call failed for {item}/{category}: {e}")
        return []

    # attempt to extract JSON array
    start = raw.find('[')
    end = raw.rfind(']')
    if start == -1 or end == -1:
        print(f"Could not parse response for {item}/{category}: {raw}")
        return []
    snippet = raw[start:end+1]
    try:
        arr = json.loads(snippet)
        if isinstance(arr, list):
            return arr
    except json.JSONDecodeError:
        try:
            arr = json.loads(snippet.replace("'", '"'))
            return arr
        except Exception:
            print(f"Failed JSON decode for {item}/{category}: {snippet}")
    return []


def main():
    # no-op: dataset seeding has been disabled, application now uses OpenRouter
    print('seed_alternatives is deprecated; alternatives are generated via OpenRouter API only.')


if __name__ == '__main__':
    main()
