from datetime import datetime
import re
from bson.objectid import ObjectId
from bson.errors import InvalidId
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _to_object_id(value):
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if ObjectId.is_valid(raw):
            return ObjectId(raw)
    raise ValueError('Invalid ObjectId value')


def _user_id_query(user_id):
    """Support legacy rows where user_id may still be stored as string."""
    oid = _to_object_id(user_id)
    return {'$in': [oid, str(oid)]}


def _validate_email(email: str) -> str:
    normalized = str(email or '').strip().lower()
    if not normalized or not EMAIL_REGEX.match(normalized):
        raise ValueError('Invalid email format')
    return normalized


def _validate_age(age) -> int:
    try:
        value = int(age)
    except (TypeError, ValueError):
        raise ValueError('Age must be a valid integer')
    if value <= 0:
        raise ValueError('Age must be greater than 0')
    return value


def _validate_rating(rating) -> int:
    try:
        value = int(rating)
    except (TypeError, ValueError):
        raise ValueError('Rating must be an integer between 1 and 5')
    if value < 1 or value > 5:
        raise ValueError('Rating must be between 1 and 5')
    return value


def _to_number_or_none(value):
    if value is None or value == '':
        return None
    try:
        num = float(value)
        return int(num) if num.is_integer() else num
    except (TypeError, ValueError):
        return None


def _normalize_health_conditions(raw_conditions):
    raw = raw_conditions if isinstance(raw_conditions, dict) else {}
    normalized = {}

    diabetes = _to_number_or_none(raw.get('diabetes'))
    if diabetes is not None:
        normalized['diabetes'] = diabetes

    bp = str(raw.get('bp') or raw.get('blood_pressure') or '').strip()
    if bp:
        normalized['bp'] = bp
        # Keep legacy alias for compatibility with existing route code.
        normalized['blood_pressure'] = bp

    cholesterol = _to_number_or_none(raw.get('cholesterol'))
    if cholesterol is not None:
        normalized['cholesterol'] = cholesterol

    obesity_bmi = _to_number_or_none(raw.get('obesity_bmi'))
    if obesity_bmi is not None:
        normalized['obesity_bmi'] = obesity_bmi

    return normalized


def _normalize_healthy_tips(raw_tips):
    """Store healthy tips as a list of strings."""
    tips = []
    if isinstance(raw_tips, list):
        tips = [str(t).strip() for t in raw_tips if str(t).strip()]
    elif isinstance(raw_tips, dict):
        tips = [str(v).strip() for v in raw_tips.values() if isinstance(v, str) and v.strip()]
    elif isinstance(raw_tips, str):
        value = raw_tips.strip()
        if value:
            tips = [value]

    seen = set()
    deduped = []
    for tip in tips:
        key = tip.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(tip)
    return deduped


def _extract_section_cost(items):
    if not isinstance(items, list):
        return ''
    for item in items:
        if isinstance(item, dict):
            cost = str(item.get('estimated_cost', '')).strip()
            if cost:
                return cost
    return ''

class User:
    """Patient user model"""
    def __init__(self, name, age, email, password_hash, mongo):
        self.name = name
        self.age = _validate_age(age)
        self.email = _validate_email(email)
        self.password_hash = password_hash
        self.created_at = datetime.utcnow()
        self.mongo = mongo

    @staticmethod
    def _ensure_indexes(db):
        try:
            db.users.create_index([('email', ASCENDING)], unique=True, name='users_email_unique')
        except PyMongoError:
            pass
    
    def save(self):
        db = self.mongo.db
        self._ensure_indexes(db)
        if db.users.find_one({'email': self.email}):
            raise ValueError('Email already registered')
        user_data = {
            'name': self.name,
            'age': self.age,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at,
            'user_type': 'patient'
        }
        result = db.users.insert_one(user_data)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_email(email, mongo):
        db = mongo.db
        normalized = _validate_email(email)
        return db.users.find_one({'email': normalized})
    
    @staticmethod
    def find_by_id(user_id, mongo):
        db = mongo.db
        try:
            return db.users.find_one({'_id': _to_object_id(user_id)})
        except (InvalidId, TypeError, ValueError):
            return None


class HealthInformation:
    """Health data model"""
    def __init__(self, user_id, mongo):
        self.user_id = _to_object_id(user_id)
        self.mongo = mongo

    @staticmethod
    def _ensure_indexes(db):
        try:
            db.health_information.create_index([('user_id', ASCENDING)], unique=True, name='health_user_unique')
        except PyMongoError:
            pass
    
    def save(self, health_data):
        db = self.mongo.db
        self._ensure_indexes(db)
        health_info = {
            'user_id': self.user_id,
            'name': health_data.get('name'),
            'health_conditions': _normalize_health_conditions(health_data.get('health_conditions', {})),
            'allergies': health_data.get('allergies', []),
            'food_preference': health_data.get('food_preference'),
            'updated_at': datetime.utcnow()
        }
        
        existing = db.health_information.find_one({'user_id': _user_id_query(self.user_id)})
        if existing:
            db.health_information.update_one(
                {'_id': existing['_id']},
                {'$set': health_info}
            )
            return str(existing['_id'])
        else:
            health_info['created_at'] = datetime.utcnow()
            result = db.health_information.insert_one(health_info)
            return str(result.inserted_id)
    
    @staticmethod
    def find_by_user_id(user_id, mongo):
        db = mongo.db
        HealthInformation._ensure_indexes(db)
        try:
            return db.health_information.find_one({'user_id': _user_id_query(user_id)})
        except (InvalidId, TypeError, ValueError):
            return None

    @staticmethod
    def delete_by_user_id(user_id, mongo):
        db = mongo.db
        HealthInformation._ensure_indexes(db)
        try:
            result = db.health_information.delete_many({'user_id': _user_id_query(user_id)})
        except (InvalidId, TypeError, ValueError):
            return False
        return result.deleted_count > 0


