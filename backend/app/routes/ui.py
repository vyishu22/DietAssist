from flask import Blueprint, jsonify, render_template, request, redirect
import re
from datetime import datetime

from app import mongo
from app.models.models import HealthInformation, Recommendation
from app.routes.recommendations import _simplify_genai_result, _build_personalized_tips
from app.services.gemini_recommender import get_recommendations_from_gemini_uncached, get_critical_alert_message
from app.utils.auth_utils import verify_token


ui_bp = Blueprint('ui', __name__)


def _normalize_allergy_term(term: str) -> str:
    t = str(term or '').strip().lower()
    if t == 'diary':
        return 'dairy'
    return t


def _normalize_allergies(allergies):
    seen = set()
    out = []
    for a in allergies or []:
        n = _normalize_allergy_term(a)
        if not n or n in seen:
            continue
        seen.add(n)
        out.append(n)
    return out


def _normalize_cost_text(value: str) -> str:
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


def _compute_health_score(health_conditions: dict) -> int:
    score = 10
    try:
        if health_conditions.get('diabetes') and float(health_conditions.get('diabetes')) > 140:
            score -= 2
        if health_conditions.get('cholesterol'):
            chol = float(health_conditions.get('cholesterol'))
            if 180 <= chol <= 200:
                score -= 1
            elif chol > 200:
                score -= 2
        if health_conditions.get('obesity_bmi') and float(health_conditions.get('obesity_bmi')) >= 30:
            score -= 2
    except Exception:
        pass

    bp = str(health_conditions.get('blood_pressure') or '').strip()
    if bp:
        try:
            if '/' in bp:
                s, d = bp.split('/', 1)
                if float(s) >= 180 or float(d) >= 120:
                    score -= 3
                elif float(s) >= 140 or float(d) >= 90:
                    score -= 2
            else:
                if float(bp) >= 180:
                    score -= 3
                elif float(bp) >= 140:
                    score -= 2
        except Exception:
            pass

    return max(1, min(10, score))


def _critical_bp_alert(health_conditions: dict) -> str:
    bp = str(health_conditions.get('blood_pressure') or '').strip()
    if not bp:
        return ''
    try:
        if '/' in bp:
            s, d = bp.split('/', 1)
            if float(s) >= 180 or float(d) >= 120:
                return 'Critical Alert: Your blood pressure is extremely high. Please consult a doctor immediately.'
        else:
            if float(bp) >= 180:
                return 'Critical Alert: Your blood pressure is extremely high. Please consult a doctor immediately.'
    except Exception:
        return ''
    return ''


def _fallback_health_issue_analysis(health_conditions: dict) -> str:
    """Fallback text if OpenRouter health analysis call fails."""
    parts = []
    bp = str(health_conditions.get('blood_pressure') or '').strip()
    if bp:
        try:
            if '/' in bp:
                s, d = bp.split('/', 1)
                systolic = float(s)
                diastolic = float(d)
                if systolic >= 180 or diastolic >= 120:
                    parts.append(
                        "⚠️ Issues You MUST Fix\n\n"
                        "🔴 1. Blood Pressure Issue (Major Issue)\n"
                        f"{bp} mmHg\n\n"
                        "❌ Explanation\n\n"
                        "Normal: 120/80 mmHg\n"
                        f"Your Value: {bp} mmHg\n"
                        "Severity: 🔴 Critical\n\n"
                        "👉 Why this is dangerous\n"
                        "This can indicate hypertensive crisis and risk of stroke or heart complications.\n\n"
                        "✅ Fix:\n"
                        "Avoid high salt immediately, rest, and seek emergency medical review.\n\n"
                        "⚠️ Critical Alert:\n"
                        "Your blood pressure is extremely high. Please consult a doctor immediately."
                    )
        except Exception:
            pass
    return "\n\n---\n\n".join(parts)


def _normalize_item_list(items):
    normalized = []
    for item in items or []:
        if isinstance(item, str):
            normalized.append({'name': item, 'reason': '', 'estimated_cost': ''})
        elif isinstance(item, dict):
            normalized.append({
                'name': item.get('name', ''),
                'reason': item.get('reason', ''),
                'estimated_cost': _normalize_cost_text(item.get('estimated_cost', ''))
            })
    return normalized


