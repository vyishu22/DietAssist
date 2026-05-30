from flask import Blueprint, request, jsonify
from app.models.models import User
from app.utils.auth_utils import (
    hash_password, verify_password, generate_token,
    validate_email, validate_password
)
from app import mongo

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/patient/register', methods=['POST'])
def patient_register():
    """Register a new patient user"""
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('name') or not data.get('age') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Check if user exists
        existing_user = User.find_by_email(data['email'], mongo)
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create user
        password_hash = hash_password(data['password'])
        user = User(
            name=data['name'],
            age=int(data['age']),
            email=data['email'],
            password_hash=password_hash,
            mongo=mongo
        )
        user_id = user.save()
        
        # Generate token
        token = generate_token(user_id, 'patient')
        
        return jsonify({
            'message': 'Patient registered successfully',
            'user_id': user_id,
            'token': token,
            'user_type': 'patient'
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/patient/login', methods=['POST'])
def patient_login():
    """Patient login"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Missing email or password'}), 400
        
        user = User.find_by_email(data['email'], mongo)
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not verify_password(data['password'], user['password_hash']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        token = generate_token(str(user['_id']), 'patient')
        
        return jsonify({
            'message': 'Login successful',
            'user_id': str(user['_id']),
            'token': token,
            'user_type': 'patient',
            'name': user.get('name')
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """Verify JWT token"""
    try:
        from app.utils.auth_utils import verify_token
        
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401
        
        return jsonify({
            'valid': True,
            'user_id': payload['user_id'],
            'user_type': payload['user_type']
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
