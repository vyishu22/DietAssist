import os
import re
from functools import lru_cache


def _to_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


STOPWORDS = {
    'the', 'and', 'for', 'with', 'that', 'this', 'was', 'were', 'are', 'but',
    'very', 'good', 'nice', 'bad', 'too', 'not', 'from', 'have', 'has', 'had',
    'meal', 'meals', 'food', 'foods', 'plan', 'today', 'more', 'less', 'high',
    'low', 'my', 'your', 'you', 'our', 'they', 'them', 'their', 'into', 'than',
}


def _tokenize(text):
    return [
        t for t in re.findall(r'[a-zA-Z]{3,}', (text or '').lower())
        if t not in STOPWORDS
    ]


def _cost_midpoint(item):
    if not isinstance(item, dict):
        return 0.0
    text = str(item.get('estimated_cost', '') or '')
    nums = [int(x) for x in re.findall(r'\d+', text)]
    if not nums:
        return 0.0
    if len(nums) == 1:
        return float(nums[0])
    return (nums[0] + nums[1]) / 2.0


def _feedback_signal(user_id=None, mongo=None, max_docs=50):
    """Build lightweight preference signals from user feedback history."""
    if not user_id or mongo is None:
        return None

    try:
        from bson.objectid import ObjectId
        uid = ObjectId(user_id) if not isinstance(user_id, ObjectId) else user_id
        query = {'user_id': {'$in': [uid, str(uid)]}}
    except Exception:
        query = {'user_id': user_id}

    docs = list(
        mongo.db.feedback.find(query).sort('created_at', -1).limit(max_docs)
    )
    if not docs:
        return None

    boost_terms = {}
    avoid_terms = {}
    ratings = []
    cost_complaints = 0

    for d in docs:
        rating = _to_float(d.get('rating', 0), 0)
        ratings.append(rating)
        comment = str(d.get('comment', '') or '').strip().lower()
        tokens = _tokenize(comment)

        if any(k in comment for k in ('expensive', 'costly', 'too costly', 'overpriced')):
            cost_complaints += 1

        if rating >= 4:
            for t in tokens:
                boost_terms[t] = boost_terms.get(t, 0) + 1
        elif rating <= 2:
            for t in tokens:
                avoid_terms[t] = avoid_terms.get(t, 0) + 1

    avg_rating = (sum(ratings) / len(ratings)) if ratings else 0.0
    return {
        'boost_terms': {k for k, v in boost_terms.items() if v >= 1},
        'avoid_terms': {k for k, v in avoid_terms.items() if v >= 1},
        'avg_rating': avg_rating,
        'cost_sensitive': cost_complaints > 0,
    }


def _feedback_adjustment(item, signal):
    if not signal:
        return 0.0

    if isinstance(item, dict):
        text = (str(item.get('name', '')) + ' ' + str(item.get('reason', ''))).lower()
    else:
        text = str(item).lower()

    score = 0.0
    for term in signal['boost_terms']:
        if term in text:
            score += 0.25
    for term in signal['avoid_terms']:
        if term in text:
            score -= 0.35

    if signal.get('cost_sensitive') and _cost_midpoint(item) > 100:
        score -= 0.20

    # If overall feedback is poor, penalize likely problematic items slightly.
    if signal.get('avg_rating', 0) < 3 and any(k in text for k in ('fried', 'sugary', 'processed')):
        score -= 0.25

    return score


@lru_cache(maxsize=1)
def _load_bundle():
    """Load trained ML artifacts if available.

    Returns dict with keys: model, vectorizer, scaler. If no model exists,
    returns None and caller should fall back to original ordering.
    """
    model_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'ml', 'personalizer.joblib')
    )
    if not os.path.exists(model_path):
        return None

    try:
        import joblib
        bundle = joblib.load(model_path)
        if not isinstance(bundle, dict):
            return None
        if not bundle.get('model') or not bundle.get('vectorizer'):
            return None
        return bundle
    except Exception:
        return None


def _profile_features(health_conditions, food_preference, allergies):
    return [
        1.0 if food_preference == 'vegetarian' else 0.0,
        float(len(allergies or [])),
        _to_float((health_conditions or {}).get('diabetes', 0)),
        _to_float((health_conditions or {}).get('cholesterol', 0)),
        _to_float((health_conditions or {}).get('obesity_bmi', 0)),
        _to_float(str((health_conditions or {}).get('blood_pressure', '0/0')).split('/')[0], 0),
        _to_float((str((health_conditions or {}).get('blood_pressure', '0/0')).split('/') + ['0'])[1], 0),
    ]


def rank_items(items, health_conditions, food_preference, allergies, user_id=None, mongo=None):
    """Return ML-ranked items when model is available, else unchanged input.

    Uses RandomForestRegressor predictions over text + profile features.
    """
    if not isinstance(items, list) or len(items) <= 1:
        return items

    bundle = _load_bundle()
    feedback = _feedback_signal(user_id=user_id, mongo=mongo)

    preds = [0.0 for _ in items]

    if bundle:
        model = bundle['model']
        vectorizer = bundle['vectorizer']
        scaler = bundle.get('scaler')

        try:
            import numpy as np
            from scipy.sparse import hstack

            profile = _profile_features(health_conditions, food_preference, allergies)
            texts = []
            for item in items:
                if isinstance(item, dict):
                    texts.append((item.get('name', '') + ' ' + item.get('reason', '')).strip())
                else:
                    texts.append(str(item))

            text_x = vectorizer.transform(texts)
            profile_mat = np.array([profile for _ in items], dtype=float)
            if scaler is not None:
                profile_mat = scaler.transform(profile_mat)

            full_x = hstack([text_x, profile_mat])
            preds = [float(x) for x in model.predict(full_x)]
        except Exception:
            preds = [0.0 for _ in items]

    # Apply feedback-based learning adjustment even if ML bundle is unavailable.
    adjusted = []
    for i, item in enumerate(items):
        score = preds[i] + _feedback_adjustment(item, feedback)
        adjusted.append((i, score, item))

    if bundle or feedback:
        adjusted.sort(key=lambda x: x[1], reverse=True)
        return [it for _, _, it in adjusted]

    return items
