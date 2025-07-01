import requests
import json

# Test that candidates are completely blocked from Test APIs
base_url = "http://localhost:8000"

def test_candidate_blocked_from_tests():
    """Test that candidates have NO access to any test endpoints"""
    
    print("=" * 70)
    print("TESTING CANDIDATE ACCESS RESTRICTION TO ALL TEST APIS")
    print("=" * 70)
    
    # Register and login candidate
    print("\n1. Setting up candidate user...")
    
    candidate_data = {
        "name": "Charlie Candidate",
        "email": "charlie@test.com",
        "password": "password123",
        "role": "candidate"
    }
    
    response = requests.post(f"{base_url}/auth/register", json=candidate_data)
    print(f"Candidate Registration: {response.status_code}")
    
    candidate_login = {
        "email": "charlie@test.com",
        "password": "password123"
    }
    response = requests.post(f"{base_url}/auth/login", json=candidate_login)
    candidate_token = response.json()["token"]
    candidate_headers = {"Authorization": f"Bearer {candidate_token}"}
    print(f"Candidate Login: {response.status_code}")
    
    # Register and login recruiter (for creating test data)
    print("\n2. Setting up recruiter user...")
    
    recruiter_data = {
        "name": "David Recruiter",
        "email": "david@company.com",
        "password": "password123",
        "role": "recruiter"
    }
    
    response = requests.post(f"{base_url}/auth/register", json=recruiter_data)
    print(f"Recruiter Registration: {response.status_code}")
    
    recruiter_login = {
        "email": "david@company.com",
        "password": "password123"
    }
    response = requests.post(f"{base_url}/auth/login", json=recruiter_login)
    recruiter_token = response.json()["token"]
    recruiter_headers = {"Authorization": f"Bearer {recruiter_token}"}
    print(f"Recruiter Login: {response.status_code}")
    
    # Create a test as recruiter for testing access
    test_data = {
        "name": "Sample Test for Access Testing",
        "text": "This is a test to verify access control",
        "job_description": "Test job description"
    }
    
    response = requests.post(f"{base_url}/tests/", json=test_data, headers=recruiter_headers)
    test_id = response.json()["test_id"] if response.status_code == 200 else 1
    print(f"Test Creation (Recruiter): {response.status_code}")
    
    print("\n3. Testing candidate access to ALL test endpoints...")
    print("All should return 403 Forbidden:")
    
    # Test all endpoints with candidate token
    test_endpoints = [
        ("POST", f"{base_url}/tests/", "Create Test"),
        ("GET", f"{base_url}/tests/", "Get All Tests"),
        ("GET", f"{base_url}/tests/my-tests", "Get My Tests"),
        ("GET", f"{base_url}/tests/{test_id}", "Get Test by ID"),
        ("PUT", f"{base_url}/tests/{test_id}", "Update Test"),
        ("DELETE", f"{base_url}/tests/{test_id}", "Delete Test"),
        ("GET", f"{base_url}/tests/recruiter/all", "Recruiter-only Endpoint")
    ]
    
    all_blocked = True
    
    for method, url, description in test_endpoints:
        if method == "POST":
            response = requests.post(url, json=test_data, headers=candidate_headers)
        elif method == "PUT":
            update_data = {"name": "Updated Test Name"}
            response = requests.put(url, json=update_data, headers=candidate_headers)
        else:
            response = requests.get(url, headers=candidate_headers) if method == "GET" else requests.delete(url, headers=candidate_headers)
        
        status_code = response.status_code
        access_blocked = status_code == 403
        status_emoji = "✅" if access_blocked else "❌"
        
        print(f"  {status_emoji} {description}: {status_code} {'(BLOCKED)' if access_blocked else '(ALLOWED - SECURITY ISSUE!)'}")
        
        if not access_blocked:
            all_blocked = False
            print(f"      ERROR: Response: {response.text}")
    
    print("\n4. Verification with recruiter access...")
    print("These should work for recruiters:")
    
    # Verify recruiter can access
    recruiter_endpoints = [
        ("GET", f"{base_url}/tests/", "Get All Tests"),
        ("GET", f"{base_url}/tests/{test_id}", "Get Test by ID"),
    ]
    
    for method, url, description in recruiter_endpoints:
        response = requests.get(url, headers=recruiter_headers)
        status_code = response.status_code
        access_granted = status_code == 200
        status_emoji = "✅" if access_granted else "❌"
        
        print(f"  {status_emoji} {description} (Recruiter): {status_code}")
    
    print("\n" + "=" * 70)
    if all_blocked:
        print("🔒 SECURITY VERIFICATION PASSED: All test endpoints properly blocked for candidates")
    else:
        print("⚠️  SECURITY ISSUE: Some endpoints are accessible to candidates!")
    print("=" * 70)
    
    return all_blocked

if __name__ == "__main__":
    test_candidate_blocked_from_tests()
