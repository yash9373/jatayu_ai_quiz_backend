#!/usr/bin/env python3
"""
Test script for Assessment API endpoints
This will help you verify that your Assessment API is working correctly
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def test_login_and_get_token():
    """Login as recruiter to get authentication token"""
    print("🔐 Testing Login...")
    
    login_data = {
        "email": "recruiter@company.com",
        "password": "recruiter123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Login Status: {response.status_code}")
        
        if response.status_code == 200:
            token = response.json()["token"]
            print("✅ Login successful!")
            return token
        else:
            print(f"❌ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_create_candidate():
    """Create a test candidate user"""
    print("\n👤 Creating test candidate...")
    
    candidate_data = {
        "name": "Test Candidate",
        "email": "candidate@example.com",
        "password": "candidate123",
        "role": "candidate"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=candidate_data)
        print(f"Candidate creation status: {response.status_code}")
        
        if response.status_code == 200:
            user_id = response.json()["user_id"]
            print(f"✅ Candidate created with ID: {user_id}")
            return user_id
        else:
            print(f"❌ Candidate creation failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Candidate creation error: {e}")
        return None

def test_create_test(token):
    """Create a test that can be used for assessments"""
    print("\n📝 Creating test for assessments...")
    
    headers = {"Authorization": f"Bearer {token}"}
    test_data = {
        "test_name": "Python Assessment Test",
        "job_description": "Assessment for Python developer position",
        "parsed_job_description": {
            "skills": ["Python", "FastAPI", "SQLAlchemy"],
            "level": "Mid-Level",
            "experience": "2-5 years"
        },
        "skill_graph": {
            "technical": {
                "python": {"weight": 0.4, "max_score": 100},
                "web_frameworks": {"weight": 0.3, "max_score": 100},
                "databases": {"weight": 0.3, "max_score": 100}
            }
        },
        "scheduled_at": "2025-07-15T10:00:00"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/tests/", json=test_data, headers=headers)
        print(f"Test creation status: {response.status_code}")
        
        if response.status_code == 200:
            test_id = response.json()["test_id"]
            print(f"✅ Test created with ID: {test_id}")
            return test_id
        else:
            print(f"❌ Test creation failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Test creation error: {e}")
        return None

def test_start_assessment(token, test_id, candidate_id):
    """Test starting an assessment"""
    print(f"\n🚀 Starting assessment for test {test_id} and candidate {candidate_id}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    assessment_data = {
        "test_id": test_id,
        "candidate_id": candidate_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/assessments/", json=assessment_data, headers=headers)
        print(f"Assessment start status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            assessment_id = result["assessment_id"]
            print(f"✅ Assessment started with ID: {assessment_id}")
            print(f"Started at: {result['started_at']}")
            print(f"Test: {result['test_name']}")
            print(f"Candidate: {result['candidate_name']}")
            return assessment_id
        else:
            print(f"❌ Assessment start failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Assessment start error: {e}")
        return None

def test_update_assessment(token, assessment_id):
    """Test updating assessment with scores and remarks"""
    print(f"\n📊 Updating assessment {assessment_id} with scores...")
    
    headers = {"Authorization": f"Bearer {token}"}
    update_data = {
        "remark": "Candidate showed good understanding of Python fundamentals. Strong problem-solving skills demonstrated.",
        "resume_score": 85,
        "skill_graph": {
            "python": {"score": 88, "notes": "Excellent knowledge of Python syntax and best practices"},
            "web_frameworks": {"score": 75, "notes": "Good understanding of FastAPI, needs more experience with advanced features"},
            "databases": {"score": 70, "notes": "Basic SQL knowledge, could improve on complex queries"},
            "overall_assessment": {
                "strengths": ["Problem solving", "Code quality", "Communication"],
                "areas_for_improvement": ["Database optimization", "Testing practices"]
            }
        },
        "score": 78
    }
    
    try:
        response = requests.put(f"{BASE_URL}/assessments/{assessment_id}", json=update_data, headers=headers)
        print(f"Assessment update status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Assessment updated successfully!")
            print(f"Overall Score: {result['score']}")
            print(f"Resume Score: {result['resume_score']}")
            print(f"Remark: {result['remark'][:100]}...")
            return True
        else:
            print(f"❌ Assessment update failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Assessment update error: {e}")
        return False

def test_get_assessment(token, assessment_id):
    """Test retrieving assessment details"""
    print(f"\n📋 Retrieving assessment {assessment_id}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/assessments/{assessment_id}", headers=headers)
        print(f"Assessment retrieval status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Assessment retrieved successfully!")
            print(f"Assessment ID: {result['assessment_id']}")
            print(f"Test: {result['test_name']}")
            print(f"Candidate: {result['candidate_name']} ({result['candidate_email']})")
            print(f"Started: {result['started_at']}")
            print(f"Scores - Overall: {result['score']}, Resume: {result['resume_score']}")
            
            if result['skill_graph']:
                print("Skill Assessment:")
                for skill, data in result['skill_graph'].items():
                    if isinstance(data, dict) and 'score' in data:
                        print(f"  {skill}: {data['score']}")
            
            return True
        else:
            print(f"❌ Assessment retrieval failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Assessment retrieval error: {e}")
        return False

def test_list_assessments(token):
    """Test listing all assessments"""
    print(f"\n📊 Listing all assessments...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/assessments/", headers=headers)
        print(f"Assessment list status: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Found {len(results)} assessments")
            
            for assessment in results:
                print(f"  ID: {assessment['assessment_id']} - {assessment['test_name']} - {assessment['candidate_name']} - Score: {assessment.get('score', 'Not scored')}")
            
            return True
        else:
            print(f"❌ Assessment list failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Assessment list error: {e}")
        return False

def test_server_status():
    """Check if server is running"""
    print("🌐 Checking server status...")
    
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ Server is running!")
            return True
        else:
            print(f"❌ Server responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server is not accessible: {e}")
        print("Make sure to start the server with: uvicorn main:app --reload")
        return False

def main():
    """Run all assessment API tests"""
    print("🧪 Assessment API Test Suite")
    print("=" * 50)
    
    # Check server
    if not test_server_status():
        return
    
    # Login
    token = test_login_and_get_token()
    if not token:
        print("❌ Cannot proceed without authentication")
        return
    
    # Create candidate
    candidate_id = test_create_candidate()
    if not candidate_id:
        print("❌ Cannot proceed without candidate")
        return
    
    # Create test
    test_id = test_create_test(token)
    if not test_id:
        print("❌ Cannot proceed without test")
        return
    
    # Start assessment
    assessment_id = test_start_assessment(token, test_id, candidate_id)
    if not assessment_id:
        print("❌ Cannot proceed without assessment")
        return
    
    # Update assessment
    if not test_update_assessment(token, assessment_id):
        print("❌ Assessment update failed")
        return
    
    # Get assessment
    if not test_get_assessment(token, assessment_id):
        print("❌ Assessment retrieval failed")
        return
    
    # List assessments
    if not test_list_assessments(token):
        print("❌ Assessment listing failed")
        return
    
    print("\n🎉 All Assessment API tests completed successfully!")
    print("\n📋 Summary of what was tested:")
    print("✅ Server connectivity")
    print("✅ User authentication")
    print("✅ Candidate creation")
    print("✅ Test creation")
    print("✅ Assessment start")
    print("✅ Assessment update (scores, remarks)")
    print("✅ Assessment retrieval")
    print("✅ Assessment listing")
    print("\n🏆 Your Assessment API is working correctly!")

if __name__ == "__main__":
    main()
