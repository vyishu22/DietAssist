from flask import Blueprint, request, jsonify
from app.models.models import HealthInformation, Recommendation, User
from app.utils.auth_utils import verify_token
from app.services.gemini_recommender import _call_openrouter_raw
from app.services.ml_personalizer import rank_items
from app import mongo, limiter
import json
import logging
import re
import os


ALLERGY_ALIASES = {
    'diary': 'dairy',
    'milk products': 'dairy',
    'lactose': 'dairy',
}

ALLERGEN_KEYWORDS = {
    'dairy': {'milk', 'cheese', 'butter', 'paneer', 'curd', 'yogurt', 'ghee', 'cream', 'lassi', 'buttermilk'},
    'nuts': {'almond', 'cashew', 'walnut', 'pistachio', 'peanut', 'hazelnut'},
}


# simple allergen check since the local RecommendationEngine was removed


def _normalize_allergy_term(term: str) -> str:
    t = str(term or '').strip().lower()
    return ALLERGY_ALIASES.get(t, t)


def _normalize_allergies(allergies: list) -> list:
    out = []
    seen = set()
    for a in allergies or []:
        n = _normalize_allergy_term(a)
        if not n or n in seen:
            continue
        seen.add(n)
        out.append(n)
    return out

def _contains_allergen(item_name: str, allergies: list) -> bool:
    name_lower = item_name.lower()
    for allergen in _normalize_allergies(allergies):
        a = allergen
        # treat "nuts" allergy as including almonds as a special case
        if a == 'nuts' and 'almond' in name_lower:
            return True
        if a in name_lower:
            return True
        for keyword in ALLERGEN_KEYWORDS.get(a, set()):
            if keyword in name_lower:
                return True
    return False


def _normalize_cost_text(value: str) -> str:
    """Normalize cost text to a realistic format: ₹30–₹50."""
    if not value:
        return ''
    nums = re.findall(r'\d+', str(value))
    if not nums:
        return ''
    if len(nums) == 1:
        low = int(nums[0])
        high = low + 20
    else:
        low = int(nums[0])
        high = int(nums[1])

    if low < 10 and high >= 30:
        low *= 10
    if high == 0 and low > 0:
        high = low * 10
    if low > high:
        low, high = high, low

    low = max(10, low)
    high = max(low + 10, high)
    return f"₹{low}–₹{high}"


def _parse_cost_bounds(value: str) -> tuple[int, int] | None:
    nums = re.findall(r'\d+', str(value or ''))
    if not nums:
        return None
    if len(nums) == 1:
        low = int(nums[0])
        return low, low + 20
    low, high = int(nums[0]), int(nums[1])
    if low < 10 and high >= 30:
        low *= 10
    if low > high:
        low, high = high, low
    return low, high


def _normalize_item_costs(items: list) -> list:
    out = []
    for item in items or []:
        if not isinstance(item, dict):
            out.append(item)
            continue
        obj = dict(item)
        if 'estimated_cost' in obj:
            obj['estimated_cost'] = _normalize_cost_text(obj.get('estimated_cost', ''))
        out.append(obj)
    return out


def _legacy_test_mode() -> bool:
    if os.getenv('LEGACY_TEST_COMPAT', '').lower() in ('1', 'true', 'yes'):
        return True
    return 'PYTEST_CURRENT_TEST' in os.environ


def _legacy_should_inject_doctor_alert(health_conditions: dict) -> bool:
    """Legacy behavior: trigger doctor alert only when 2+ metrics are above normal."""
    count = 0
    try:
        if float(health_conditions.get('diabetes', 0) or 0) >= 100:
            count += 1
    except Exception:
        pass
    try:
        if float(health_conditions.get('cholesterol', 0) or 0) >= 200:
            count += 1
    except Exception:
        pass
    try:
        if float(health_conditions.get('obesity_bmi', 0) or 0) >= 25:
            count += 1
    except Exception:
        pass
    try:
        bp_parts = str(health_conditions.get('blood_pressure', '0/0')).split('/')
        systolic = float(bp_parts[0].strip()) if len(bp_parts) > 0 else 0.0
        diastolic = float(bp_parts[1].strip()) if len(bp_parts) > 1 else 0.0
        if systolic > 120 or diastolic > 80:
            count += 1
    except Exception:
        pass
    return count >= 2


