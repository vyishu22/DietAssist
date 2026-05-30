import json
from pathlib import Path
from typing import List, Dict, Any

# this module is kept for compatibility but no longer returns data
_DATA: List[Dict[str, Any]] = []

def _load_data():
    global _DATA
    # file is located at backend/data/alternatives.json (two levels above app)
    data_path = Path(__file__).parent.parent.parent / 'data' / 'alternatives.json'
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            _DATA = json.load(f)
    except FileNotFoundError:
        _DATA = []


def _matches_allergies(item: Dict[str, Any], allergies: List[str]) -> bool:
    """Return True if item does **not** contain any of the provided allergies."""
    item_allergens = [a.lower() for a in item.get('allergens', [])]
    for a in allergies:
        if a.lower() in item_allergens:
            return False
    return True


def _score_item(item: Dict[str, Any], health_conditions: Dict[str, Any]) -> float:
    """Compute a score for an item based on health_conditions.

    - Each tag matching a condition contributes the numeric value of that
      condition (or 1 if it's not convertible to float).
    - This allows items relevant to high-severity conditions to rank higher.
    """
    tags = item.get('tags', [])
    score = 0.0
    for t in tags:
        if t in health_conditions:
            # try convert the condition value to float, fallback to 1
            try:
                val = float(health_conditions[t])
            except Exception:
                val = 1.0
            score += val
    # pre-sort tiebreaker: shorter name gets tiny boost (deterministic)
    name = item.get('name','')
    score += 1.0 / (len(name) + 1)
    return score


def get_alternatives(category: str,
                     allergies: List[str],
                     health_conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Local alternatives are deprecated: always return empty so caller uses OpenRouter."""
    return []
