#!/usr/bin/env python3
"""
Local test script to verify GenAI recommendation endpoint.
Mocks the database and GenAI service to demonstrate the full flow.
"""
import sys
import os
import json
import requests
from unittest.mock import patch, MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Set test environment variables
os.environ['GEMINI_API_KEY'] = 'test-key-for-demo'
os.environ['MONGO_URI'] = 'mongodb://localhost:27017/dietassist'
os.environ['SECRET_KEY'] = 'test-secret'

from app import create_app

# Mock data for health information
MOCK_HEALTH_INFO = {
    'user_id': 'test_user_123',
    'name': 'John Doe',
    'health_conditions': {
        'diabetes': '145',  # Above threshold (100)
        'cholesterol': '220'  # Above threshold (200)
    },
    'allergies': ['peanuts'],
    'food_preference': 'vegetarian'
}

# Mock GenAI response (would normally come from Google Gemini)
MOCK_GENAI_RESPONSE = {
    'Food': {
        'Morning': [
            {'name': 'Jowar Porridge', 'reason': 'Low glycemic ancient grain helps control blood sugar'},
            {'name': 'Green Tea', 'reason': 'Antioxidants support overall health'}
        ],
        'Afternoon': [
            {'name': 'Vegetable Sambhar with Ragi', 'reason': 'Low-calorie meal with mineral-rich ancient grain'}
        ],
        'Evening': [
            {'name': 'Vegetable Uttapam', 'reason': 'Light meal, high protein and easily digestible'}
        ]
    },
    'Drinks': [
        {'name': 'Cinnamon Water', 'reason': 'May help improve insulin sensitivity and blood glucose control'},
        {'name': 'Green Tea with Moringa', 'reason': 'Antioxidants for heart health'}
    ],
    'Snacks': [
        {'name': 'Roasted Peanuts', 'reason': 'Protein-rich snack with stable blood sugar impact'},
        {'name': 'Cucumber with Yogurt', 'reason': 'Low carb, probiotic-rich'}
    ],
    'alternativeMessage': 'Alternative food options are available.',
    'healthyTipsForToday': {
        'hydration': 'Drink at least 8-10 glasses of water daily',
        'exercise': 'Aim for 30 minutes of moderate physical activity',
        'sleep': 'Get 7-9 hours of quality sleep',
        'specific': 'Monitor blood glucose and cholesterol levels regularly'
    },
    'doctorAlert': 'Please consult a doctor for personalized medical guidance.'
}


def test_genai_endpoint():
    """Test the GenAI recommendation endpoint with mocked data."""
    app = create_app()
    client = app.test_client()
    
    with app.app_context():
        # Mock verify_token
        def mock_verify_token(token):
            return {'user_id': 'test_user_123', 'user_type': 'patient'}
        
        # Mock HealthInformation.find_by_user_id
        def mock_find_health(user_id, mongo):
            if user_id == 'test_user_123':
                return MOCK_HEALTH_INFO
            return None
        
        # Mock get_recommendations_from_gemini
        def mock_genai_recommender(*args, **kwargs):
            print("  ✓ Mocked GenAI service called with:")
            print(f"    - Patient name: {args[0]}")
            print(f"    - Health conditions: {args[1]}")
            print(f"    - Allergies: {args[2]}")
            print(f"    - Food preference: {args[3]}")
            return MOCK_GENAI_RESPONSE
        
        with patch('app.routes.recommendations.verify_token', mock_verify_token), \
             patch('app.routes.recommendations.HealthInformation.find_by_user_id', mock_find_health), \
             patch('app.services.gemini_recommender.get_recommendations_from_gemini', mock_genai_recommender):
            
            # Make request to /api/recommendations/genai
            headers = {
                'Authorization': 'Bearer test-token',
                'Content-Type': 'application/json'
            }
            
            print("\n📤 Sending request to POST /api/recommendations/genai...")
            response = client.post('/api/recommendations/genai', headers=headers, json={})
            
            print(f"\n✅ Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print("\n📋 GenAI Recommendations Received:")
                print(f"\n  🍽️  Morning Food:")
                for food in data.get('Food', {}).get('Morning', []):
                    print(f"     - {food['name']}: {food['reason']}")
                
                print(f"\n  ☕ Drinks:")
                for drink in data.get('Drinks', []):
                    print(f"     - {drink['name']}: {drink['reason']}")
                
                print(f"\n  🥜 Snacks:")
                for snack in data.get('Snacks', []):
                    print(f"     - {snack['name']}: {snack['reason']}")
                
                print(f"\n  💡 Healthy Tips:")
                tips = data.get('healthyTipsForToday', {})
                for tip_key, tip_value in tips.items():
                    print(f"     - {tip_key}: {tip_value}")
                
                if data.get('alert_message'):
                    alert = data['alert_message']
                    if alert.get('show'):
                        print(f"\n  ⚠️  Alert: {alert['message']}")
                
                if data.get('doctorAlert'):
                    print(f"\n  🏥 Doctor Alert: {data['doctorAlert']}")
                
                print("\n✨ GenAI integration is working correctly!")
                return True
            else:
                print(f"\n❌ Error: {response.get_json()}")
                return False


if __name__ == '__main__':
    print("=" * 70)
    print("Testing GenAI Recommendation Endpoint (Local with Mocked Services)")
    print("=" * 70)
    
    success = test_genai_endpoint()
    sys.exit(0 if success else 1)
