#!/usr/bin/env python3
"""
Comprehensive Candidate API Assessment
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def comprehensive_test():
    print("🎯 Comprehensive Candidate API Assessment")
    print("=" * 50)
    
    results = []
    
    # Helper function to record results
    def record_test(name, success, details=""):
        status = "✅ PASS" if success else "❌ FAIL"
        results.append({"name": name, "success": success, "details": details})
        print(f"{status} {name}")
        if details:
            print(f"    {details}")
    
    # Test 1: Server Health
    try:
        response = requests.get(f"{BASE_URL}/docs")
        record_test("Server Health", response.status_code == 200)
    except:
        record_test("Server Health", False, "Server not accessible")
        return results
    
    # Test 2: User Registration (Candidate)
    candidate_data = {
        "name": "Assessment Candidate",
        "email": "assessment_candidate@test.com",
        "password": "test123",
        "role": "candidate"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=candidate_data)
        if response.status_code == 200:
            candidate_user_id = response.json().get("user_id")
            record_test("Candidate Registration", True, f"User ID: {candidate_user_id}")
        elif "already exists" in response.text:
            record_test("Candidate Registration", True, "User already exists")
            candidate_user_id = None
        else:
            record_test("Candidate Registration", False, f"Status: {response.status_code}")
            candidate_user_id = None
    except Exception as e:
        record_test("Candidate Registration", False, str(e))
        candidate_user_id = None
    
    # Test 3: User Registration (Recruiter)
    recruiter_data = {
        "name": "Assessment Recruiter",
        "email": "assessment_recruiter@test.com",
        "password": "recruiter123",
        "role": "recruiter"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=recruiter_data)
        record_test("Recruiter Registration", 
                   response.status_code == 200 or "already exists" in response.text)
    except Exception as e:
        record_test("Recruiter Registration", False, str(e))
    
    # Test 4: Candidate Login
    try:
        response = requests.post(f"{BASE_URL}/auth/login", 
                               json={"email": "assessment_candidate@test.com", "password": "test123"})
        if response.status_code == 200:
            candidate_token = response.json().get("token")
            candidate_user_id = response.json().get("user_id")
            record_test("Candidate Login", True, f"Token received, User ID: {candidate_user_id}")
        else:
            record_test("Candidate Login", False, f"Status: {response.status_code}")
            candidate_token = None
    except Exception as e:
        record_test("Candidate Login", False, str(e))
        candidate_token = None
    
    # Test 5: Recruiter Login
    try:
        response = requests.post(f"{BASE_URL}/auth/login", 
                               json={"email": "assessment_recruiter@test.com", "password": "recruiter123"})
        if response.status_code == 200:
            recruiter_token = response.json().get("token")
            record_test("Recruiter Login", True, "Token received")
        else:
            record_test("Recruiter Login", False, f"Status: {response.status_code}")
            recruiter_token = None
    except Exception as e:
        record_test("Recruiter Login", False, str(e))
        recruiter_token = None
    
    # Test 6: Create Candidate Profile
    if candidate_token and candidate_user_id:
        profile_data = {
            "candidate_id": int(candidate_user_id),
            "resume": "Experienced software developer with expertise in Python, FastAPI, and database design. Strong background in API development and testing.",
            "parsed_resume": {
                "personal_info": {
                    "name": "Assessment Candidate",
                    "email": "assessment_candidate@test.com"
                },
                "skills": ["Python", "FastAPI", "PostgreSQL", "API Development", "Testing"],
                "experience": [
                    {
                        "company": "Tech Company",
                        "position": "Software Developer",
                        "duration": "2022-2024"
                    }
                ]
            }
        }
        
        try:
            response = requests.post(f"{BASE_URL}/candidates/", 
                                   json=profile_data,
                                   headers={"Authorization": f"Bearer {candidate_token}"})
            success = response.status_code == 200 or "already exists" in response.text
            record_test("Create Candidate Profile", success, 
                       f"Status: {response.status_code}")
        except Exception as e:
            record_test("Create Candidate Profile", False, str(e))
    
    # Test 7: Get Own Profile (Candidate)
    if candidate_token and candidate_user_id:
        try:
            response = requests.get(f"{BASE_URL}/candidates/{candidate_user_id}",
                                  headers={"Authorization": f"Bearer {candidate_token}"})
            if response.status_code == 200:
                profile = response.json()
                has_resume = bool(profile.get("resume"))
                has_parsed = bool(profile.get("parsed_resume"))
                record_test("Get Own Profile", True, 
                           f"Has resume: {has_resume}, Has parsed data: {has_parsed}")
            else:
                record_test("Get Own Profile", False, f"Status: {response.status_code}")
        except Exception as e:
            record_test("Get Own Profile", False, str(e))
    
    # Test 8: Update Profile (Candidate)
    if candidate_token and candidate_user_id:
        update_data = {
            "resume": "UPDATED: Senior software developer with advanced expertise in Python, FastAPI, microservices, and cloud technologies.",
            "parsed_resume": {
                "personal_info": {
                    "name": "Assessment Candidate",
                    "email": "assessment_candidate@test.com"
                },
                "skills": ["Python", "FastAPI", "PostgreSQL", "API Development", "Testing", "Docker", "AWS"],
                "experience": [
                    {
                        "company": "Tech Company",
                        "position": "Senior Software Developer",
                        "duration": "2022-2024"
                    }
                ]
            }
        }
        
        try:
            response = requests.put(f"{BASE_URL}/candidates/{candidate_user_id}",
                                  json=update_data,
                                  headers={"Authorization": f"Bearer {candidate_token}"})
            record_test("Update Profile", response.status_code == 200,
                       f"Status: {response.status_code}")
        except Exception as e:
            record_test("Update Profile", False, str(e))
    
    # Test 9: Recruiter View Profile
    if recruiter_token and candidate_user_id:
        try:
            response = requests.get(f"{BASE_URL}/candidates/{candidate_user_id}",
                                  headers={"Authorization": f"Bearer {recruiter_token}"})
            record_test("Recruiter View Profile", response.status_code == 200,
                       f"Status: {response.status_code}")
        except Exception as e:
            record_test("Recruiter View Profile", False, str(e))
    
    # Test 10: List All Candidates (Recruiter)
    if recruiter_token:
        try:
            response = requests.get(f"{BASE_URL}/candidates/",
                                  headers={"Authorization": f"Bearer {recruiter_token}"})
            if response.status_code == 200:
                candidates = response.json()
                record_test("List All Candidates", True, 
                           f"Found {len(candidates)} candidates")
            else:
                record_test("List All Candidates", False, f"Status: {response.status_code}")
        except Exception as e:
            record_test("List All Candidates", False, str(e))
    
    # Test 11: Security - Candidate Cannot List All
    if candidate_token:
        try:
            response = requests.get(f"{BASE_URL}/candidates/",
                                  headers={"Authorization": f"Bearer {candidate_token}"})
            record_test("Security: Candidate Cannot List All", 
                       response.status_code == 403,
                       f"Status: {response.status_code} (should be 403)")
        except Exception as e:
            record_test("Security: Candidate Cannot List All", False, str(e))
    
    # Test 12: Unauthenticated Access Blocked
    try:
        response = requests.get(f"{BASE_URL}/candidates/")
        record_test("Security: Unauthenticated Blocked", 
                   response.status_code == 401,
                   f"Status: {response.status_code} (should be 401)")
    except Exception as e:
        record_test("Security: Unauthenticated Blocked", False, str(e))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Assessment Summary")
    print("=" * 50)
    
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    failed = total - passed
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if failed > 0:
        print(f"\n❌ Failed Tests:")
        for result in results:
            if not result["success"]:
                print(f"  - {result['name']}: {result['details']}")
    
    print(f"\n🎉 Candidate API Assessment Complete!")
    print(f"{'🟢 All tests passed!' if failed == 0 else '🟡 Some tests failed - check details above'}")
    
    return results

if __name__ == "__main__":
    comprehensive_test()
