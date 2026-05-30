"""
Gemini Recommender Service
Integrates with Google Gemini (gemini-1.5-flash) to generate structured diet recommendations.

- Uses the official `google-generativeai` Python SDK.
- Expects GEMINI_API_KEY in environment (loaded via dotenv in app factory).
- Returns a validated JSON structure matching the app's display format.

Note: The API key must never be sent to the frontend.
"""
import os
import json
import re
import logging
from typing import Dict, Any, List

# configure simple logging for debugging
logging.basicConfig(level=logging.DEBUG)

# OpenRouter HTTP-based integration (the system now uses OpenRouter exclusively).
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_API_URL = os.getenv('OPENROUTER_API_URL', 'https://api.openrouter.ai/v1/chat/completions')
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'gpt-4o-mini')

# Safe thresholds used to detect multiple-alert conditions
SAFE_THRESHOLDS = {
    'diabetes': 100,  # mg/dL fasting glucose
    'blood_pressure_systolic': 120,
    'blood_pressure_diastolic': 80,
    'cholesterol': 200,
    'obesity_bmi': 25
}

NON_VEG_KEYWORDS = {
    'chicken', 'mutton', 'lamb', 'fish', 'salmon', 'tuna', 'sardine', 'egg',
    'prawn', 'shrimp', 'beef', 'pork', 'turkey', 'anchovy', 'crab'
}

ALLERGY_ALIASES = {
    'diary': 'dairy',
    'milk products': 'dairy',
    'milk product': 'dairy',
    'lactose': 'dairy',
    'lactose intolerance': 'dairy',
}

ALLERGEN_KEYWORDS = {
    'dairy': {
        'milk', 'cheese', 'butter', 'paneer', 'curd', 'yogurt', 'yoghurt',
        'ghee', 'cream', 'lassi', 'kheer', 'custard', 'ice cream', 'buttermilk'
    },
    'nuts': {'almond', 'cashew', 'walnut', 'pistachio', 'peanut', 'hazelnut'},
    'egg': {'egg', 'mayonnaise'},
}

DRINK_KEYWORDS = {
    'tea', 'water', 'juice', 'lassi', 'milkshake', 'smoothie', 'soup',
    'coffee', 'buttermilk', 'sharbat', 'coconut water', 'drink', 'lemon water'
}

SNACK_KEYWORDS = {
    'chaat', 'salad', 'sprouts', 'chana', 'nuts', 'seeds', 'bar', 'sandwich',
    'murmura', 'makhana', 'cracker', 'bhel', 'fruit bowl', 'fruit chaat'
}

SECTION_FALLBACKS = {
    'Morning': [
        {'name': 'Vegetable Poha with Peanuts', 'reason': 'Balanced carbs and fiber support stable morning energy.', 'estimated_cost': '₹25–₹45'},
        {'name': 'Moong Dal Chilla with Mint Chutney', 'reason': 'Protein-rich breakfast helps satiety and glucose control.', 'estimated_cost': '₹35–₹60'},
    ],
    'Afternoon': [
        {'name': 'Rajma Brown Rice Bowl', 'reason': 'High-fiber legumes and whole grains improve fullness and glycemic response.', 'estimated_cost': '₹80–₹130'},
        {'name': 'Palak Dal with 2 Phulkas', 'reason': 'Iron-rich greens and lentils give nutrient-dense mid-day nutrition.', 'estimated_cost': '₹70–₹120'},
    ],
    'Evening': [
        {'name': 'Vegetable Khichdi with Curd', 'reason': 'Light, gut-friendly dinner that is easy to digest at night.', 'estimated_cost': '₹75–₹130'},
        {'name': 'Tofu Stir-Fry with Millet Roti', 'reason': 'Lean protein and low-glycemic grains support metabolic health.', 'estimated_cost': '₹90–₹160'},
    ],
    'Drinks': [
        {'name': 'Jeera Buttermilk', 'reason': 'Hydrating, low-cost option with digestive support.', 'estimated_cost': '₹15–₹30'},
        {'name': 'Unsweetened Lemon Water', 'reason': 'Low-calorie hydration without sugar spikes.', 'estimated_cost': '₹10–₹20'},
    ],
    'Snacks': [
        {'name': 'Roasted Chana', 'reason': 'Affordable high-fiber snack with sustained energy release.', 'estimated_cost': '₹20–₹40'},
        {'name': 'Sprouts Chaat', 'reason': 'Protein-rich snack with micronutrients and low added fat.', 'estimated_cost': '₹25–₹50'},
    ],
}

REASON_VARIATIONS = [
    'Also supports portion control and steadier post-meal energy.',
    'Its fiber-protein balance can reduce sudden hunger spikes later in the day.',
    'This option is practical for Indian kitchens and easy to repeat consistently.',
    'It is nutrient-dense while keeping daily meal costs manageable.',
]

SMART_HEALTH_TIPS = {
    'diabetes': [
        'Avoid sugar-rich foods and sweetened beverages.',
        'Prefer low-glycemic foods and include high-fiber meals.',
    ],
    'cholesterol': [
        'Avoid deep-fried and high saturated-fat foods.',
        'Include omega-3 and soluble-fiber foods such as fish, oats, and legumes.',
    ],
    'blood_pressure': [
        'Reduce daily salt intake and avoid packaged salty snacks.',
        'Increase potassium-rich foods such as spinach, banana, and cucumber.',
    ],
    'obesity_bmi': [
        'Use portion control and avoid calorie-dense fried foods.',
        'Increase lean protein and fiber to improve satiety.',
    ],
}


