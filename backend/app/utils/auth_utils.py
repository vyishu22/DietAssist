import jwt
import bcrypt
from datetime import datetime, timedelta
import os

def hash_password(password):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def verify_password(password, hashed):
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    except:
        return False

def generate_token(user_id, user_type):
    """Generate JWT token"""
    secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    payload = {
        'user_id': user_id,
        'user_type': user_type,
        'exp': datetime.utcnow() + timedelta(days=30)
    }
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token

def verify_token(token):
    """Verify JWT token"""
    try:
        secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except:
        return None

def validate_email(email):
    """Simple email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, "Password is strong"
