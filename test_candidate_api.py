#!/usr/bin/env python3
"""
Comprehensive Test Script for Candidate API

This script tests all the candidate API endpoints with proper authentication
and role-based access control.
"""

import requests
import json
import sys
from typing import Dict, Any

# API Configuration
BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"Content-Type": "application/json"}

class APITester:
    def __init__(self):
        self.recruiter_token = None
        self.candidate_token = None
        self.candidate_id = None
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, token: str = None):
        """Make HTTP request with proper error handling"""
        url = f"{BASE_URL}{endpoint}"
        headers = HEADERS.copy()
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
    
    def setup_users(self):
        """Create test users (recruiter and candidate)"""
        print("\n🔧 Setting up test users...")
        
        # Create recruiter
        recruiter_data = {
            "name": "Test Recruiter",
            "email": "recruiter@testcompany.com",
            "password": "recruiter123",
            "role": "recruiter"
        }
        
        response = self.make_request("POST", "/auth/register", recruiter_data)
        if response and response.status_code == 200:
            self.log_test("Create Recruiter", True, f"Recruiter created")
        else:
            self.log_test("Create Recruiter", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Create candidate
        candidate_data = {
            "name": "Test Candidate",
            "email": "candidate@example.com",
            "password": "candidate123",
            "role": "candidate"
        }
        
        response = self.make_request("POST", "/auth/register", candidate_data)
        if response and response.status_code == 200:
            self.candidate_id = response.json().get("user_id")
            self.log_test("Create Candidate", True, f"Candidate ID: {self.candidate_id}")
        else:
            self.log_test("Create Candidate", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Login recruiter
        login_data = {"email": "recruiter@testcompany.com", "password": "recruiter123"}
        response = self.make_request("POST", "/auth/login", login_data)
        if response and response.status_code == 200:
            self.recruiter_token = response.json().get("token")
            self.log_test("Recruiter Login", True, "Token received")
        else:
            self.log_test("Recruiter Login", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Login candidate
        login_data = {"email": "candidate@example.com", "password": "candidate123"}
        response = self.make_request("POST", "/auth/login", login_data)
        if response and response.status_code == 200:
            self.candidate_token = response.json().get("token")
            self.log_test("Candidate Login", True, "Token received")
        else:
            self.log_test("Candidate Login", False, f"Status: {response.status_code if response else 'No response'}")
    
    def test_candidate_crud(self):
        """Test candidate CRUD operations"""
        print("\n📋 Testing Candidate CRUD Operations...")
        
        # Test 1: Create candidate profile (as candidate)
        candidate_profile_data = {
            "candidate_id": self.candidate_id,
            "resume": "I am a skilled software developer with 3 years of experience in Python, JavaScript, and cloud technologies. I have worked on various projects including web applications, APIs, and data processing systems.",
            "parsed_resume": {
                "personal_info": {
                    "name": "Test Candidate",
                    "email": "candidate@example.com",
                    "phone": "+1-555-0123"
                },
                "experience": [
                    {
                        "company": "Tech Solutions Inc.",
                        "position": "Software Developer",
                        "duration": "2021-2024",
                        "responsibilities": [
                            "Developed REST APIs using Python and FastAPI",
                            "Built responsive web applications with React",
                            "Managed PostgreSQL databases"
                        ]
                    }
                ],
                "skills": [
                    "Python", "JavaScript", "FastAPI", "React", "PostgreSQL", 
                    "Docker", "AWS", "Git", "Linux"
                ],
                "education": [
                    {
                        "degree": "Bachelor of Computer Science",
                        "institution": "University of Technology",
                        "year": "2021"
                    }
                ],
                "certifications": [
                    "AWS Certified Developer Associate",
                    "Python Professional Certification"
                ]
            }
        }
        
        response = self.make_request("POST", "/candidates/", candidate_profile_data, self.candidate_token)
        if response and response.status_code == 200:
            self.log_test("Create Candidate Profile", True, "Profile created successfully")
        else:
            error_detail = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Create Candidate Profile", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_detail}")
        
        # Test 2: Get candidate profile (as candidate - own profile)
        response = self.make_request("GET", f"/candidates/{self.candidate_id}", token=self.candidate_token)
        if response and response.status_code == 200:
            profile_data = response.json()
            has_resume = bool(profile_data.get("resume"))
            has_parsed_resume = bool(profile_data.get("parsed_resume"))
            self.log_test("Get Own Profile (Candidate)", True, f"Resume: {has_resume}, Parsed: {has_parsed_resume}")
        else:
            error_detail = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Get Own Profile (Candidate)", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_detail}")
        
        # Test 3: Update candidate profile (as candidate)
        update_data = {
            "resume": "Updated resume with more recent experience and new skills in cloud computing and microservices architecture.",
            "parsed_resume": {
                "personal_info": {
                    "name": "Test Candidate",
                    "email": "candidate@example.com",
                    "phone": "+1-555-0123"
                },
                "experience": [
                    {
                        "company": "Tech Solutions Inc.",
                        "position": "Senior Software Developer",
                        "duration": "2021-2024",
                        "responsibilities": [
                            "Developed REST APIs using Python and FastAPI",
                            "Built responsive web applications with React",
                            "Managed PostgreSQL databases",
                            "Implemented microservices architecture",
                            "Deployed applications on AWS using Docker"
                        ]
                    }
                ],
                "skills": [
                    "Python", "JavaScript", "FastAPI", "React", "PostgreSQL", 
                    "Docker", "AWS", "Git", "Linux", "Microservices", "Redis"
                ],
                "education": [
                    {
                        "degree": "Bachelor of Computer Science",
                        "institution": "University of Technology",
                        "year": "2021"
                    }
                ],
                "certifications": [
                    "AWS Certified Developer Associate",
                    "AWS Certified Solutions Architect",
                    "Python Professional Certification"
                ]
            }
        }
        
        response = self.make_request("PUT", f"/candidates/{self.candidate_id}", update_data, self.candidate_token)
        if response and response.status_code == 200:
            self.log_test("Update Own Profile (Candidate)", True, "Profile updated successfully")
        else:
            error_detail = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Update Own Profile (Candidate)", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_detail}")
        
        # Test 4: Get candidate profile (as recruiter)
        response = self.make_request("GET", f"/candidates/{self.candidate_id}", token=self.recruiter_token)
        if response and response.status_code == 200:
            profile_data = response.json()
            self.log_test("Get Candidate Profile (Recruiter)", True, f"Can view candidate profile")
        else:
            error_detail = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Get Candidate Profile (Recruiter)", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_detail}")
        
        # Test 5: List all candidates (as recruiter)
        response = self.make_request("GET", "/candidates/", token=self.recruiter_token)
        if response and response.status_code == 200:
            candidates = response.json()
            candidate_count = len(candidates)
            self.log_test("List All Candidates (Recruiter)", True, f"Found {candidate_count} candidates")
        else:
            error_detail = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("List All Candidates (Recruiter)", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_detail}")
    
    def test_security_rules(self):
        """Test security and access control"""
        print("\n🔒 Testing Security and Access Control...")
        
        # Test 1: Candidate cannot list all candidates
        response = self.make_request("GET", "/candidates/", token=self.candidate_token)
        if response and response.status_code == 403:
            self.log_test("Candidate Cannot List All", True, "Properly blocked with 403")
        else:
            self.log_test("Candidate Cannot List All", False, f"Expected 403, got {response.status_code if response else 'No response'}")
        
        # Test 2: Candidate cannot view other candidate's profile
        # (This would require another candidate, so we'll simulate with wrong ID)
        response = self.make_request("GET", f"/candidates/{self.candidate_id + 100}", token=self.candidate_token)
        if response and response.status_code in [403, 404]:
            self.log_test("Candidate Cannot View Others", True, f"Properly blocked with {response.status_code}")
        else:
            self.log_test("Candidate Cannot View Others", False, f"Expected 403/404, got {response.status_code if response else 'No response'}")
        
        # Test 3: Unauthenticated access should be blocked
        response = self.make_request("GET", "/candidates/")
        if response and response.status_code == 401:
            self.log_test("Unauthenticated Access Blocked", True, "Properly blocked with 401")
        else:
            self.log_test("Unauthenticated Access Blocked", False, f"Expected 401, got {response.status_code if response else 'No response'}")
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n🧪 Testing Edge Cases...")
        
        # Test 1: Create duplicate candidate profile
        duplicate_data = {
            "candidate_id": self.candidate_id,
            "resume": "This should fail as profile already exists"
        }
        
        response = self.make_request("POST", "/candidates/", duplicate_data, self.candidate_token)
        if response and response.status_code == 400:
            self.log_test("Duplicate Profile Rejected", True, "Properly rejected duplicate profile")
        else:
            self.log_test("Duplicate Profile Rejected", False, f"Expected 400, got {response.status_code if response else 'No response'}")
        
        # Test 2: Invalid candidate ID
        response = self.make_request("GET", "/candidates/99999", token=self.recruiter_token)
        if response and response.status_code == 404:
            self.log_test("Invalid ID Handled", True, "Properly returned 404 for invalid ID")
        else:
            self.log_test("Invalid ID Handled", False, f"Expected 404, got {response.status_code if response else 'No response'}")
        
        # Test 3: Invalid JSON in parsed_resume
        invalid_update = {
            "parsed_resume": "This should be an object, not a string"
        }
        
        response = self.make_request("PUT", f"/candidates/{self.candidate_id}", invalid_update, self.candidate_token)
        if response and response.status_code == 422:
            self.log_test("Invalid JSON Rejected", True, "Properly rejected invalid JSON structure")
        else:
            self.log_test("Invalid JSON Rejected", False, f"Expected 422, got {response.status_code if response else 'No response'}")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Candidate API Tests...")
        print("=" * 50)
        
        # Check if server is running
        response = self.make_request("GET", "/docs")
        if not response or response.status_code != 200:
            print("❌ Server is not running! Please start the server first:")
            print("   uvicorn main:app --reload")
            return False
        
        self.log_test("Server Health Check", True, "Server is running")
        
        # Run test suites
        self.setup_users()
        self.test_candidate_crud()
        self.test_security_rules()
        self.test_edge_cases()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n🎉 Testing Complete!")
        return failed_tests == 0

if __name__ == "__main__":
    tester = APITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