def _tips_to_list(tips_data):
    tips = []
    if isinstance(tips_data, dict):
        if tips_data.get('hydration'):
            tips.append({'icon': '💧', 'text': tips_data['hydration']})
        if tips_data.get('exercise'):
            tips.append({'icon': '🏃', 'text': tips_data['exercise']})
        if tips_data.get('sleep'):
            tips.append({'icon': '😴', 'text': tips_data['sleep']})
        if tips_data.get('specific'):
            tips.append({'icon': '⚕️', 'text': tips_data['specific']})
    elif isinstance(tips_data, list):
        for tip in tips_data:
            value = str(tip).strip()
            if value:
                tips.append({'icon': '⚕️', 'text': value})
    return tips


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
        'healthyTipsForToday': latest_rec.get('healthy_tips', {}),
    }


def _format_last_updated(dt):
    if not dt:
        return 'Unknown'
    if isinstance(dt, datetime):
        return dt.strftime('%d %B %Y, %I:%M %p UTC')
    return str(dt)


def _wants_html_response() -> bool:
    accept = (request.headers.get('Accept') or '').lower()
    return 'text/html' in accept or '*/*' in accept


@ui_bp.route('/recommendations', methods=['GET'])
def recommendations_page():
    token = request.args.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        if _wants_html_response():
            return redirect('/')
        return jsonify({'error': 'No token provided'}), 401

    payload = verify_token(token)
    if not payload or payload.get('user_type') != 'patient':
        if _wants_html_response():
            return redirect('/')
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = payload['user_id']
    health_info = HealthInformation.find_by_user_id(user_id, mongo)
    if not health_info:
        return jsonify({'error': 'Health information not found. Please complete your health profile first.'}), 404

    patient_name = health_info.get('name') or ''
    health_conditions = health_info.get('health_conditions', {})
    allergies = _normalize_allergies(health_info.get('allergies', []))
    food_pref = health_info.get('food_preference', 'non-vegetarian')

    regenerate = str(request.args.get('regenerate', '')).strip().lower() in ('1', 'true', 'yes')
    latest_saved = Recommendation.find_latest_by_user_id(user_id, mongo)
    generated_at = latest_saved.get('created_at') if latest_saved else None

    if latest_saved and not regenerate:
        simple = _simplify_saved_recommendation(latest_saved)
    else:
        genai_result = get_recommendations_from_gemini_uncached(patient_name, health_conditions, allergies, food_pref)
        simple = _simplify_genai_result(genai_result, health_conditions, allergies, food_pref)

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

        latest_saved = Recommendation.find_latest_by_user_id(user_id, mongo)
        generated_at = latest_saved.get('created_at') if latest_saved else generated_at

    food = simple.get('Food', {})
    drinks = _normalize_item_list(simple.get('Drinks', []))
    snacks = _normalize_item_list(simple.get('Snacks', []))
    foods_to_avoid = _normalize_item_list(simple.get('foods_to_avoid', []))
    tips = _tips_to_list(simple.get('healthyTipsForToday', {}))
    if not tips:
        fallback_tips = _build_personalized_tips(health_conditions, allergies, food_pref)
        tips = _tips_to_list(fallback_tips)

    allergy_messages = [
        f"Allergy alert: foods containing {allergy} are excluded from your plan."
        for allergy in allergies
    ]
    if not allergy_messages:
        allergy_messages = ['No allergy restrictions found in your profile.']

    critical_alert = ''
    try:
        critical_msg = get_critical_alert_message(health_conditions)
        if critical_msg and critical_msg != 'No critical health alerts':
            critical_alert = critical_msg
    except Exception:
        critical_alert = _critical_bp_alert(health_conditions)

    health_issue_analysis = critical_alert or _fallback_health_issue_analysis(health_conditions)

    health_score = _compute_health_score(health_conditions)
    health_score_stars = '★' * health_score + '☆' * (10 - health_score)

    return render_template(
        'recommendations.html',
        token=token,
        patient_name=patient_name,
        food_morning=_normalize_item_list(food.get('morning', [])),
        food_afternoon=_normalize_item_list(food.get('afternoon', [])),
        food_evening=_normalize_item_list(food.get('evening', [])),
        drinks=drinks,
        snacks=snacks,
        foods_to_avoid=foods_to_avoid,
        tips=tips,
        allergy_messages=allergy_messages,
        health_conditions=health_conditions,
        food_preference=food_pref,
        allergies=allergies,
        critical_alert=critical_alert,
        health_issue_analysis=health_issue_analysis,
        health_score=health_score,
        health_score_stars=health_score_stars,
        recommendation_last_updated=_format_last_updated(generated_at),
    )