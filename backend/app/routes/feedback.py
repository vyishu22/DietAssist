from flask import Blueprint, request, jsonify
from app.models.models import Feedback
from app.utils.auth_utils import verify_token
from app import mongo

feedback_bp = Blueprint('feedback', __name__, url_prefix='/api/feedback')

@feedback_bp.route('/submit', methods=['POST'])
def submit_feedback():
    """Submit feedback on recommendations"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        payload = verify_token(token)
        if not payload or payload.get('user_type') != 'patient':
            return jsonify({'error': 'Unauthorized'}), 401
        
        user_id = payload['user_id']
        data = request.get_json()
        
        if not data.get('rating'):
            return jsonify({'error': 'Rating is required'}), 400
        
        if data['rating'] < 1 or data['rating'] > 5:
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        # Save feedback
        feedback = Feedback(user_id, mongo)
        feedback_id = feedback.save({
            'rating': data.get('rating'),
            'comment': data.get('comment', ''),
            'recommendation_type': data.get('recommendation_type', 'general'),
            'recommendation_id': data.get('recommendation_id')
        })
        
        return jsonify({
            'message': 'Feedback submitted successfully',
            'feedback_id': feedback_id
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@feedback_bp.route('/history', methods=['GET'])
def get_feedback_history():
    """Get user's feedback history"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        payload = verify_token(token)
        if not payload or payload.get('user_type') != 'patient':
            return jsonify({'error': 'Unauthorized'}), 401
        
        user_id = payload['user_id']
        
        feedback_list = Feedback.find_by_user_id(user_id, mongo)
        
        # Convert ObjectId to string for JSON serialization
        feedback_data = []
        for fb in feedback_list:
            feedback_data.append({
                'id': str(fb.get('_id')),
                'rating': fb.get('rating'),
                'comment': fb.get('comment'),
                'recommendation_type': fb.get('recommendation_type'),
                'recommendation_id': str(fb.get('recommendation_id')) if fb.get('recommendation_id') else None,
                'created_at': fb.get('created_at').isoformat() if fb.get('created_at') else None
            })
        
        return jsonify({'feedback': feedback_data}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
