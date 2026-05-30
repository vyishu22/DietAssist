#!/usr/bin/env python3
"""
Quick script to verify MongoDB connection and check stored data
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/dietassist')

def verify_mongodb_connection():
    """Verify MongoDB connection and show stored data"""
    try:
        # Try to connect
        print(f"📡 Attempting to connect to MongoDB: {MONGO_URI}")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        
        # Verify connection by checking server info
        server_info = client.server_info()
        print(f"✅ MongoDB Connection: SUCCESS")
        print(f"   Server Version: {server_info.get('version', 'Unknown')}")
        
        # Get database
        db = client['dietassist']
        print(f"\n📦 Database: {db.name}")
        
        # Check collections and their data
        collections_info = {
            'users': 'Patient & Caretaker Accounts',
            'health_information': 'Health Profiles (Conditions, Allergies, Preferences)',
            'feedback': 'User Feedback & Ratings',
            'recommendations': 'Recommendation History'
        }
        
        print("\n" + "="*70)
        print("COLLECTIONS & DATA COUNT")
        print("="*70)
        
        for collection_name, description in collections_info.items():
            try:
                collection = db[collection_name]
                count = collection.count_documents({})
                print(f"\n📋 {collection_name}")
                print(f"   Description: {description}")
                print(f"   Documents Stored: {count}")
                
                if count > 0:
                    # Show recent documents
                    latest = list(collection.find().sort('created_at', -1).limit(1))
                    if latest:
                        doc = latest[0]
                        print(f"   Latest Entry ID: {doc.get('_id')}")
                        print(f"   Last Updated: {doc.get('created_at', doc.get('updated_at', 'N/A'))}")
                        
                        # Show sample data
                        if collection_name == 'users':
                            print(f"   Sample: {doc.get('name')} ({doc.get('user_type')}) - {doc.get('email')}")
                        elif collection_name == 'health_information':
                            print(f"   Sample: {doc.get('name')} - Conditions: {list(doc.get('health_conditions', {}).keys())}")
                        elif collection_name == 'recommendations':
                            meals = f"Recipes: {[f.get('name', 'Unknown') for f in doc.get('breakfast', [])[:2]]}"
                            print(f"   Sample: {meals}")
                        elif collection_name == 'feedback':
                            print(f"   Sample: Rating {doc.get('rating')}/5 - {doc.get('comment', 'No comment')[:50]}")
                            
            except Exception as e:
                print(f"   ⚠️  Error reading collection: {str(e)}")
        
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        
        total_docs = sum(db[col].count_documents({}) for col in collections_info.keys())
        print(f"✅ Total Documents Stored: {total_docs}")
        
        if total_docs > 0:
            print("✅ Data IS being stored in MongoDB")
        else:
            print("⚠️  No data found. MongoDB is connected but empty.")
        
        client.close()
        return True
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"❌ MongoDB Connection: FAILED")
        print(f"   Error: {str(e)}")
        print(f"\n   🔧 Fix: Make sure MongoDB is running")
        print(f"      Windows: mongod")
        print(f"      Or use MongoDB Atlas (cloud): Update MONGO_URI in .env")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")
        return False

if __name__ == '__main__':
    success = verify_mongodb_connection()
    exit(0 if success else 1)