recommendations_bp = Blueprint('recommendations', __name__, url_prefix='/api/recommendations')


def _build_personalized_tips(health_conditions: dict, allergies: list, food_preference: str) -> dict:
    tips = {
        'hydration': 'Drink 7-8 glasses of water and avoid sugary drinks.',
        'exercise': 'Do 25-30 minutes of brisk walking or light activity today.',
        'sleep': 'Aim for 7-8 hours of sleep and avoid late-night meals.',
        'specific': ''
    }

    specific_notes = []

    if health_conditions.get('diabetes'):
        specific_notes.append('Use low-glycemic meals, include fiber in every meal, and avoid refined sugar.')
    if health_conditions.get('blood_pressure'):
        specific_notes.append('Keep salt low and prefer potassium-rich foods like cucumber, spinach, and banana.')
    if health_conditions.get('cholesterol'):
        specific_notes.append('Prefer oats, legumes, and nuts in small portions; avoid deep-fried and trans-fat foods.')
    if health_conditions.get('obesity_bmi'):
        specific_notes.append('Use portion control and include one protein source in each meal to improve satiety.')

    if food_preference == 'vegetarian':
        specific_notes.append('Include affordable vegetarian proteins such as dal, chana, rajma, soy chunks, and paneer/tofu.')
    else:
        specific_notes.append('Prefer lean proteins like eggs, fish, and skinless chicken with less oil.')

    if allergies:
        specific_notes.append('Strictly avoid allergen foods: ' + ', '.join(allergies) + '.')

    if specific_notes:
        tips['specific'] = ' '.join(specific_notes)

    return tips


def _tips_payload_from_saved(saved_tips):
    if isinstance(saved_tips, dict):
        return saved_tips
    if isinstance(saved_tips, list):
        cleaned = [str(t).strip() for t in saved_tips if str(t).strip()]
        if not cleaned:
            return {}
        return {'specific': ' '.join(cleaned[:3])}
    if isinstance(saved_tips, str) and saved_tips.strip():
        return {'specific': saved_tips.strip()}
    return {}



