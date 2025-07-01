#!/usr/bin/env python3
"""
Quick test to verify candidate APIs are working
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("🔍 Quick API Test")
    print("=" * 30)
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server not responding properly")
            return
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return
    
    # Test 2: Try to create a new user
    user_data = {
        "name": "API Test User",
        "email": "apitest@example.com",
        "password": "testpass123",
        "role": "candidate"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ User registration works")
            user_id = response.json().get("user_id")
            print(f"   Created user ID: {user_id}")
        elif response.status_code == 400 and "already exists" in response.text:
            print("ℹ️  User already exists (that's fine)")
            user_id = None
        else:
            print(f"❌ Registration failed: Status {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Registration request failed: {e}")
        return
    
    # Test 3: Login
    login_data = {
        "email": "apitest@example.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Login works")
            token = response.json().get("token")
            user_id_from_login = response.json().get("user_id")
            print(f"   User ID: {user_id_from_login}")
        else:
            print(f"❌ Login failed: Status {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Login request failed: {e}")
        return
    
    # Test 4: Create candidate profile
    if user_id_from_login:
        candidate_data = {
            "candidate_id": user_id_from_login,
            "resume": "Test resume for API testing",
            "parsed_resume": {
                "skills": ["Python", "FastAPI", "Testing"],
                "experience": ["Software Development"]
            }
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/candidates/",
                json=candidate_data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            )
            
            if response.status_code == 200:
                print("✅ Candidate profile creation works")
            elif response.status_code == 400 and "already exists" in response.text:
                print("ℹ️  Candidate profile already exists")
            else:
                print(f"❌ Candidate creation failed: Status {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Candidate creation request failed: {e}")
    
    # Test 5: Get candidate profile
    if user_id_from_login:
        try:
            response = requests.get(
                f"{BASE_URL}/candidates/{user_id_from_login}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                print("✅ Get candidate profile works")
                profile = response.json()
                print(f"   Resume length: {len(profile.get('resume', ''))}")
            else:
                print(f"❌ Get profile failed: Status {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Get profile request failed: {e}")
    
    # Test 6: Create recruiter and test recruiter access
    recruiter_data = {
        "name": "Test Recruiter",
        "email": "recruiter@test.com",
        "password": "recruiter123",
        "role": "recruiter"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=recruiter_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Login as recruiter
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": "recruiter@test.com", "password": "recruiter123"},
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code == 200:
            recruiter_token = login_response.json().get("token")
            
            # Test list all candidates
            list_response = requests.get(
                f"{BASE_URL}/candidates/",
                headers={"Authorization": f"Bearer {recruiter_token}"}
            )
            
            if list_response.status_code == 200:
                candidates = list_response.json()
                print(f"✅ Recruiter can list candidates (found {len(candidates)})")
            else:
                print(f"❌ Recruiter list failed: {list_response.status_code}")
        
    except Exception as e:
        print(f"ℹ️  Recruiter test: {e}")
    
    print("\n🎯 API Test Summary:")
    print("   Core authentication and candidate endpoints appear to be working!")

if __name__ == "__main__":
    test_api()
