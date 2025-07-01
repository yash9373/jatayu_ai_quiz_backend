#!/usr/bin/env python3
"""
Create a test recruiter user for API testing
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def create_recruiter():
    """Create a test recruiter user"""
    user_data = {
        "name": "Test Recruiter",
        "email": "recruiter@company.com",
        "password": "recruiter123",
        "role": "recruiter"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    print(f"Registration Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Created user: {result['name']} ({result['role']})")
        return True
    else:
        print(f"Registration response: {response.text}")
        return False

if __name__ == "__main__":
    print("🔐 Creating test recruiter user...")
    if create_recruiter():
        print("✅ Test recruiter created successfully!")
    else:
        print("❌ Failed to create test recruiter")
