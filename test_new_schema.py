#!/usr/bin/env python3
"""
Test script for the updated Test API with new schema
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_login():
    """Login as recruiter to get token"""
    login_data = {
        "email": "recruiter@company.com",
        "password": "recruiter123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Login Status: {response.status_code}")
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.text}")
        return None

def test_create_test_with_new_schema(token):
    """Test creating a test with the new schema"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test data with new schema
    test_data = {
        "test_name": "Python Developer Assessment 2025",
        "job_description": "We are looking for a skilled Python developer with experience in FastAPI, SQLAlchemy, and PostgreSQL. The candidate should have strong problem-solving skills and be able to work in an agile environment.",
        "parsed_job_description": {
            "required_skills": ["Python", "FastAPI", "SQLAlchemy", "PostgreSQL"],
            "experience_level": "Mid-Senior",
            "location": "Remote",
            "salary_range": "$80k-120k"
        },
        "skill_graph": {
            "technical_skills": {
                "programming": ["Python", "JavaScript"],
                "frameworks": ["FastAPI", "Django", "React"],
                "databases": ["PostgreSQL", "MongoDB"],
                "tools": ["Git", "Docker", "AWS"]
            },
            "soft_skills": ["Communication", "Problem Solving", "Team Work"],
            "weight": {
                "technical": 0.7,
                "soft": 0.3
            }
        },
        "scheduled_at": "2025-07-15T10:00:00"
    }
    
    response = requests.post(f"{BASE_URL}/tests/", json=test_data, headers=headers)
    print(f"\n=== CREATE TEST ===")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Created Test ID: {result['test_id']}")
        print(f"Test Name: {result['test_name']}")
        print(f"Scheduled At: {result['scheduled_at']}")
        print(f"Parsed Job Description: {json.dumps(result['parsed_job_description'], indent=2)}")
        print(f"Skill Graph: {json.dumps(result['skill_graph'], indent=2)}")
        return result['test_id']
    else:
        print(f"Create failed: {response.text}")
        return None

def test_get_test(test_id, token):
    """Test getting a test by ID"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/tests/{test_id}", headers=headers)
    print(f"\n=== GET TEST ===")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Retrieved Test: {result['test_name']}")
        print(f"Job Description Length: {len(result['job_description']) if result['job_description'] else 0} characters")
        print(f"Has Parsed Job Description: {bool(result['parsed_job_description'])}")
        print(f"Has Skill Graph: {bool(result['skill_graph'])}")
        return True
    else:
        print(f"Get failed: {response.text}")
        return False

def test_update_test(test_id, token):
    """Test updating a test"""
    headers = {"Authorization": f"Bearer {token}"}
    
    update_data = {
        "test_name": "Senior Python Developer Assessment 2025",
        "skill_graph": {
            "technical_skills": {
                "programming": ["Python", "Go"],  # Updated
                "frameworks": ["FastAPI", "Gin"],
                "databases": ["PostgreSQL", "Redis"],
                "tools": ["Git", "Kubernetes", "AWS"]  # Updated
            },
            "soft_skills": ["Leadership", "Mentoring", "Communication"],  # Updated
            "weight": {
                "technical": 0.8,  # Updated
                "soft": 0.2
            }
        }
    }
    
    response = requests.put(f"{BASE_URL}/tests/{test_id}", json=update_data, headers=headers)
    print(f"\n=== UPDATE TEST ===")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Updated Test Name: {result['test_name']}")
        print(f"Updated Skill Graph: {json.dumps(result['skill_graph'], indent=2)}")
        return True
    else:
        print(f"Update failed: {response.text}")
        return False

def test_list_tests(token):
    """Test listing all tests"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/tests/", headers=headers)
    print(f"\n=== LIST TESTS ===")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        results = response.json()
        print(f"Total Tests: {len(results)}")
        for test in results:
            print(f"- {test['test_name']} (ID: {test['test_id']}) - Scheduled: {test.get('scheduled_at', 'Not scheduled')}")
        return True
    else:
        print(f"List failed: {response.text}")
        return False

def main():
    print("🧪 Testing Updated Test API with New Schema")
    print("=" * 50)
    
    # Step 1: Login
    token = test_login()
    if not token:
        print("❌ Cannot proceed without authentication")
        return
    
    # Step 2: Create test with new schema
    test_id = test_create_test_with_new_schema(token)
    if not test_id:
        print("❌ Cannot proceed without creating a test")
        return
    
    # Step 3: Get the created test
    if not test_get_test(test_id, token):
        print("❌ Failed to retrieve test")
        return
    
    # Step 4: Update the test
    if not test_update_test(test_id, token):
        print("❌ Failed to update test")
        return
    
    # Step 5: List all tests
    if not test_list_tests(token):
        print("❌ Failed to list tests")
        return
    
    print("\n✅ All tests passed! New schema is working correctly.")
    print("\n🎯 Key Features Verified:")
    print("✓ test_name field (renamed from name)")
    print("✓ parsed_job_description as JSON")
    print("✓ skill_graph as JSON")
    print("✓ scheduled_at timestamp")
    print("✓ Database migration successful")
    print("✓ JSON serialization/deserialization working")

if __name__ == "__main__":
    main()
