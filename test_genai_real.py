#!/usr/bin/env python3
"""
Test script to call GenAI endpoint with REAL Google Gemini API.
Requires valid GEMINI_API_KEY in backend/.env
"""
import sys
import os
import json
from unittest.mock import patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

from app import create_app

# Mock data for health information
MOCK_HEALTH_INFO = {
    'user_id': 'test_user_123',
    'name': 'John Doe',
    'health_conditions': {
        'diabetes': '145',
        'cholesterol': '220'
    },
    'allergies': ['shellfish'],
    'food_preference': 'non-vegetarian'
}


def test_with_real_genai():
    """Test the GenAI recommendation endpoint with REAL Gemini API."""
    app = create_app()
    client = app.test_client()
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found in backend/.env")
        return False
    
    print(f"✅ GEMINI_API_KEY loaded: {api_key[:10]}...")
    
    with app.app_context():
        # Mock verify_token
        def mock_verify_token(token):
            return {'user_id': 'test_user_123', 'user_type': 'patient'}
        
        # Mock HealthInformation.find_by_user_id
        def mock_find_health(user_id, mongo):
            if user_id == 'test_user_123':
                return MOCK_HEALTH_INFO
            return None
        
        with patch('app.routes.recommendations.verify_token', mock_verify_token), \
             patch('app.routes.recommendations.HealthInformation.find_by_user_id', mock_find_health):
            
            headers = {
                'Authorization': 'Bearer test-token',
                'Content-Type': 'application/json'
            }
            
            print("\n📤 Calling GenAI endpoint with REAL Google Gemini API...")
            print(f"   Patient: {MOCK_HEALTH_INFO['name']}")
            print(f"   Conditions: {MOCK_HEALTH_INFO['health_conditions']}")
            print(f"   Allergies: {MOCK_HEALTH_INFO['allergies']}")
            
            response = client.post('/api/recommendations/genai', headers=headers, json={})
            
            print(f"\n✅ Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                
                print("\n🎯 GenAI-Generated Recommendations from Google Gemini:")
                print("\n  🍽️  Food Recommendations:")
                
                food = data.get('Food', {})
                for meal_type in ['Morning', 'Afternoon', 'Evening']:
                    meals = food.get(meal_type, [])
                    if meals:
                        print(f"\n     {meal_type}:")
                        for item in meals:
                            print(f"       • {item['name']}")
                            print(f"         Reason: {item['reason']}")
                
                drinks = data.get('Drinks', [])
                if drinks:
                    print(f"\n  ☕ Recommended Drinks:")
                    for drink in drinks:
                        print(f"     • {drink['name']}: {drink['reason']}")
                
                snacks = data.get('Snacks', [])
                if snacks:
                    print(f"\n  🥜 Recommended Snacks:")
                    for snack in snacks:
                        print(f"     • {snack['name']}: {snack['reason']}")
                
                tips = data.get('healthyTipsForToday', {})
                if tips:
                    print(f"\n  💡 Healthy Tips for Today:")
                    for key, tip in tips.items():
                        if key != 'specific':
                            print(f"     • {tip}")
                    if tips.get('specific'):
                        print(f"     • {tips['specific']}")
                
                if data.get('doctorAlert'):
                    print(f"\n  🏥 Medical Alert: {data['doctorAlert']}")
                
                print("\n" + "="*70)
                print("✨ SUCCESS! Real Gemini API is working correctly!")
                print("="*70)
                return True
            else:
                print(f"\n❌ Error: {response.get_json()}")
                return False


if __name__ == '__main__':
    print("="*70)
    print("Testing GenAI Endpoint with REAL Google Gemini API")
    print("="*70)
    
    success = test_with_real_genai()
    sys.exit(0 if success else 1)