class Caretaker:
    """Caretaker user model (Doctor, Parent, Nutritionist, etc.)"""
    def __init__(self, name, email, password_hash, role, mongo):
        self.name = name
        self.email = _validate_email(email)
        self.password_hash = password_hash
        self.role = role
        self.created_at = datetime.utcnow()
        self.mongo = mongo

    @staticmethod
    def _ensure_indexes(db):
        try:
            db.users.create_index([('email', ASCENDING)], unique=True, name='users_email_unique')
        except PyMongoError:
            pass
    
    def save(self):
        db = self.mongo.db
        self._ensure_indexes(db)
        if db.users.find_one({'email': self.email}):
            raise ValueError('Email already registered')
        caretaker_data = {
            'name': self.name,
            'email': self.email,
            'password_hash': self.password_hash,
            'role': self.role,
            'created_at': self.created_at,
            'user_type': 'caretaker'
        }
        result = db.users.insert_one(caretaker_data)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_email(email, mongo):
        db = mongo.db
        normalized = _validate_email(email)
        return db.users.find_one({'email': normalized, 'user_type': 'caretaker'})
    
    @staticmethod
    def find_by_id(caretaker_id, mongo):
        db = mongo.db
        try:
            return db.users.find_one({'_id': _to_object_id(caretaker_id), 'user_type': 'caretaker'})
        except (InvalidId, TypeError, ValueError):
            return None


class Feedback:
    """Feedback model for recommendations"""
    def __init__(self, user_id, mongo):
        self.user_id = _to_object_id(user_id)
        self.mongo = mongo

    @staticmethod
    def _ensure_indexes(db):
        try:
            db.feedback.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)], name='feedback_user_created_idx')
            db.feedback.create_index([('recommendation_id', ASCENDING)], name='feedback_recommendation_idx')
        except PyMongoError:
            pass
    
    def save(self, feedback_data):
        db = self.mongo.db
        self._ensure_indexes(db)
        recommendation_id = feedback_data.get('recommendation_id')
        recommendation_oid = None
        if recommendation_id:
            recommendation_oid = _to_object_id(recommendation_id)
        feedback = {
            'user_id': self.user_id,
            'rating': _validate_rating(feedback_data.get('rating')),
            'comment': feedback_data.get('comment'),
            'recommendation_type': feedback_data.get('recommendation_type'),
            'recommendation_id': recommendation_oid,
            'created_at': datetime.utcnow()
        }
        result = db.feedback.insert_one(feedback)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_user_id(user_id, mongo):
        db = mongo.db
        Feedback._ensure_indexes(db)
        try:
            return list(db.feedback.find({'user_id': _user_id_query(user_id)}))
        except (InvalidId, TypeError, ValueError):
            return []


class Recommendation:
    """Recommendation history model for caretaker viewing"""
    def __init__(self, user_id, mongo):
        self.user_id = _to_object_id(user_id)
        self.mongo = mongo

    @staticmethod
    def _ensure_indexes(db):
        try:
            db.recommendations.create_index([('user_id', ASCENDING)], name='recommendations_user_idx')
            db.recommendations.create_index([('created_at', DESCENDING)], name='recommendations_created_idx')
            db.recommendations.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)], name='recommendations_user_created_idx')
        except PyMongoError:
            pass
    
    def save(self, recommendation_data):
        """Save a recommendation (for caretaker history viewing)"""
        db = self.mongo.db
        self._ensure_indexes(db)

        breakfast = recommendation_data.get('breakfast', [])
        lunch = recommendation_data.get('lunch', [])
        dinner = recommendation_data.get('dinner', [])
        drinks = recommendation_data.get('drinks', [])
        snacks = recommendation_data.get('snacks', [])

        recommendation = {
            'user_id': self.user_id,
            'breakfast': breakfast,
            'lunch': lunch,
            'dinner': dinner,
            'drinks': drinks,
            'snacks': snacks,
            'breakfast_cost': recommendation_data.get('breakfast_cost') or _extract_section_cost(breakfast),
            'lunch_cost': recommendation_data.get('lunch_cost') or _extract_section_cost(lunch),
            'dinner_cost': recommendation_data.get('dinner_cost') or _extract_section_cost(dinner),
            'drinks_cost': recommendation_data.get('drinks_cost') or _extract_section_cost(drinks),
            'snacks_cost': recommendation_data.get('snacks_cost') or _extract_section_cost(snacks),
            'foods_to_avoid': recommendation_data.get('foods_to_avoid', []),
            'healthy_tips': _normalize_healthy_tips(recommendation_data.get('healthy_tips', [])),
            'recommendation_type': recommendation_data.get('recommendation_type', 'genai'),  # 'genai' indicates LLM-generated
            'created_at': datetime.utcnow()
        }
        result = db.recommendations.insert_one(recommendation)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_user_id(user_id, mongo, limit=10):
        """Get latest recommendations for a user"""
        db = mongo.db
        Recommendation._ensure_indexes(db)
        try:
            return list(db.recommendations.find({'user_id': _user_id_query(user_id)}).sort('created_at', -1).limit(limit))
        except (InvalidId, TypeError, ValueError):
            return []
    
    @staticmethod
    def find_latest_by_user_id(user_id, mongo):
        """Get the most recent recommendation for a user"""
        db = mongo.db
        Recommendation._ensure_indexes(db)
        try:
            return db.recommendations.find_one({'user_id': _user_id_query(user_id)}, sort=[('created_at', -1)])
        except (InvalidId, TypeError, ValueError):
            return None