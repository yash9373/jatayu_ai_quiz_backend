#!/usr/bin/env python3
"""Test AI processing in test creation"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_create_test_with_ai():
    """Test test creation with AI processing"""
    
    # First create a recruiter and login
    print("1. Creating recruiter...")
    unique_email = f"airecruiter_{int(time.time())}@test.com"
    register_data = {
        "name": "AI Test Recruiter",
        "email": unique_email,
        "password": "TestPass123!",
        "role": "recruiter"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print(f"Register Status: {response.status_code}")
    if response.status_code not in [200, 201]:
        print(f"Register failed: {response.text}")
        return
    
    # Login
    print("2. Logging in...")
    login_data = {
        "email": unique_email,
        "password": "TestPass123!"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Login Status: {response.status_code}")
    
    if response.status_code == 200:
        login_result = response.json()
        print(f"Login response: {login_result}")
        token = login_result.get("token") or login_result.get("access_token")
        if not token:
            print("❌ Login did not return a usable token. Full response above.")
            return
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test with job description
        print("3. Creating test with job description...")
        test_data = {
            "test_name": "Python Developer Test",
            "job_description": """
            We are looking for a Python Developer with the following requirements:
            - 3+ years of experience in Python development
            - Strong knowledge of Django and Flask frameworks
            - Experience with PostgreSQL and MongoDB databases
            - Familiarity with AWS cloud services
            - Knowledge of REST API development
            - Experience with Git version control
            - Understanding of Agile methodologies
            - Bachelor's degree in Computer Science or related field
            """,
            "total_questions": 20,
            "time_limit_minutes": 60,
            "total_marks": 100,
            "resume_score_threshold": 70,
            "max_shortlisted_candidates": 50,
            "auto_shortlist": True
        }
        
        response = requests.post(f"{BASE_URL}/tests", json=test_data, headers=headers)
        print(f"Create Test Status: {response.status_code}")
        
        if response.status_code == 201:
            test_result = response.json()
            print(f"Test created successfully!")
            print(f"Test ID: {test_result['test_id']}")
            print(f"Test Name: {test_result['test_name']}")
            print(f"Parsed Job Description: {test_result['parsed_job_description']}")
            print(f"Skill Graph: {test_result['skill_graph']}")
            
            # Check if AI processing worked
            if test_result['parsed_job_description'] is not None:
                print("✅ AI processing successful - parsed_job_description is populated")
            else:
                print("❌ AI processing failed - parsed_job_description is null")
                
            if test_result['skill_graph'] is not None:
                print("✅ AI processing successful - skill_graph is populated")
            else:
                print("❌ AI processing failed - skill_graph is null")
                
        else:
            print(f"Failed to create test: {response.text}")
    else:
        print(f"Login failed: {response.text}")

if __name__ == "__main__":
    test_create_test_with_ai()