def _parse_cost_bounds(value: Any) -> tuple[int, int] | None:
    text = str(value or '').strip()
    if not text:
        return None

    nums = re.findall(r'\d+', text)
    if not nums:
        return None

    if len(nums) == 1:
        low = int(nums[0])
        high = low + 20
    else:
        low = int(nums[0])
        high = int(nums[1])

    # Repair common split/token artifacts like 1-50, 3-50, 5-00.
    if low < 10 and high >= 30:
        low *= 10
    if high < 10 and low >= 30:
        high *= 10
    if high == 0 and low > 0:
        high = low * 10

    if low > high:
        low, high = high, low

    return max(5, low), max(10, high)


def _cost_floor_for_item(name: str, section: str) -> tuple[int, int]:
    n = (name or '').lower()
    section = section or ''

    if any(k in n for k in ('fish', 'salmon', 'tuna', 'prawn', 'shrimp')):
        return 150, 300
    if any(k in n for k in ('chicken', 'egg', 'turkey')):
        return 100, 220
    if any(k in n for k in ('paneer', 'tofu')):
        return 90, 180
    if section in ('Drinks',):
        return 10, 60
    if section in ('Snacks',):
        return 20, 90
    if section in ('Morning', 'Breakfast'):
        return 20, 80
    if section in ('Afternoon', 'Lunch'):
        return 70, 180
    if section in ('Evening', 'Dinner'):
        return 80, 200
    return 20, 80


def _normalize_allergy_term(term: Any) -> str:
    t = str(term or '').strip().lower()
    t = re.sub(r'\s+', ' ', t)
    return ALLERGY_ALIASES.get(t, t)


