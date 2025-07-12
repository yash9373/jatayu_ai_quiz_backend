import requests
import json

# Test the Test API endpoints
base_url = "http://localhost:8000"

def test_test_api():
    """Test the complete Test API functionality"""
    
    print("=" * 60)
    print("TESTING TEST API ENDPOINTS")
    print("=" * 60)
    
    # Step 1: Register users
    print("\n1. Registering test users...")
    
    # Register a recruiter
    recruiter_data = {
        "name": "Alice Recruiter",
        "email": "alice@company.com",
        "password": "password123",
        "role": "recruiter"
    }
    
    response = requests.post(f"{base_url}/auth/register", json=recruiter_data)
    print(f"Recruiter Registration: {response.status_code}")
    
    # Register a candidate
    candidate_data = {
        "name": "Bob Candidate",
        "email": "bob@email.com",
        "password": "password123",
        "role": "candidate"
    }
    
    response = requests.post(f"{base_url}/auth/register", json=candidate_data)
    print(f"Candidate Registration: {response.status_code}")
    
    # Step 2: Login users
    print("\n2. Logging in users...")
    
    # Login recruiter
    recruiter_login = {
        "email": "alice@company.com",
        "password": "password123"
    }
    response = requests.post(f"{base_url}/auth/login", json=recruiter_login)
    recruiter_token = response.json()["token"]
    recruiter_headers = {"Authorization": f"Bearer {recruiter_token}"}
    print(f"Recruiter Login: {response.status_code}")
    
    # Login candidate
    candidate_login = {
        "email": "bob@email.com",
        "password": "password123"
    }
    response = requests.post(f"{base_url}/auth/login", json=candidate_login)
    candidate_token = response.json()["token"]
    candidate_headers = {"Authorization": f"Bearer {candidate_token}"}
    print(f"Candidate Login: {response.status_code}")
    
    # Step 3: Create tests (recruiter only)
    print("\n3. Creating tests...")
    
    test_data1 = {
        "name": "Python Developer Assessment",
        "text": "Complete the following Python coding challenges...",
        "job_description": "We are looking for a Python developer with 3+ years experience"
    }
    
    response = requests.post(f"{base_url}/tests/", json=test_data1, headers=recruiter_headers)
    print(f"Create Test (Recruiter): {response.status_code}")
    if response.status_code == 200:
        test1_id = response.json()["test_id"]
        print(f"Created Test ID: {test1_id}")
    
    # Try creating test as candidate (should fail)
    response = requests.post(f"{base_url}/tests/", json=test_data1, headers=candidate_headers)
    print(f"Create Test (Candidate - should fail): {response.status_code}")
    
    # Step 4: Get all tests
    print("\n4. Getting all tests...")
    
    response = requests.get(f"{base_url}/tests/", headers=recruiter_headers)
    print(f"Get All Tests (Recruiter): {response.status_code}")
    if response.status_code == 200:
        tests = response.json()
        print(f"Number of tests: {len(tests)}")
        for test in tests:
            print(f"  - {test['name']} (ID: {test['test_id']})")
    
    response = requests.get(f"{base_url}/tests/", headers=candidate_headers)
    print(f"Get All Tests (Candidate): {response.status_code}")
    
    # Step 5: Get specific test
    print("\n5. Getting specific test...")
    
    if 'test1_id' in locals():
        response = requests.get(f"{base_url}/tests/{test1_id}", headers=recruiter_headers)
        print(f"Get Test by ID (Recruiter): {response.status_code}")
        if response.status_code == 200:
            test_detail = response.json()
            print(f"Test Details: {test_detail['name']}")
            print(f"Created by: {test_detail['creator_name']} ({test_detail['creator_role']})")
        
        response = requests.get(f"{base_url}/tests/{test1_id}", headers=candidate_headers)
        print(f"Get Test by ID (Candidate): {response.status_code}")
    
    # Step 6: Update test
    print("\n6. Updating test...")
    
    if 'test1_id' in locals():
        update_data = {
            "name": "Advanced Python Developer Assessment",
            "text": "Updated test content with more challenges..."
        }
        
        response = requests.put(f"{base_url}/tests/{test1_id}", json=update_data, headers=recruiter_headers)
        print(f"Update Test (Recruiter): {response.status_code}")
        
        # Try updating as candidate (should fail)
        response = requests.put(f"{base_url}/tests/{test1_id}", json=update_data, headers=candidate_headers)
        print(f"Update Test (Candidate - should fail): {response.status_code}")
    
    # Step 7: Get my tests
    print("\n7. Getting my tests...")
    
    response = requests.get(f"{base_url}/tests/my-tests", headers=recruiter_headers)
    print(f"Get My Tests (Recruiter): {response.status_code}")
    if response.status_code == 200:
        my_tests = response.json()
        print(f"Recruiter's tests: {len(my_tests)}")
    
    response = requests.get(f"{base_url}/tests/my-tests", headers=candidate_headers)
    print(f"Get My Tests (Candidate): {response.status_code}")
    if response.status_code == 200:
        my_tests = response.json()
        print(f"Candidate's tests: {len(my_tests)}")
    
    # Step 8: Recruiter-only endpoint
    print("\n8. Testing recruiter-only endpoint...")
    
    response = requests.get(f"{base_url}/tests/recruiter/all", headers=recruiter_headers)
    print(f"Recruiter-only endpoint (Recruiter): {response.status_code}")
    
    response = requests.get(f"{base_url}/tests/recruiter/all", headers=candidate_headers)
    print(f"Recruiter-only endpoint (Candidate - should fail): {response.status_code}")
    
    print("\n" + "=" * 60)
    print("TEST API TESTING COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_test_api()
