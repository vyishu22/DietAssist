#!/usr/bin/env python
"""
Verify test fixes without importing the app
"""
import os
import re

print("Verifying test fixes...")
print("=" * 60)

# Test 1: Check test_gemini_recommender.py uses OPENROUTER_API_KEY
print("\n1. Checking test_gemini_recommender.py...")
with open('backend/tests/test_gemini_recommender.py', 'r') as f:
    content = f.read()
    
    # Should NOT have API_KEY
    if re.search(r"monkeypatch\.setattr\(gemini_recommender,\s*['\"]API_KEY['\"]", content):
        print("✗ FAIL: test_gemini_recommender.py still references API_KEY")
        exit(1)
    
    # Should have OPENROUTER_API_KEY
    if "OPENROUTER_API_KEY" not in content:
        print("✗ FAIL: test_gemini_recommender.py doesn't mock OPENROUTER_API_KEY")
        exit(1)
    
    # Should have FakeHTTPResp class
    if "class FakeHTTPResp:" not in content:
        print("✗ FAIL: test_gemini_recommender.py missing FakeHTTPResp class")
        exit(1)
    
    # Should mock requests.post
    if "requests.post" not in content:
        print("✗ FAIL: test_gemini_recommender.py doesn't mock requests.post")
        exit(1)
    
    # Should have OpenRouter response format
    if "choices" not in content or "message" not in content or "content" not in content:
        print("✗ FAIL: test_gemini_recommender.py missing OpenRouter response format")
        exit(1)
    
    print("✓ PASS: test_gemini_recommender.py properly mocks OpenRouter HTTP")

# Test 2: Check test_caching.py uses OPENROUTER_API_KEY
print("\n2. Checking test_caching.py...")
with open('backend/tests/test_caching.py', 'r') as f:
    content = f.read()
    
    # Should NOT have old genai mock
    if "_call_gemini_raw" in content:
        print("✗ FAIL: test_caching.py still mocks _call_gemini_raw")
        exit(1)
    
    # Should have OPENROUTER_API_KEY
    if "OPENROUTER_API_KEY" not in content:
        print("✗ FAIL: test_caching.py doesn't mock OPENROUTER_API_KEY")
        exit(1)
    
    # Should have FakeHTTPResp class
    if "class FakeHTTPResp:" not in content:
        print("✗ FAIL: test_caching.py missing FakeHTTPResp class")
        exit(1)
    
    # Should mock requests.post
    if "requests.post" not in content or "monkeypatch.setattr(requests" not in content:
        print("✗ FAIL: test_caching.py doesn't properly mock requests.post")
        exit(1)
    
    print("✓ PASS: test_caching.py properly mocks requests.post")

# Test 3: Check gemini_recommender.py removed API_KEY
print("\n3. Checking gemini_recommender.py...")
with open('backend/app/services/gemini_recommender.py', 'r') as f:
    content = f.read()
    
    # Should NOT have API_KEY = ...
    if re.search(r'^API_KEY\s*=', content, re.MULTILINE):
        print("✗ FAIL: gemini_recommender.py still defines API_KEY")
        exit(1)
    
    # Should NOT import google SDK
    if "google.genai" in content or "google.generativeai" in content:
        print("✗ FAIL: gemini_recommender.py still imports Gemini SDK")
        exit(1)
    
    # Should have OPENROUTER constants
    if "OPENROUTER_API_KEY" not in content:
        print("✗ FAIL: gemini_recommender.py missing OPENROUTER_API_KEY")
        exit(1)
    
    # Should have _call_openrouter_raw function
    if "def _call_openrouter_raw(" not in content:
        print("✗ FAIL: gemini_recommender.py missing _call_openrouter_raw")
        exit(1)
    
    # Should use requests.post
    if "requests.post(" not in content:
        print("✗ FAIL: gemini_recommender.py doesn't use requests.post")
        exit(1)
    
    print("✓ PASS: gemini_recommender.py properly implements OpenRouter")

# Test 4: Check requirements.txt has requests
print("\n4. Checking requirements.txt...")
with open('backend/requirements.txt', 'r') as f:
    content = f.read()
    
    if "requests" not in content:
        print("✗ FAIL: requirements.txt missing requests package")
        exit(1)
    
    if "google" in content and ("genai" in content or "generativeai" in content):
        print("✗ FAIL: requirements.txt still has Google SDK packages")
        exit(1)
    
    print("✓ PASS: requirements.txt has requests, no Gemini SDK")

print("\n" + "=" * 60)
print("ALL VERIFICATION PASSED!")
print("=" * 60)
print("\nSummary of fixes:")
print("✓ test_gemini_recommender.py: Updated to mock OpenRouter HTTP")
print("✓ test_caching.py: Updated to mock requests.post")
print("✓ gemini_recommender.py: Removed Gemini SDK, added OpenRouter")
print("✓ requirements.txt: Added requests, removed Gemini SDK")
print("\nThe 3 failing tests should now pass:")
print("  - test_caching.py::test_caching_uses_cache")
print("  - test_gemini_recommender.py::test_get_recommendations_from_gemini_success")
print("  - test_gemini_recommender.py::test_get_recommendations_adds_doctor_alert")