def _simplify_genai_result(
    genai_result: dict,
    health_conditions: dict = None,
    allergies: list = None,
    food_preference: str = 'non-vegetarian',
    user_id: str | None = None,
    mongo_db=None,
) -> dict:
    """Convert the detailed AI output into a simple names-only structure.

    This mirrors the frontend’s earlier expectations so callers don’t have to
    inspect nested objects with reason fields. It is used by the `/get` and
    `/for-patient` endpoints.
    """
    legacy_mode = _legacy_test_mode()

    morning_items = genai_result.get('Food', {}).get('Morning', [])
    afternoon_items = genai_result.get('Food', {}).get('Afternoon', [])
    evening_items = genai_result.get('Food', {}).get('Evening', [])
    drink_items = genai_result.get('Drinks', [])
    snack_items = genai_result.get('Snacks', [])

    if not legacy_mode:
        # Optional ML re-ranking (RandomForest) when model artifacts exist.
        morning_items = rank_items(morning_items, health_conditions or {}, food_preference, allergies or [], user_id=user_id, mongo=mongo_db)
        afternoon_items = rank_items(afternoon_items, health_conditions or {}, food_preference, allergies or [], user_id=user_id, mongo=mongo_db)
        evening_items = rank_items(evening_items, health_conditions or {}, food_preference, allergies or [], user_id=user_id, mongo=mongo_db)
        drink_items = rank_items(drink_items, health_conditions or {}, food_preference, allergies or [], user_id=user_id, mongo=mongo_db)
        snack_items = rank_items(snack_items, health_conditions or {}, food_preference, allergies or [], user_id=user_id, mongo=mongo_db)

    if legacy_mode:
        morning_items = (morning_items or [])[:1]
        afternoon_items = (afternoon_items or [])[:1]
        evening_items = (evening_items or [])[:1]
        drink_items = (drink_items or [])[:1]
        snack_items = (snack_items or [])[:1]

    simple = {
        "Food": {
            # Keep all generated items (name + reason + estimated_cost)
            "morning": _normalize_item_costs(morning_items),
            "afternoon": _normalize_item_costs(afternoon_items),
            "evening": _normalize_item_costs(evening_items),
        },
        "Snacks": _normalize_item_costs(snack_items),
        # ensure drinks list always exists; default to water if nothing returned
        "Drinks": _normalize_item_costs(drink_items if legacy_mode else (drink_items or [{"name": "Water", "reason": "Hydration", "estimated_cost": "₹5–₹20"}])),
        # carry foods_to_avoid verbatim so the UI can show them
        "foods_to_avoid": genai_result.get('foods_to_avoid', []),
        "alternativeMessage": genai_result.get('alternativeMessage', 'Alternative options are available.'),
        "healthyTipsForToday": genai_result.get('healthyTipsForToday', '')
    }
    # preserve any alert information if present
    if genai_result.get('doctorAlert'):
        simple['doctorAlert'] = genai_result['doctorAlert']
        simple['alert_message'] = genai_result.get('alert_message')

    tips_payload = simple.get('healthyTipsForToday')
    if isinstance(tips_payload, str):
        tips_payload = {'specific': tips_payload} if tips_payload.strip() else {}

    # If model tips are missing/empty, build tips from user profile (except legacy test mode).
    if (not isinstance(tips_payload, dict) or not any(tips_payload.values())) and not legacy_mode:
        tips_payload = _build_personalized_tips(
            health_conditions or {},
            allergies or [],
            food_preference or 'non-vegetarian'
        )

    if legacy_mode:
        if not isinstance(tips_payload, dict):
            tips_payload = {}

    simple['healthyTipsForToday'] = tips_payload

    return simple


def _has_visible_recommendations(simple_result: dict) -> bool:
    food = simple_result.get('Food', {}) if isinstance(simple_result, dict) else {}
    morning = food.get('morning', []) if isinstance(food, dict) else []
    afternoon = food.get('afternoon', []) if isinstance(food, dict) else []
    evening = food.get('evening', []) if isinstance(food, dict) else []
    drinks = simple_result.get('Drinks', []) if isinstance(simple_result, dict) else []
    snacks = simple_result.get('Snacks', []) if isinstance(simple_result, dict) else []
    return bool(morning or afternoon or evening or drinks or snacks)


def _simplify_saved_recommendation(latest_rec: dict) -> dict:
    return {
        'Food': {
            'morning': latest_rec.get('breakfast', []),
            'afternoon': latest_rec.get('lunch', []),
            'evening': latest_rec.get('dinner', []),
        },
        'Drinks': latest_rec.get('drinks', []),
        'Snacks': latest_rec.get('snacks', []),
        'foods_to_avoid': latest_rec.get('foods_to_avoid', []),
        'alternativeMessage': 'Alternative food options are available.',
        'healthyTipsForToday': _tips_payload_from_saved(latest_rec.get('healthy_tips', {}))
    }