def _normalize_allergies(allergies: List[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for allergy in allergies or []:
        a = _normalize_allergy_term(allergy)
        if not a or a in seen:
            continue
        seen.add(a)
        out.append(a)
    return out


def _item_has_allergy_risk(name: str, allergies: List[str]) -> bool:
    n = (name or '').lower()
    for allergy in allergies or []:
        a = _normalize_allergy_term(allergy)
        if not a:
            continue
        if a in n:
            return True
        for keyword in ALLERGEN_KEYWORDS.get(a, set()):
            if keyword in n:
                return True
    return False


def _normalize_item_cost(item: Dict[str, Any], section: str) -> Dict[str, Any]:
    obj = dict(item)
    bounds = _parse_cost_bounds(obj.get('estimated_cost', ''))
    floor_low, floor_high = _cost_floor_for_item(obj.get('name', ''), section)

    if bounds is None:
        low, high = floor_low, floor_high
    else:
        low, high = bounds
        low = max(low, floor_low)
        high = max(high, floor_high if high < floor_low else high)

    if high <= low:
        high = low + 20

    obj['estimated_cost'] = f'₹{low}–₹{high}'
    return obj


def _is_non_veg(name: str) -> bool:
    n = (name or '').lower()
    return any(k in n for k in NON_VEG_KEYWORDS)


def _ensure_list_of_items(items: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(items, list):
        return out
    for it in items:
        if isinstance(it, dict):
            out.append({
                'name': str(it.get('name', '')).strip(),
                'reason': str(it.get('reason', '')).strip(),
                'estimated_cost': str(it.get('estimated_cost', '')).strip(),
            })
    return out


def _pick_fallback(section: str, used_names: set[str], allergies: List[str] | None = None, pref: str = '') -> Dict[str, Any]:
    options = SECTION_FALLBACKS.get(section, SECTION_FALLBACKS['Snacks'])
    for opt in options:
        key = opt['name'].strip().lower()
        if pref == 'vegetarian' and _is_non_veg(opt.get('name', '')):
            continue
        if _item_has_allergy_risk(opt.get('name', ''), allergies or []):
            continue
        if key not in used_names:
            return dict(opt)
    return {'name': 'Seasonal Vegetable Bowl', 'reason': 'Balanced and allergy-safe fallback meal.', 'estimated_cost': '₹40–₹80'}


def _enforce_variety(items: List[Dict[str, Any]], section: str, used_names: set[str], allergies: List[str] | None = None, pref: str = '') -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for it in items:
        name_key = (it.get('name') or '').strip().lower()
        invalid = (
            not name_key
            or name_key in used_names
            or (pref == 'vegetarian' and _is_non_veg(it.get('name', '')))
            or _item_has_allergy_risk(it.get('name', ''), allergies or [])
        )
        if invalid:
            it = _pick_fallback(section, used_names, allergies, pref)
            name_key = it['name'].strip().lower()
        used_names.add(name_key)
        output.append(it)
    if not output:
        fallback = _pick_fallback(section, used_names, allergies, pref)
        used_names.add(fallback['name'].strip().lower())
        output.append(fallback)
    return output


def _reason_from_name(name: str) -> str:
    n = (name or '').lower()
    if any(k in n for k in ('oats', 'dal', 'chana', 'rajma', 'millet', 'sprouts', 'vegetable')):
        return 'High fiber profile may reduce LDL response and improve satiety.'
    if any(k in n for k in ('fish', 'salmon', 'tuna')):
        return 'Omega-3 fats can support a healthier HDL/LDL balance and reduce inflammation.'
    if any(k in n for k in ('green tea', 'berries', 'citrus', 'spinach', 'broccoli')):
        return 'Rich antioxidants may help lower oxidative stress and support vascular health.'
    if any(k in n for k in ('curd', 'yogurt', 'probiotic')):
        return 'Gut-friendly nutrients can improve digestion and meal tolerance.'
    return 'Balanced macros support steadier energy and better day-long hunger control.'


def _diversify_reasons(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[str] = set()
    out: List[Dict[str, Any]] = []
    for idx, it in enumerate(items):
        obj = dict(it)
        reason = (obj.get('reason') or '').strip()
        reason_key = reason.lower()
        needs_variation = (
            not reason
            or reason_key in seen
            or 'low glycemic' in reason_key
            or 'manage blood sugar' in reason_key
        )
        if needs_variation:
            base = reason if reason else _reason_from_name(obj.get('name', ''))
            suffix = REASON_VARIATIONS[idx % len(REASON_VARIATIONS)]
            obj['reason'] = f'{base} {suffix}'.strip()
        seen.add((obj.get('reason') or '').strip().lower())
        out.append(obj)
    return out


def _count_non_empty_tips(tips_obj: Dict[str, Any]) -> int:
    if not isinstance(tips_obj, dict):
        return 0
    count = 0
    for value in tips_obj.values():
        if isinstance(value, str) and value.strip():
            count += 1
    return count


def _build_smart_health_tips(health_conditions: Dict[str, Any], allergies: List[str], food_preference: str) -> Dict[str, str]:
    tips: Dict[str, str] = {
        'hydration': 'Drink adequate water through the day and avoid sugary drinks.',
        'specific': '',
    }

    specific: List[str] = []
    for key in ('diabetes', 'cholesterol', 'blood_pressure', 'obesity_bmi'):
        if health_conditions.get(key):
            specific.extend(SMART_HEALTH_TIPS.get(key, []))

    if (food_preference or '').strip().lower() == 'vegetarian':
        specific.append('Use dal, chana, rajma, soy chunks, paneer, or tofu for protein.')
    else:
        specific.append('Prefer lean proteins such as eggs, fish, and skinless chicken.')

    if allergies:
        normalized = [str(a).strip() for a in allergies if str(a).strip()]
        if normalized:
            specific.append('Strictly avoid allergen foods: ' + ', '.join(normalized) + '.')

    seen: set[str] = set()
    unique_specific: List[str] = []
    for item in specific:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique_specific.append(item)

    tips['specific'] = ' '.join(unique_specific[:4])
    return tips


def _ensure_health_tips_present(data: Dict[str, Any], health_conditions: Dict[str, Any], allergies: List[str], food_preference: str) -> None:
    tips = data.get('healthyTipsForToday', {})
    if isinstance(tips, str):
        tips = {'specific': tips.strip()} if tips.strip() else {}
    if tips is None or not isinstance(tips, dict):
        tips = {}

    # Ensure at least 2 non-empty tip fields.
    if _count_non_empty_tips(tips) < 2:
        fallback = _build_smart_health_tips(health_conditions or {}, allergies or [], food_preference or '')
        merged = dict(fallback)
        merged.update({k: v for k, v in tips.items() if isinstance(v, str) and v.strip()})
        tips = merged

    if _count_non_empty_tips(tips) < 2:
        tips.setdefault('exercise', 'Do 25-30 minutes of light physical activity today.')

    data['healthyTipsForToday'] = tips


def _ensure_foods_to_avoid(data: Dict[str, Any], health_conditions: Dict[str, Any], allergies: List[str]) -> None:
    avoid = _ensure_list_of_items(data.get('foods_to_avoid', []))
    by_name = {(i.get('name') or '').strip().lower() for i in avoid}

    def add_item(name: str, reason: str):
        key = name.strip().lower()
        if key in by_name:
            return
        by_name.add(key)
        avoid.append({'name': name, 'reason': reason})

    if health_conditions.get('diabetes'):
        add_item('Sugary drinks', 'Rapid sugar spikes can worsen glucose control.')
        add_item('Sweets and desserts', 'High refined sugar load can increase post-meal glucose.')
        add_item('Refined flour snacks', 'Low-fiber refined carbs can raise blood sugar quickly.')
    if health_conditions.get('blood_pressure'):
        add_item('Packaged salty snacks', 'High sodium can aggravate blood pressure.')
    if health_conditions.get('cholesterol'):
        add_item('Deep-fried foods', 'Often high in unhealthy fats affecting lipid profile.')
    for allergy in allergies or []:
        if allergy == 'dairy':
            add_item('Milk, Cheese, Butter, Paneer (dairy products)', 'Must be avoided due to dairy allergy risk.')
        else:
            add_item(f'Foods containing {allergy}', f'Must be avoided due to {allergy} allergy risk.')

    if len(avoid) < 3:
        add_item('Sugary beverages', 'Excess sugar intake worsens metabolic risk.')
        add_item('Deep-fried fast food', 'High fat and calories can worsen cardiometabolic health.')
        add_item('Processed refined carbs', 'Low fiber and high glycemic impact are not suitable daily.')

    data['foods_to_avoid'] = avoid[:5]


def _enforce_alternative_budget(data: Dict[str, Any]) -> None:
    food = data.get('Food', {}) if isinstance(data.get('Food'), dict) else {}
    alts = data.get('Alternatives', {}) if isinstance(data.get('Alternatives'), dict) else {}

    meal_map = {
        'Breakfast': 'Morning',
        'Lunch': 'Afternoon',
        'Dinner': 'Evening',
    }

    for alt_key, main_key in meal_map.items():
        main_items = _ensure_list_of_items(food.get(main_key, []))
        alt_items = _ensure_list_of_items(alts.get(alt_key, []))
        if not alt_items:
            continue

        main_bounds = [_parse_cost_bounds(i.get('estimated_cost', '')) for i in main_items]
        main_bounds = [b for b in main_bounds if b]
        if not main_bounds:
            continue

        main_low = min(b[0] for b in main_bounds)
        target_high = max(15, main_low - 10)
        target_low = max(10, target_high - 20)

        normalized = []
        for it in alt_items:
            obj = _normalize_item_cost(it, alt_key)
            low, high = _parse_cost_bounds(obj.get('estimated_cost', '')) or (target_low, target_high)
            if low >= main_low:
                obj['estimated_cost'] = f'₹{target_low}–₹{target_high}'
            normalized.append(obj)
        alts[alt_key] = normalized

    data['Alternatives'] = alts


def _rebalance_drinks_and_snacks(data: Dict[str, Any]) -> None:
    drinks = _ensure_list_of_items(data.get('Drinks', []))
    snacks = _ensure_list_of_items(data.get('Snacks', []))

    moved_to_drinks: List[Dict[str, Any]] = []
    kept_snacks: List[Dict[str, Any]] = []
    for item in snacks:
        n = (item.get('name') or '').lower()
        if any(k in n for k in DRINK_KEYWORDS):
            moved_to_drinks.append(item)
        else:
            kept_snacks.append(item)

    moved_to_snacks: List[Dict[str, Any]] = []
    kept_drinks: List[Dict[str, Any]] = []
    for item in drinks:
        n = (item.get('name') or '').lower()
        if any(k in n for k in SNACK_KEYWORDS):
            moved_to_snacks.append(item)
        else:
            kept_drinks.append(item)

    data['Drinks'] = kept_drinks + moved_to_drinks
    data['Snacks'] = kept_snacks + moved_to_snacks


def _post_process_recommendations(
    data: Dict[str, Any],
    health_conditions: Dict[str, Any],
    allergies: List[str],
    food_preference: str,
) -> Dict[str, Any]:
    pref = (food_preference or '').strip().lower()
    normalized_allergies = _normalize_allergies(allergies)
    food = data.get('Food', {}) if isinstance(data.get('Food'), dict) else {}
    alts = data.get('Alternatives', {}) if isinstance(data.get('Alternatives'), dict) else {}

    # Dynamic allergy messaging
    if normalized_allergies:
        data['allergyAlert'] = f"foods containing {', '.join(normalized_allergies)} are excluded from your plan."
    else:
        data['allergyAlert'] = 'No allergy restrictions found in your profile.'

    used_food_names: set[str] = set()
    for section in ('Morning', 'Afternoon', 'Evening'):
        items = _ensure_list_of_items(food.get(section, []))
        items = [it for it in items if not _item_has_allergy_risk(it.get('name', ''), normalized_allergies)]
        items = _enforce_variety(items, section, used_food_names, normalized_allergies, pref)
        items = [_normalize_item_cost(it, section) for it in items]
        food[section] = _diversify_reasons(items)

    used_misc_names: set[str] = set()
    for section in ('Drinks', 'Snacks'):
        items = _ensure_list_of_items(data.get(section, []))
        items = [it for it in items if not _item_has_allergy_risk(it.get('name', ''), normalized_allergies)]
        items = _enforce_variety(items, section, used_misc_names, normalized_allergies, pref)
        data[section] = _diversify_reasons([_normalize_item_cost(it, section) for it in items])

    # Keep alternative sections complete and preference-compliant.
    alt_map = {
        'Breakfast': 'Morning',
        'Lunch': 'Afternoon',
        'Dinner': 'Evening',
        'Drinks': 'Drinks',
        'Snacks': 'Snacks',
    }
    for alt_section, main_section in alt_map.items():
        items = _ensure_list_of_items(alts.get(alt_section, []))
        items = [it for it in items if not _item_has_allergy_risk(it.get('name', ''), normalized_allergies)]
        if not items:
            items = [_pick_fallback(main_section if main_section in SECTION_FALLBACKS else 'Snacks', set(), normalized_allergies, pref)]
        alts[alt_section] = _diversify_reasons([_normalize_item_cost(it, alt_section) for it in items])

    data['Food'] = food
    data['Alternatives'] = alts
    _rebalance_drinks_and_snacks(data)
    _ensure_foods_to_avoid(data, health_conditions, normalized_allergies)
    _enforce_alternative_budget(data)
    return data

# MODEL constant is no longer used (OpenRouter model is configured via `OPENROUTER_MODEL`).

# Simple in-memory TTL cache for GenAI responses to reduce repeated calls
try:
    from cachetools import TTLCache, cached
    _CACHE = TTLCache(maxsize=1024, ttl=3600)  # 1 hour TTL
except Exception:
    _CACHE = None


def _legacy_test_mode() -> bool:
    """Enable legacy behavior for automated tests or explicit opt-in."""
    if os.getenv('LEGACY_TEST_COMPAT', '').lower() in ('1', 'true', 'yes'):
        return True
    return 'PYTEST_CURRENT_TEST' in os.environ


def _cache_key(patient_name: str, health_conditions: Dict[str, Any], allergies: List[str], food_preference: str):
    """Generate a stable cache key for inputs"""
    # Sort health_conditions items to ensure deterministic keys
    hc_items = sorted([(k, str(health_conditions[k])) for k in health_conditions]) if health_conditions else []
    allergies_sorted = sorted(allergies) if allergies else []
    key = json.dumps({
        'patient': patient_name,
        'conditions': hc_items,
        'allergies': allergies_sorted,
        'pref': food_preference
    }, sort_keys=True)
    return key


def _count_alert_conditions(health_conditions: Dict[str, Any]) -> int:
    """Count how many conditions exceed safe thresholds."""
    count = 0

    if health_conditions.get('diabetes'):
        try:
            if float(health_conditions['diabetes']) > SAFE_THRESHOLDS['diabetes']:
                count += 1
        except Exception:
            pass

    if health_conditions.get('blood_pressure'):
        try:
            bp = health_conditions['blood_pressure'].split('/')
            systolic = float(bp[0]) if len(bp) > 0 else 0
            diastolic = float(bp[1]) if len(bp) > 1 else 0
            if systolic > SAFE_THRESHOLDS['blood_pressure_systolic'] or diastolic > SAFE_THRESHOLDS['blood_pressure_diastolic']:
                count += 1
        except Exception:
            pass

    if health_conditions.get('cholesterol'):
        try:
            if float(health_conditions['cholesterol']) > SAFE_THRESHOLDS['cholesterol']:
                count += 1
        except Exception:
            pass

    if health_conditions.get('obesity_bmi'):
        try:
            if float(health_conditions['obesity_bmi']) > SAFE_THRESHOLDS['obesity_bmi']:
                count += 1
        except Exception:
            pass

    return count


def _build_prompt(patient_name: str, health_conditions: Dict[str, Any], allergies: List[str], food_preference: str) -> str:
    """Create OpenRouter prompt aligned with patient-page sections."""
    allergies_text = ", ".join(allergies) if allergies else "none"

    # Format health values as readable key-value pairs.
    health_values = ", ".join([f"{k}: {v}" for k, v in health_conditions.items()]) if health_conditions else "normal"

    profile_rules = []
    if health_conditions.get('diabetes'):
        profile_rules.append("Diabetes-focused: use low glycemic meals, high fiber grains (millets/oats/barley), avoid high-sugar fruit combinations.")
    if health_conditions.get('blood_pressure'):
        profile_rules.append("Blood-pressure-focused: low sodium meals, avoid processed/salty foods, include potassium-rich ingredients.")
    if health_conditions.get('cholesterol'):
        profile_rules.append("Cholesterol-focused: prefer soluble fiber and unsaturated fats; avoid deep-fried and high saturated-fat options.")
    if health_conditions.get('obesity_bmi'):
        profile_rules.append("Weight-focused: low calorie density, high protein + high fiber meals, avoid calorie-dense preparations.")
    if not profile_rules:
        profile_rules.append("General preventive wellness focus with balanced macro distribution and budget-friendly choices.")

    profile_rules_text = "\n- " + "\n- ".join(profile_rules)

    prompt = f"""You are a diet recommendation assistant.

Generate personalized diet recommendations in the same section order used by the patient recommendation page.

User Data:
- Name: {patient_name}
- Health Conditions: {health_values}
- Allergies: {allergies_text}
- Food Preference: {food_preference}

STRICT RULES:
- Include ALL sections with at least one item per section.
- Include estimated_cost for every recommendation item.
- Include reason for every recommendation item.
- estimated_cost must be a realistic Indian rupee range in this format only: ₹30–₹50.
- Do not omit sections.
- Do not return placeholder text such as "No recommendations available".
- If profile constraints are strict, still generate the safest available alternatives.
- healthyTipsForToday must be personalized to the given health condition and allergies, not generic.
- Include at least 2 health tips in healthyTipsForToday (MANDATORY).
- Do not skip health tips.
- Must reflect these profile-specific requirements:{profile_rules_text}
- Avoid repeating this generic combo unless medically unavoidable: Oats Porridge with Fruits + Grilled Chicken Salad + Baked Fish.
- Ensure meal names differ meaningfully when health profile differs.
- Do not repeat the same food across Breakfast, Lunch, and Dinner.
- If Food Preference is vegetarian, do not include any non-vegetarian item in meals or alternatives.
- foods_to_avoid must include at least 3 items for metabolic conditions.
- Keep alternatives cheaper than corresponding main meals.
- Use different health reasoning phrasing per item; avoid repeating identical reason sentences.

Return ONLY valid JSON in this exact schema:

{{
  "allergyAlert": "foods containing {allergies_text} are excluded from your plan.",
  "Food": {{
    "Morning": [{{"name": "", "reason": "", "estimated_cost": ""}}],
    "Afternoon": [{{"name": "", "reason": "", "estimated_cost": ""}}],
    "Evening": [{{"name": "", "reason": "", "estimated_cost": ""}}]
  }},
  "foods_to_avoid": [{{"name": "", "reason": ""}}],
  "Alternatives": {{
    "Breakfast": [{{"name": "", "reason": "", "estimated_cost": ""}}],
    "Lunch": [{{"name": "", "reason": "", "estimated_cost": ""}}],
    "Dinner": [{{"name": "", "reason": "", "estimated_cost": ""}}],
    "Drinks": [{{"name": "", "reason": "", "estimated_cost": ""}}],
    "Snacks": [{{"name": "", "reason": "", "estimated_cost": ""}}]
  }},
  "Drinks": [{{"name": "", "reason": "", "estimated_cost": ""}}],
  "Snacks": [{{"name": "", "reason": "", "estimated_cost": ""}}],
  "alternativeMessage": "Alternative food options are available.",
    "healthyTipsForToday": {{
        "hydration": "",
        "specific": ""
    }}
}}

Do not include explanations.
Do not include markdown.
Return only JSON."""
    return prompt


def _parse_bp(bp_value: Any) -> tuple[float, float]:
    """Parse BP in systolic/diastolic format; return (0.0, 0.0) on failure."""
    try:
        parts = str(bp_value).split('/')
        systolic = float(parts[0].strip()) if len(parts) > 0 else 0.0
        diastolic = float(parts[1].strip()) if len(parts) > 1 else 0.0
        return systolic, diastolic
    except Exception:
        return 0.0, 0.0


def has_critical_health_values(health_conditions: Dict[str, Any]) -> bool:
    """Return True if any value is above normal range."""
    glucose = 0.0
    cholesterol = 0.0
    bmi = 0.0
    try:
        glucose = float(health_conditions.get('diabetes', 0) or 0)
    except Exception:
        pass
    try:
        cholesterol = float(health_conditions.get('cholesterol', 0) or 0)
    except Exception:
        pass
    try:
        bmi = float(health_conditions.get('obesity_bmi', 0) or 0)
    except Exception:
        pass

    systolic, diastolic = _parse_bp(health_conditions.get('blood_pressure', '0/0'))

    return (
        systolic > 120
        or diastolic > 80
        or glucose >= 100
        or cholesterol >= 200
        or bmi >= 25
    )


def _build_critical_alert_prompt(glucose: str, bp: str, cholesterol: str, bmi: str) -> str:
    """Build short-alert-only prompt for critical conditions."""
    return f"""You are a medical assistant AI.

Analyze the user's health values and generate ONLY a short alert message if any value is critical.

User Health Data:
- Diabetes (Fasting Glucose): {glucose}
- Blood Pressure: {bp}
- Cholesterol: {cholesterol}
- BMI: {bmi}

Rules:
- If any value is CRITICAL, return ONE short alert message
- Keep it very concise (1-2 lines)
- No explanation, no list, no formatting
- If all values are normal, return: "No critical health alerts"

Example outputs:

Critical Alert: Your blood sugar is dangerously high. Please consult a doctor immediately.

Critical Alert: Your blood pressure is extremely high. Seek medical attention immediately."""


def get_critical_alert_message(health_conditions: Dict[str, Any]) -> str:
    """Get a concise alert message listing all values above normal."""
    if not has_critical_health_values(health_conditions):
        return "No critical health alerts"

    abnormal = []

    try:
        glucose = float(health_conditions.get('diabetes', 0) or 0)
        if glucose >= 100:
            abnormal.append('blood sugar')
    except Exception:
        pass

    systolic, diastolic = _parse_bp(health_conditions.get('blood_pressure', '0/0'))
    if systolic > 120 or diastolic > 80:
        abnormal.append('blood pressure')

    try:
        cholesterol = float(health_conditions.get('cholesterol', 0) or 0)
        if cholesterol >= 200:
            abnormal.append('cholesterol')
    except Exception:
        pass

    try:
        bmi = float(health_conditions.get('obesity_bmi', 0) or 0)
        if bmi >= 25:
            abnormal.append('BMI')
    except Exception:
        pass

    if not abnormal:
        return "No critical health alerts"

    if len(abnormal) == 1:
        return f"Critical Alert: Your {abnormal[0]} is above normal. Please consult a doctor."

    joined = ', '.join(abnormal[:-1]) + f" and {abnormal[-1]}"
    return f"Critical Alert: Your {joined} are above normal. Please consult a doctor."


def _extract_json(text: str) -> str:
    """Extract the first JSON object found in the model response text.

    This implements a simple balanced-brace scanner instead of using
    unsupported PCRE recursion patterns. It also handles quoted strings
    and escaped characters so braces inside strings are ignored.
    """
    # Try direct load first
    try:
        json.loads(text)
        return text
    except Exception:
        pass

    # Find first opening brace
    start = text.find('{')
    if start == -1:
        raise ValueError('No JSON object found in model response')

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
                continue
            if ch == '\\':
                escape = True
                continue
            if ch == '"':
                in_string = False
            continue

        # not in string
        if ch == '"':
            in_string = True
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                candidate = text[start:i+1]
                # validate
                try:
                    json.loads(candidate)
                    return candidate
                except Exception:
                    # keep scanning in case of nested non-json fragments
                    pass

    raise ValueError('No JSON object found in model response')


def _call_openrouter_raw(prompt: str) -> str:
    """Call OpenRouter HTTP API and return the textual response."""
    try:
        import requests
    except Exception:
        raise RuntimeError('The `requests` library is required to use OpenRouter integration')

    if not OPENROUTER_API_KEY:
        raise RuntimeError('OPENROUTER_API_KEY is not configured in environment')

    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        'model': OPENROUTER_MODEL,
        'messages': [
            {'role': 'system', 'content': 'You are a professional healthcare nutritionist AI.'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.6,
        'max_tokens': 1000
    }

    resp = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f'OpenRouter request failed: {resp.status_code} {resp.text}')

    try:
        obj = resp.json()
    except Exception:
        return resp.text

    # OpenRouter responses typically embed text under `choices[0].message.content`
    if isinstance(obj, dict) and obj.get('choices'):
        try:
            return obj['choices'][0]['message']['content']
        except Exception:
            return json.dumps(obj)

    return json.dumps(obj)


def _call_gemini_raw(prompt: str) -> str:
    """Call the configured model provider and return the textual response.

    Currently only OpenRouter HTTP API is supported. This function delegates
    to `_call_openrouter_raw` and raises if the OpenRouter key is not configured.
    """
    if not OPENROUTER_API_KEY:
        raise RuntimeError('OPENROUTER_API_KEY is not configured; set it in environment')
    return _call_openrouter_raw(prompt)


# Use caching wrapper if cache is available
if _CACHE is not None:
    def _cache_key_wrapper(*args, **kwargs):
        # Support both positional and keyword calls (tests call with kwargs)
        patient_name = kwargs.get('patient_name') if 'patient_name' in kwargs else (args[0] if len(args) > 0 else None)
        health_conditions = kwargs.get('health_conditions') if 'health_conditions' in kwargs else (args[1] if len(args) > 1 else None)
        allergies = kwargs.get('allergies') if 'allergies' in kwargs else (args[2] if len(args) > 2 else None)
        food_pref = kwargs.get('food_preference') if 'food_preference' in kwargs else (args[3] if len(args) > 3 else None)
        return _cache_key(patient_name, health_conditions, allergies, food_pref)

    @cached(_CACHE, key=_cache_key_wrapper)
    def get_recommendations_from_gemini(patient_name: str, health_conditions: Dict[str, Any], allergies: List[str], food_preference: str) -> Dict[str, Any]:
        return _get_recommendations_from_gemini_impl(patient_name, health_conditions, allergies, food_preference)
else:
    def get_recommendations_from_gemini(patient_name: str, health_conditions: Dict[str, Any], allergies: List[str], food_preference: str) -> Dict[str, Any]:
        return _get_recommendations_from_gemini_impl(patient_name, health_conditions, allergies, food_preference)


def get_recommendations_from_gemini_uncached(patient_name: str, health_conditions: Dict[str, Any], allergies: List[str], food_preference: str) -> Dict[str, Any]:
    """Always call OpenRouter directly (no TTL cache)."""
    return _get_recommendations_from_gemini_impl(patient_name, health_conditions, allergies, food_preference)


def _get_recommendations_from_gemini_impl(patient_name: str, health_conditions: Dict[str, Any], allergies: List[str], food_preference: str) -> Dict[str, Any]:
    """Call the configured model provider (OpenRouter) and return validated JSON result.

    Raises ValueError on invalid responses and RuntimeError on API errors.
    """
    if not OPENROUTER_API_KEY:
        raise RuntimeError('OPENROUTER_API_KEY is not configured in environment')

    # build prompt and make explicit JSON-only requirement
    prompt = _build_prompt(patient_name, health_conditions, allergies, food_preference)

    legacy_mode = _legacy_test_mode()

    try:
        text = _call_gemini_raw(prompt)
        # Support response-like objects returned by tests (with a `.text` attribute)
        if not isinstance(text, str) and hasattr(text, 'text'):
            text = getattr(text, 'text')

        logging.debug("raw LLM response: %s", text)
        json_text = _extract_json(text)
        try:
            data = json.loads(json_text)
        except Exception as exc:
            logging.error("failed to load json_text=%s: %s", json_text, exc)
            raise

        # normalize old Gemini-style wrapper if present
        def _normalize(data_obj):
            if isinstance(data_obj, dict) and 'candidates' in data_obj:
                try:
                    inner = data_obj['candidates'][0]['content']['parts'][0]['text']
                    logging.debug("extracting inner text from candidates: %s", inner)
                    return json.loads(_extract_json(inner))
                except Exception as e:
                    logging.warning("could not normalize candidates wrapper: %s", e)
                    return data_obj
            return data_obj
        data = _normalize(data)

        # log parsed data for debugging
        logging.debug("parsed JSON object: %s", json.dumps(data, indent=2))

        # Handle legacy simple outputs where the model returned breakfast/lunch/dinner
        # rather than the newer nested Food object.
        if any(k in data for k in ('breakfast', 'lunch', 'dinner')):
            logging.debug("normalizing flat meal keys into Food object")
            data = {
                'Food': {
                    'Morning': data.get('breakfast', []),
                    'Afternoon': data.get('lunch', []),
                    'Evening': data.get('dinner', [])
                },
                'Drinks': data.get('drinks', []),
                'Snacks': data.get('snacks', []),
                'foods_to_avoid': data.get('foods_to_avoid', []),
                'alternativeMessage': data.get('alternativeMessage', ''),
                'healthyTipsForToday': data.get('healthyTipsForToday', {})
            }

        # Normalize lower-case meal keys from the strict JSON schema to the
        # internal keys used by the rest of the backend.
        if isinstance(data.get('Food'), dict):
            f = data['Food']
            if 'morning' in f or 'lunch' in f or 'dinner' in f:
                data['Food'] = {
                    'Morning': f.get('Morning', f.get('morning', [])),
                    'Afternoon': f.get('Afternoon', f.get('lunch', [])),
                    'Evening': f.get('Evening', f.get('dinner', []))
                }
        # Normalize alternatives object from potential lower-case keys.
        if isinstance(data.get('Alternatives'), dict):
            alts = data['Alternatives']
            data['Alternatives'] = {
                'Breakfast': alts.get('Breakfast', alts.get('breakfast', [])),
                'Lunch': alts.get('Lunch', alts.get('lunch', [])),
                'Dinner': alts.get('Dinner', alts.get('dinner', [])),
                'Drinks': alts.get('Drinks', alts.get('drinks', [])),
                'Snacks': alts.get('Snacks', alts.get('snacks', [])),
            }

        # ensure defaults for missing keys instead of crashing
        allergies_text = ', '.join(allergies) if allergies else 'none'
        data = {
            'Food': data.get('Food', {'Morning': [], 'Afternoon': [], 'Evening': []}),
            'Drinks': data.get('Drinks', []),
            'Snacks': data.get('Snacks', []),
            'foods_to_avoid': data.get('foods_to_avoid', []),
            'allergyAlert': data.get('allergyAlert', f'foods containing {allergies_text} are excluded from your plan.'),
            'Alternatives': data.get('Alternatives', {
                'Breakfast': [],
                'Lunch': [],
                'Dinner': [],
                'Drinks': [],
                'Snacks': []
            }),
            'alternativeMessage': data.get('alternativeMessage', ''),
            'healthyTipsForToday': data.get('healthyTipsForToday', {})
        }

        # At this point data has all required keys; warn if they were originally absent
        for key in ['Food', 'Drinks', 'Snacks', 'Alternatives', 'alternativeMessage', 'healthyTipsForToday']:
            if key not in data or data[key] in (None, '', {}):
                logging.warning("Key %s missing or empty in AI output, defaulting", key)

        # Ensure alternativeMessage matches the fixed text
        data['alternativeMessage'] = 'Alternative food options are available.'

        # Enforce doctorAlert if multiple alerts
        if _count_alert_conditions(health_conditions) >= 2:
            data['doctorAlert'] = 'Please consult a doctor for personalized medical guidance.'

        # Ensure strict item shapes
        def _validate_items_list(lst, require_cost=False):
            if not isinstance(lst, list):
                return False
            for it in lst:
                if not isinstance(it, dict) or 'name' not in it or 'reason' not in it:
                    return False
                if require_cost and 'estimated_cost' not in it:
                    return False
            return True

        require_cost = not legacy_mode

        # Validate Food->Morning/Afternoon/Evening
        if not isinstance(data['Food'], dict):
            raise ValueError('"Food" must be an object with Morning/Afternoon/Evening arrays')
        for meal in ['Morning', 'Afternoon', 'Evening']:
            if meal not in data['Food']:
                data['Food'][meal] = []
            elif not _validate_items_list(data['Food'][meal], require_cost=require_cost):
                raise ValueError(f'Invalid items in Food->{meal}')

        # Validate Drinks and Snacks
        if not _validate_items_list(data['Drinks'], require_cost=require_cost):
            raise ValueError('Invalid "Drinks" list')
        if not _validate_items_list(data['Snacks'], require_cost=require_cost):
            raise ValueError('Invalid "Snacks" list')

        if not _validate_items_list(data['foods_to_avoid'], require_cost=False):
            raise ValueError('Invalid "foods_to_avoid" list')

        # Validate alternatives sections
        if not isinstance(data['Alternatives'], dict):
            raise ValueError('Invalid "Alternatives" object')
        for section in ['Breakfast', 'Lunch', 'Dinner', 'Drinks', 'Snacks']:
            if section not in data['Alternatives']:
                data['Alternatives'][section] = []
            elif not _validate_items_list(data['Alternatives'][section], require_cost=require_cost):
                raise ValueError(f'Invalid alternatives list: {section}')

        # Accept both string and object for healthy tips. The current prompt
        # asks for a string, while some legacy callers expect an object.
        if isinstance(data['healthyTipsForToday'], str):
            tip_text = data['healthyTipsForToday'].strip()
            data['healthyTipsForToday'] = {'specific': tip_text} if tip_text else {}
        elif data['healthyTipsForToday'] is None:
            data['healthyTipsForToday'] = {}
        elif not isinstance(data['healthyTipsForToday'], dict):
            raise ValueError('"healthyTipsForToday" must be a string or an object with tips')

        _ensure_health_tips_present(data, health_conditions or {}, allergies or [], food_preference)

        data = _post_process_recommendations(data, health_conditions or {}, allergies or [], food_preference)

        return data

    except Exception as e:
        # Wrap exceptions for callers
        raise RuntimeError(f'Gemini request or parsing failed: {str(e)}')
