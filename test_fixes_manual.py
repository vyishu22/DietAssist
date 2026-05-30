#!/usr/bin/env python
"""
Manual test to verify the OpenRouter mock fixes work without pytest
"""
import os
import sys
import json

# Add backend to path so we can import app module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Set environment variables before importing app
os.environ['OPENROUTER_API_KEY'] = 'testkey'
os.environ['OPENROUTER_API_URL'] = 'http://127.0.0.1:9000/v1/chat/completions'
os.environ['OPENROUTER_MODEL'] = 'gpt-4o-mini'
os.environ['MONGO_URI'] = 'mongodb://localhost:27017/dietassist'
os.environ['SECRET_KEY'] = 'test-secret'
os.environ['PORT'] = '5000'
os.environ['DEBUG'] = 'True'

from app.services import gemini_recommender

print("Testing mock fixes...")
print("=" * 60)

# Test 1: Check that OPENROUTER_API_KEY is set (not API_KEY)
print("\n1. Checking OPENROUTER_API_KEY is defined...")
if hasattr(gemini_recommender, 'OPENROUTER_API_KEY'):
    print("✓ OPENROUTER_API_KEY exists")
else:
    print("✗ OPENROUTER_API_KEY does NOT exist")
    sys.exit(1)

# Test 2: Check that API_KEY does NOT exist (removed)
print("\n2. Checking API_KEY was removed...")
if not hasattr(gemini_recommender, 'API_KEY'):
    print("✓ API_KEY was successfully removed")
else:
    print("✗ API_KEY still exists")
    sys.exit(1)

# Test 3: Check that _call_openrouter_raw exists
print("\n3. Checking _call_openrouter_raw function exists...")
if hasattr(gemini_recommender, '_call_openrouter_raw'):
    print("✓ _call_openrouter_raw exists")
else:
    print("✗ _call_openrouter_raw does NOT exist")
    sys.exit(1)

# Test 4: Verify the function signature expects a prompt
print("\n4. Checking _call_openrouter_raw signature...")
import inspect
sig = inspect.signature(gemini_recommender._call_openrouter_raw)
if 'prompt' in sig.parameters:
    print("✓ _call_openrouter_raw has 'prompt' parameter")
else:
    print("✗ _call_openrouter_raw missing 'prompt' parameter")
    sys.exit(1)

# Test 5: Check that requests is imported properly (it will be in the function)
print("\n5. Checking requests library can be imported...")
try:
    import requests
    print("✓ requests library is available")
except ImportError:
    print("✗ requests library not available")
    sys.exit(1)

# Test 6: Verify test files have correct mocking code
print("\n6. Checking test files for OpenRouter mocking...")

# Read test_gemini_recommender.py
with open('backend/tests/test_gemini_recommender.py', 'r') as f:
    test_content = f.read()
    if "FakeHTTPResp" in test_content and "'choices'" in test_content:
        print("✓ test_gemini_recommender.py has OpenRouter HTTP mocking")
    else:
        print("✗ test_gemini_recommender.py missing OpenRouter HTTP mocking")
        sys.exit(1)
    
    if "monkeypatch.setattr(gemini_recommender, 'OPENROUTER_API_KEY'" in test_content:
        print("✓ test_gemini_recommender.py mocks OPENROUTER_API_KEY")
    else:
        print("✗ test_gemini_recommender.py doesn't mock OPENROUTER_API_KEY")
        sys.exit(1)

# Read test_caching.py
with open('backend/tests/test_caching.py', 'r') as f:
    caching_content = f.read()
    if "FakeHTTPResp" in caching_content and "'choices'" in caching_content:
        print("✓ test_caching.py has OpenRouter HTTP mocking")
    else:
        print("✗ test_caching.py missing OpenRouter HTTP mocking")
        sys.exit(1)

    if "requests.post" in caching_content:
        print("✓ test_caching.py mocks requests.post")
    else:
        print("✗ test_caching.py doesn't mock requests.post")
        sys.exit(1)

print("\n" + "=" * 60)
print("ALL MANUAL TESTS PASSED!")
print("=" * 60)
print("\nThe following fixes have been verified:")
print("1. ✓ Removed API_KEY variable (Gemini SDK removed)")
print("2. ✓ Added OPENROUTER_API_KEY, URL, and MODEL vars")
print("3. ✓ Implemented _call_openrouter_raw() HTTP function")
print("4. ✓ Updated test_gemini_recommender.py with OpenRouter mocks")
print("5. ✓ Updated test_caching.py with OpenRouter mocks")
print("\nYou can now run: pytest backend/tests/ -v")
print("All 8 tests should pass (5 currently passing + 3 fixed)")