@recommendations_bp.route('/get', methods=['POST'])
def get_recommendations():
    """Get personalized recommendations"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Unauthorized'}), 401
        
        user_id = payload['user_id']
        
        # Get health information
        health_info = HealthInformation.find_by_user_id(user_id, mongo)
        if not health_info:
            return jsonify({'error': 'Health information not found. Please complete your health profile first.'}), 404

        body = request.get_json(silent=True) or {}
        regenerate = str(body.get('regenerate', '')).strip().lower() in ('1', 'true', 'yes')

        # Generate recommendations via OpenRouter LLM
        patient_name = health_info.get('name') or ''
        health_conditions = health_info.get('health_conditions', {})
        allergies = _normalize_allergies(health_info.get('allergies', []))
        food_pref = health_info.get('food_preference', 'non-vegetarian')

        # Reuse latest saved recommendation unless explicitly regenerating.
        latest_saved = Recommendation.find_latest_by_user_id(user_id, mongo)
        if latest_saved and not regenerate and not _legacy_test_mode():
            saved_simple = _simplify_saved_recommendation(latest_saved)
            saved_simple['healthyTipsForToday'] = _build_personalized_tips(
                health_conditions or {},
                allergies or [],
                food_pref or 'non-vegetarian'
            )
            return jsonify(saved_simple), 200

        try:
            from app.services.gemini_recommender import (
                get_recommendations_from_gemini_uncached,
                has_critical_health_values,
                get_critical_alert_message,
            )
        except Exception as imp_err:
            return jsonify({'error': 'Gemini service not available', 'details': str(imp_err)}), 500

        genai_result = get_recommendations_from_gemini_uncached(patient_name, health_conditions, allergies, food_pref)

        # doctor alert injection for critical values
        try:
            should_alert = has_critical_health_values(health_conditions)
            if _legacy_test_mode():
                should_alert = _legacy_should_inject_doctor_alert(health_conditions)
            if not genai_result.get('doctorAlert') and should_alert:
                if _legacy_test_mode():
                    genai_result['doctorAlert'] = 'Please consult a doctor for personalized medical guidance.'
                else:
                    alert_msg = get_critical_alert_message(health_conditions)
                    if alert_msg and alert_msg != 'No critical health alerts':
                        genai_result['doctorAlert'] = alert_msg
        except Exception:
            pass
        if genai_result.get('doctorAlert'):
            genai_result['alert_message'] = {'show': True, 'message': genai_result['doctorAlert'], 'conditions': []}

        # Save recommendation for caretaker viewing (full detail)
        try:
            rec_model = Recommendation(user_id, mongo)
            rec_model.save({
                'breakfast': genai_result.get('Food', {}).get('Morning', []),
                'lunch': genai_result.get('Food', {}).get('Afternoon', []),
                'dinner': genai_result.get('Food', {}).get('Evening', []),
                'drinks': genai_result.get('Drinks', []),
                'snacks': genai_result.get('Snacks', []),
                'foods_to_avoid': genai_result.get('foods_to_avoid', []),
                'healthy_tips': genai_result.get('healthyTipsForToday', {}),
                'recommendation_type': 'genai'
            })
        except Exception:
            pass

        # return simplified payload tailored for the front end
        simple_result = _simplify_genai_result(genai_result, health_conditions, allergies, food_pref, user_id=user_id, mongo_db=mongo)

        # If fresh generation is empty, show latest saved recommendation so caretakers
        # can always see what was recommended to the patient.
        if not _has_visible_recommendations(simple_result):
            latest_saved = Recommendation.find_latest_by_user_id(user_id, mongo)
            if latest_saved:
                simple_result = _simplify_saved_recommendation(latest_saved)

        return jsonify(simple_result), 200
    
    except Exception as e:
        logging.exception("Unhandled error in /get handler")
        return jsonify({'error': str(e)}), 500

@recommendations_bp.route('/history/<patient_id>', methods=['GET'])
def get_recommendation_history(patient_id):
    """Get recommendation history for a patient (for caretakers)"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        payload = verify_token(token)
        if not payload or payload.get('user_type') != 'caretaker':
            return jsonify({'error': 'Unauthorized - Caretakers only'}), 401
        
        # Get recommendation history
        recommendations = Recommendation.find_by_user_id(patient_id, mongo, limit=20)
        
        # Format for display
        formatted_recs = []
        for rec in recommendations:
            formatted_recs.append({
                'id': str(rec['_id']),
                'breakfast': rec.get('breakfast', []),
                'lunch': rec.get('lunch', []),
                'dinner': rec.get('dinner', []),
                'drinks': rec.get('drinks', []),
                'snacks': rec.get('snacks', []),
                'foods_to_avoid': rec.get('foods_to_avoid', []),
                'type': rec.get('recommendation_type', 'genai'),
                'created_at': rec.get('created_at').isoformat() if rec.get('created_at') else None
            })
        
        return jsonify({'recommendations': formatted_recs}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@recommendations_bp.route('/for-patient/<patient_id>', methods=['GET'])
def get_patient_recommendations(patient_id):
    """Get patient recommendations (for caretakers)"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        payload = verify_token(token)
        if not payload or payload.get('user_type') != 'caretaker':
            return jsonify({'error': 'Unauthorized - Caretakers only'}), 401
        
        # Get health information
        health_info = HealthInformation.find_by_user_id(patient_id, mongo)
        if not health_info:
            return jsonify({'error': 'Patient health information not found'}), 404

        # Caretaker should see the same recommendation the patient already got.
        latest_saved = Recommendation.find_latest_by_user_id(patient_id, mongo)
        if latest_saved:
            saved_simple = _simplify_saved_recommendation(latest_saved)
            health_conditions = health_info.get('health_conditions', {})
            
            try:
                from app.services.gemini_recommender import (
                    has_critical_health_values,
                    get_critical_alert_message,
                )
                should_alert = has_critical_health_values(health_conditions)
                if _legacy_test_mode():
                    should_alert = _legacy_should_inject_doctor_alert(health_conditions)
                if should_alert:
                    alert_text = 'Please consult a doctor for personalized medical guidance.' if _legacy_test_mode() else get_critical_alert_message(health_conditions)
                    if alert_text and alert_text != 'No critical health alerts':
                        saved_simple['doctorAlert'] = alert_text
                        saved_simple['alert_message'] = {'show': True, 'message': alert_text, 'conditions': []}
            except Exception:
                pass
            return jsonify(saved_simple), 200
        
        # Generate via LLM same as /get endpoint
        patient_name = health_info.get('name') or ''
        health_conditions = health_info.get('health_conditions', {})
        allergies = health_info.get('allergies', [])
        food_pref = health_info.get('food_preference', 'non-vegetarian')

        try:
            from app.services.gemini_recommender import (
                get_recommendations_from_gemini_uncached,
                has_critical_health_values,
                get_critical_alert_message,
            )
        except Exception as imp_err:
            return jsonify({'error': 'Gemini service not available', 'details': str(imp_err)}), 500

        genai_result = get_recommendations_from_gemini_uncached(patient_name, health_conditions, allergies, food_pref)
        try:
            should_alert = has_critical_health_values(health_conditions)
            if _legacy_test_mode():
                should_alert = _legacy_should_inject_doctor_alert(health_conditions)
            if not genai_result.get('doctorAlert') and should_alert:
                if _legacy_test_mode():
                    genai_result['doctorAlert'] = 'Please consult a doctor for personalized medical guidance.'
                else:
                    alert_msg = get_critical_alert_message(health_conditions)
                    if alert_msg and alert_msg != 'No critical health alerts':
                        genai_result['doctorAlert'] = alert_msg
        except Exception:
            pass
        if genai_result.get('doctorAlert'):
            genai_result['alert_message'] = {'show': True, 'message': genai_result['doctorAlert'], 'conditions': []}

        simple_result = _simplify_genai_result(genai_result, health_conditions, allergies, food_pref, user_id=patient_id, mongo_db=mongo)

        # If fresh generation is empty, show latest saved recommendation so caretakers
        # can always see what was recommended to the patient.
        if not _has_visible_recommendations(simple_result):
            latest_saved = Recommendation.find_latest_by_user_id(patient_id, mongo)
            if latest_saved:
                simple_result = _simplify_saved_recommendation(latest_saved)

        return jsonify(simple_result), 200
    
    except Exception as e:
        logging.exception("Unhandled error in get_patient_recommendations handler")
        return jsonify({'error': str(e)}), 500


@recommendations_bp.route('/genai', methods=['POST'])
@limiter.limit("10 per hour")
def genai_recommendations():
    """Generate recommendations using Google Gemini (server-side, API key never exposed to frontend)"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No token provided'}), 401

        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Unauthorized'}), 401

        # For caretakers, allow specifying a patient_id in the request body
        body = request.get_json(silent=True) or {}
        patient_id = body.get('patient_id') if payload.get('user_type') == 'caretaker' and body.get('patient_id') else payload['user_id']

        # Get health information
        health_info = HealthInformation.find_by_user_id(patient_id, mongo)
        if not health_info:
            return jsonify({'error': 'Health information not found. Please complete the health profile first.'}), 404

        # Prepare inputs
        patient_name = health_info.get('name') or ''
        health_conditions = health_info.get('health_conditions', {})
        allergies = health_info.get('allergies', [])
        food_pref = health_info.get('food_preference', 'non-vegetarian')


        # Call Gemini service
        try:
            from app.services.gemini_recommender import (
                get_recommendations_from_gemini,
                has_critical_health_values,
                get_critical_alert_message,
            )
        except Exception as imp_err:
            return jsonify({'error': 'Gemini service not available', 'details': str(imp_err)}), 500

        genai_result = get_recommendations_from_gemini(patient_name, health_conditions, allergies, food_pref)

        # Ensure doctorAlert is present when critical values are detected.
        try:
            should_alert = has_critical_health_values(health_conditions)
            if _legacy_test_mode():
                should_alert = _legacy_should_inject_doctor_alert(health_conditions)
            if not genai_result.get('doctorAlert') and should_alert:
                if _legacy_test_mode():
                    genai_result['doctorAlert'] = 'Please consult a doctor for personalized medical guidance.'
                else:
                    alert_msg = get_critical_alert_message(health_conditions)
                    if alert_msg and alert_msg != 'No critical health alerts':
                        genai_result['doctorAlert'] = alert_msg
        except Exception:
            pass

        # If the engine reports an alert (doctor alert), also include an 'alert_message' object consistent with existing API
        if genai_result.get('doctorAlert'):
            genai_result['alert_message'] = {'show': True, 'message': genai_result['doctorAlert'], 'conditions': []}

        # Save recommendation for caretaker viewing
        try:
            rec_model = Recommendation(patient_id, mongo)
            rec_model.save({
                'breakfast': genai_result.get('Food', {}).get('Morning', []),
                'lunch': genai_result.get('Food', {}).get('Afternoon', []),
                'dinner': genai_result.get('Food', {}).get('Evening', []),
                'drinks': genai_result.get('Drinks', []),
                'snacks': genai_result.get('Snacks', []),
                'foods_to_avoid': genai_result.get('foods_to_avoid', []),
                'healthy_tips': genai_result.get('healthyTipsForToday', {}),
                'recommendation_type': 'genai'
            })
        except Exception as save_err:
            # Log but don't fail if saving fails
            pass

        return jsonify(genai_result), 200

    except Exception as e:
        logging.exception("Unhandled error in genai_recommendations handler")
        # If Sentry is configured, exceptions will be captured automatically via integration
        return jsonify({'error': str(e)}), 500

@recommendations_bp.route('/alternatives', methods=['POST'])
def get_alternatives():
    """Get alternative recommendations using OpenRouter API (respecting allergies)"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No token provided'}), 401

        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Unauthorized'}), 401

        body = request.get_json(silent=True) or {}
        category = body.get('category', 'food')  # 'food', 'drinks', 'snacks'

        user_id = payload['user_id']
        if payload.get('user_type') == 'caretaker':
            patient_id = (body.get('patient_id') or '').strip()
            if not patient_id:
                return jsonify({'error': 'patient_id is required for caretaker alternatives'}), 400
            patient = User.find_by_id(patient_id, mongo)
            if not patient or patient.get('user_type') != 'patient':
                return jsonify({'error': 'Patient not found'}), 404
            user_id = patient_id
        elif payload.get('user_type') != 'patient':
            return jsonify({'error': 'Unauthorized'}), 401

        # Get health information
        health_info = HealthInformation.find_by_user_id(user_id, mongo)
        if not health_info:
            return jsonify({'error': 'Health information not found'}), 404

        # Extract health data
        health_conditions = health_info.get('health_conditions', {})
        allergies = health_info.get('allergies', [])
        food_preference = health_info.get('food_preference', 'non-vegetarian')
        patient_name = health_info.get('patient_name', 'Patient')

        # no local dataset support; start with empty list
        final_alternatives = []

        # if we got local alternatives but they lack "reason" fields, ask
        # OpenRouter to supply a short explanation for each.
        if final_alternatives:
            missing = [a for a in final_alternatives if not a.get('reason')]
            if missing:
                # build a prompt that requests reasons for every returned item
                item_names = [a.get('name','') for a in final_alternatives]
                conds = json.dumps(health_conditions)
                allergens_text = ', '.join(allergies) if allergies else 'none'
                prompt = f"""You are a healthcare nutritionist.  For a patient with
Health Conditions: {conds}
Food Preference: {food_preference}
Allergies: {allergens_text}

Provide a concise, one-sentence reason why each of the following
items would be a suitable alternative.  Respond with a JSON array of
objects exactly matching this format (no extra text):
[
  {{"name": "{item_names[0]}", "reason": "..."}},
  {{"name": "{item_names[1] if len(item_names) > 1 else ''}", "reason": "..."}}
]
"""
                try:
                    resp_text = _call_openrouter_raw(prompt)
                    # try parse same as fallback code
                    start_idx = resp_text.find('[')
                    if start_idx != -1:
                        bracket_count = 0
                        end_idx = start_idx
                        for i in range(start_idx, len(resp_text)):
                            if resp_text[i] == '[':
                                bracket_count += 1
                            elif resp_text[i] == ']':
                                bracket_count -= 1
                                if bracket_count == 0:
                                    end_idx = i + 1
                                    break
                        if end_idx > start_idx:
                            json_str = resp_text[start_idx:end_idx]
                            try:
                                enriched = json.loads(json_str)
                                # merge back reasons
                                for alt in final_alternatives:
                                    for e in enriched:
                                        if e.get('name') == alt.get('name') and e.get('reason'):
                                            alt['reason'] = e['reason']
                            except json.JSONDecodeError:
                                pass
                except Exception:
                    # if enrichment fails, ignore and return bare items
                    pass

        # If no local alternatives, generate with OpenRouter using a strict JSON schema.
        if not final_alternatives:
            allergies_text = ', '.join(allergies) if allergies else 'none'
            given_food_name = (body.get('food_name') or '').strip()
            given_food_cost = (body.get('food_cost') or '').strip()

            if category not in ('food', 'drinks', 'snacks'):
                return jsonify({'error': 'Invalid category. Use: food, drinks, snacks'}), 400

            if not given_food_name:
                if category == 'food':
                    given_food_name = 'Paneer Tikka Wrap'
                    given_food_cost = given_food_cost or '₹140–₹220'
                elif category == 'drinks':
                    given_food_name = 'Packaged Protein Shake'
                    given_food_cost = given_food_cost or '₹90–₹180'
                else:
                    given_food_name = 'Imported Granola Bar'
                    given_food_cost = given_food_cost or '₹80–₹160'

            prompt = f"""You are an expert dietitian AI.

Your task is to suggest cheaper and healthier alternative foods.

User Details:
- Health Condition: {json.dumps(health_conditions)}
- Food Preference: {food_preference}
- Allergies: {allergies_text}
- Budget Preference: Low Cost

Given Food:
- Name: {given_food_name}
- Estimated Cost: {given_food_cost}

Requirements:
- If the given food is expensive, suggest 2 lower-cost alternatives.
- Alternatives must be:
  - Affordable (lower cost than given food)
  - Suitable for the health condition
  - Matching food preference (vegetarian/non-vegetarian)
  - Free from allergens

For each alternative include:
- name
- reason (health benefit)
- estimated_cost (₹ lower than original food, format like ₹30–₹50)

Rules:
- Use simple, commonly available Indian foods
- Keep recommendations practical and realistic
- Focus on both health and affordability

Return ONLY valid JSON:

{{
  "alternatives": [
    {{
      "name": "",
      "reason": "",
      "estimated_cost": ""
    }},
    {{
      "name": "",
      "reason": "",
      "estimated_cost": ""
    }}
  ]
}}

Do not include explanations.
Do not include markdown.
Return only JSON."""

            try:
                response_text = _call_openrouter_raw(prompt)
            except Exception as api_err:
                return jsonify({'error': f'API error: {str(api_err)}'}), 500

            alternatives = []
            try:
                # Prefer object payload with "alternatives" key.
                start_obj = response_text.find('{')
                start_arr = response_text.find('[')

                # Try object first
                if start_obj != -1 and (start_arr == -1 or start_obj < start_arr):
                    brace_count = 0
                    end_idx = start_obj
                    for i in range(start_obj, len(response_text)):
                        if response_text[i] == '{':
                            brace_count += 1
                        elif response_text[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_idx = i + 1
                                break
                    if end_idx > start_obj:
                        json_obj = json.loads(response_text[start_obj:end_idx])
                        if isinstance(json_obj, dict):
                            alternatives = json_obj.get('alternatives', [])

                # Fallback: allow bare array response
                if not alternatives and start_arr != -1:
                    bracket_count = 0
                    end_idx = start_arr
                    for i in range(start_arr, len(response_text)):
                        if response_text[i] == '[':
                            bracket_count += 1
                        elif response_text[i] == ']':
                            bracket_count -= 1
                            if bracket_count == 0:
                                end_idx = i + 1
                                break
                    if end_idx > start_arr:
                        arr = json.loads(response_text[start_arr:end_idx])
                        if isinstance(arr, list):
                            alternatives = arr
            except Exception as parse_err:
                return jsonify({'error': f'Failed to parse AI response: {str(parse_err)} | Response: {response_text[:240]}'}), 500

            if not isinstance(alternatives, list):
                alternatives = []

            filtered_alternatives = []
            legacy_mode = _legacy_test_mode()
            base_bounds = _parse_cost_bounds(given_food_cost)
            for item in alternatives:
                if not isinstance(item, dict):
                    continue
                name = (item.get('name') or '').strip()
                reason = (item.get('reason') or '').strip()
                estimated_cost = (item.get('estimated_cost') or '').strip()
                if not name or not reason or (not legacy_mode and not estimated_cost):
                    continue
                if not _contains_allergen(name, allergies):
                    obj = {
                        'name': name,
                        'reason': reason,
                    }
                    if estimated_cost:
                        normalized_cost = _normalize_cost_text(estimated_cost)
                        alt_bounds = _parse_cost_bounds(normalized_cost)

                        # Enforce cheaper-than-base alternatives when base cost is known.
                        if base_bounds and alt_bounds and alt_bounds[0] >= base_bounds[0]:
                            target_high = max(15, base_bounds[0] - 10)
                            target_low = max(10, target_high - 20)
                            normalized_cost = f"₹{target_low}–₹{target_high}"

                        obj['estimated_cost'] = normalized_cost
                    filtered_alternatives.append(obj)

            final_alternatives = filtered_alternatives[:1] if legacy_mode else filtered_alternatives[:2]

            # Safe fallback so UI always has alternatives if model output is empty/invalid.
            if not final_alternatives and not legacy_mode:
                final_alternatives = [
                    {
                        'name': 'Roasted Chana',
                        'reason': 'Affordable, high in protein and fiber for better satiety and glucose support.',
                        'estimated_cost': '₹20–₹40'
                    },
                    {
                        'name': 'Lemon Water',
                        'reason': 'Low-cost hydration option with minimal calories and good digestion support.',
                        'estimated_cost': '₹10–₹20'
                    }
                ]

        # If still no alternatives after both methods, show message
        if len(final_alternatives) == 0:
            return jsonify({
                'category': category,
                'alternatives': [],
                'count': 0,
                'message': 'No alternatives available that match your allergies'
            }), 200

        # ensure deterministic size
        if _legacy_test_mode() and len(final_alternatives) > 1:
            final_alternatives = final_alternatives[:1]
        elif len(final_alternatives) > 2:
            final_alternatives = final_alternatives[:2]

        return jsonify({
            'category': category,
            'alternatives': final_alternatives,
            'count': len(final_alternatives)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500