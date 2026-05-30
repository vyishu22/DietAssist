import os
from collections import defaultdict

from dotenv import load_dotenv
from pymongo import MongoClient


def _to_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _profile_features(health_conditions, food_preference, allergies):
    bp = str((health_conditions or {}).get('blood_pressure', '0/0')).split('/')
    sys_v = _to_float(bp[0] if len(bp) > 0 else 0)
    dia_v = _to_float(bp[1] if len(bp) > 1 else 0)
    return [
        1.0 if food_preference == 'vegetarian' else 0.0,
        float(len(allergies or [])),
        _to_float((health_conditions or {}).get('diabetes', 0)),
        _to_float((health_conditions or {}).get('cholesterol', 0)),
        _to_float((health_conditions or {}).get('obesity_bmi', 0)),
        sys_v,
        dia_v,
    ]


def main():
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/dietassist')

    client = MongoClient(mongo_uri)
    db = client.get_default_database()

    # Build average rating per user from feedback history.
    user_rating = defaultdict(list)
    for fb in db.feedback.find({}):
        uid = str(fb.get('user_id', ''))
        rating = fb.get('rating')
        if uid and isinstance(rating, (int, float)):
            user_rating[uid].append(float(rating))

    avg_rating = {uid: sum(vals) / len(vals) for uid, vals in user_rating.items() if vals}

    texts = []
    profile_rows = []
    targets = []

    for rec in db.recommendations.find({}):
        uid = str(rec.get('user_id', ''))
        y = avg_rating.get(uid)
        if y is None:
            continue

        health = db.health_information.find_one({'user_id': uid}) or {}
        hc = health.get('health_conditions', {})
        pref = health.get('food_preference', 'non-vegetarian')
        allergies = health.get('allergies', [])
        pvec = _profile_features(hc, pref, allergies)

        for bucket in ['breakfast', 'lunch', 'dinner', 'snacks']:
            for item in rec.get(bucket, []):
                if isinstance(item, dict):
                    name = item.get('name', '')
                    reason = item.get('reason', '')
                    text = (name + ' ' + reason).strip()
                else:
                    text = str(item)

                if not text:
                    continue

                texts.append(text)
                profile_rows.append(pvec)
                targets.append(y)

    if len(targets) < 20:
        print('Not enough training rows. Need at least 20 labeled items from feedback+history.')
        return

    from scipy.sparse import hstack
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import StandardScaler
    import joblib
    import numpy as np

    vectorizer = TfidfVectorizer(max_features=2000, ngram_range=(1, 2), min_df=1)
    text_x = vectorizer.fit_transform(texts)

    profile_arr = np.array(profile_rows, dtype=float)
    scaler = StandardScaler()
    profile_x = scaler.fit_transform(profile_arr)

    x = hstack([text_x, profile_x])
    y = np.array(targets, dtype=float)

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(x, y)

    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'ml'))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'personalizer.joblib')
    joblib.dump({'model': model, 'vectorizer': vectorizer, 'scaler': scaler}, out_path)
    print(f'Trained model saved to: {out_path}')


if __name__ == '__main__':
    main()
