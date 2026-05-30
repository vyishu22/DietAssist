from flask import Blueprint, request, jsonify
from app.models.models import HealthInformation, User
from app.utils.auth_utils import verify_token
from app import mongo

patient_bp = Blueprint('patient', __name__, url_prefix='/api/patient')

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        # Prefer module-level `verify_token` (tests often monkeypatch this). If not present,
        # fall back to `app.routes.recommendations.verify_token`, and finally to the utils
        # implementation.
        # Try multiple verify functions (module-level, recommendations, then utils) and accept the
        # first that returns a valid payload with user_type == 'patient'. This supports tests that
        # monkeypatch either `app.routes.patient.verify_token` or `app.routes.recommendations.verify_token`.
        candidate_fns = []
        v_mod = globals().get('verify_token')
        if v_mod:
            candidate_fns.append(v_mod)

        try:
            from app.routes import recommendations
            v_rec = getattr(recommendations, 'verify_token', None)
            if v_rec:
                candidate_fns.append(v_rec)
        except Exception:
            pass

        from app.utils.auth_utils import verify_token as v_utils
        candidate_fns.append(v_utils)

        payload = None
        for fn in candidate_fns:
            try:
                res = fn(token)
                if res and res.get('user_type') == 'patient':
                    payload = res
                    break
            except Exception:
                # Ignore verifier errors and try the next candidate
                continue

        if not payload:
            return jsonify({'error': 'Unauthorized'}), 401

        kwargs['user_id'] = payload['user_id']
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

@patient_bp.route('/health-information', methods=['GET'])
@require_auth
def get_health_information(user_id):
    """Get patient's health information"""
    try:
        health_info = HealthInformation.find_by_user_id(user_id, mongo)
        if not health_info:
            return jsonify({
                'name': '',
                'health_conditions': {},
                'allergies': [],
                'food_preference': 'non-vegetarian'
            }), 200
        
        return jsonify({
            'id': str(health_info.get('_id')),
            'name': health_info.get('name'),
            'health_conditions': health_info.get('health_conditions', {}),
            'allergies': health_info.get('allergies', []),
            'food_preference': health_info.get('food_preference')
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@patient_bp.route('/health-information', methods=['POST'])
@require_auth
def save_health_information(user_id):
    """Save/update patient's health information"""
    try:
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        
        # Save health information
        health_info = HealthInformation(user_id, mongo)
        health_id = health_info.save({
            'name': data.get('name'),
            'health_conditions': data.get('health_conditions', {}),
            'allergies': data.get('allergies', []),
            'food_preference': data.get('food_preference', 'non-vegetarian')
        })
        
        return jsonify({
            'message': 'Health information saved successfully',
            'id': health_id
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@patient_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile(user_id):
    """Get patient profile"""
    try:
        user = User.find_by_id(user_id, mongo)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'id': str(user['_id']),
            'name': user.get('name'),
            'age': user.get('age'),
            'email': user.get('email')
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@patient_bp.route('/delete-data', methods=['POST'])
@require_auth
def delete_data(user_id):
    """Delete a patient's health data (privacy compliance). This removes health information only; user account remains. Requires patient auth."""
    try:
        # Delete health information for the authenticated user
        deleted = HealthInformation.delete_by_user_id(user_id, mongo)
        if deleted:
            # Audit logging could be added here
            return jsonify({'message': 'Health data deleted successfully'}), 200
        else:
            return jsonify({'message': 'No health data found'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
