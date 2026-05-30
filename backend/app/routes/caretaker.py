from flask import Blueprint, request, jsonify
from app.models.models import Caretaker, User, HealthInformation
from app.utils.auth_utils import (
    hash_password, verify_password, generate_token,
    validate_email, validate_password, verify_token
)
from app import mongo

caretaker_bp = Blueprint('caretaker', __name__, url_prefix='/api/caretaker')

VALID_ROLES = ['Doctor', 'Parent', 'Nutritionist', 'Guardian', 'Others']

@caretaker_bp.route('/register', methods=['POST'])
def caretaker_register():
    """Register a new caretaker"""
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('name') or not data.get('email') or not data.get('password') or not data.get('role'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if data['role'] not in VALID_ROLES:
            return jsonify({'error': f'Invalid role. Must be one of: {", ".join(VALID_ROLES)}'}), 400
        
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Check if user exists
        existing_user = Caretaker.find_by_email(data['email'], mongo)
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create caretaker
        password_hash = hash_password(data['password'])
        caretaker = Caretaker(
            name=data['name'],
            email=data['email'],
            password_hash=password_hash,
            role=data['role'],
            mongo=mongo
        )
        caretaker_id = caretaker.save()
        
        # Generate token
        token = generate_token(caretaker_id, 'caretaker')
        
        return jsonify({
            'message': 'Caretaker registered successfully',
            'caretaker_id': caretaker_id,
            'token': token,
            'user_type': 'caretaker'
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@caretaker_bp.route('/login', methods=['POST'])
def caretaker_login():
    """Caretaker login"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Missing email or password'}), 400
        
        caretaker = Caretaker.find_by_email(data['email'], mongo)
        if not caretaker:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not verify_password(data['password'], caretaker['password_hash']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        token = generate_token(str(caretaker['_id']), 'caretaker')
        
        return jsonify({
            'message': 'Login successful',
            'caretaker_id': str(caretaker['_id']),
            'token': token,
            'user_type': 'caretaker',
            'name': caretaker.get('name'),
            'role': caretaker.get('role')
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@caretaker_bp.route('/patient/<patient_id>', methods=['GET'])
def get_patient_data(patient_id):
    """Get patient data (read-only for caretakers)"""
    try:
        # Verify caretaker token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        payload = verify_token(token)
        if not payload or payload.get('user_type') != 'caretaker':
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Get patient data
        user = User.find_by_id(patient_id, mongo)
        if not user or user.get('user_type') != 'patient':
            return jsonify({'error': 'Patient not found'}), 404
        
        health_info = HealthInformation.find_by_user_id(patient_id, mongo)
        
        response_data = {
            'patient_id': str(user['_id']),
            'name': user.get('name'),
            'age': user.get('age'),
            'email': user.get('email')
        }
        
        if health_info:
            response_data['health_information'] = {
                'name': health_info.get('name'),
                'health_conditions': health_info.get('health_conditions', {}),
                'allergies': health_info.get('allergies', []),
                'food_preference': health_info.get('food_preference')
            }
        
        return jsonify(response_data), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@caretaker_bp.route('/profile', methods=['GET'])
def get_caretaker_profile():
    """Get caretaker profile"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        payload = verify_token(token)
        if not payload or payload.get('user_type') != 'caretaker':
            return jsonify({'error': 'Unauthorized'}), 401
        
        caretaker = Caretaker.find_by_id(payload['user_id'], mongo)
        if not caretaker:
            return jsonify({'error': 'Caretaker not found'}), 404
        
        return jsonify({
            'id': str(caretaker['_id']),
            'name': caretaker.get('name'),
            'email': caretaker.get('email'),
            'role': caretaker.get('role')
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@caretaker_bp.route('/search-patients', methods=['GET'])
def search_patients():
    """Search patients by name, email, or ID"""
    try:
        # Verify caretaker token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        payload = verify_token(token)
        if not payload or payload.get('user_type') != 'caretaker':
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Get search query
        query = request.args.get('query', '').strip()
        if not query or len(query) < 2:
            return jsonify([]), 200
        
        # Search in MongoDB
        from bson.objectid import ObjectId
        
        # Build search filter - search by name, email, or ID
        or_conditions = [
            {'name': {'$regex': query, '$options': 'i'}},
            {'email': {'$regex': query, '$options': 'i'}}
        ]
        
        # Try to search by ID if it's a valid ObjectId format
        try:
            if len(query) == 24:
                or_conditions.append({'_id': ObjectId(query)})
        except:
            pass
        
        search_filter = {
            'user_type': 'patient',
            '$or': or_conditions
        }
        
        # Search for patients
        patients = list(mongo.db.users.find(search_filter).limit(10))
        
        # Format results
        results = []
        for patient in patients:
            results.append({
                '_id': str(patient['_id']),
                'name': patient.get('name', 'N/A'),
                'email': patient.get('email', 'N/A'),
                'age': patient.get('age', 'N/A')
            })
        
        return jsonify(results), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500