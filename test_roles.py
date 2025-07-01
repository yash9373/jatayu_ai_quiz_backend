import requests
import json

# Test role-based endpoints
base_url = "http://localhost:8000"

def test_role_based_endpoints():
    """Test role-based access control"""
    
    # Login as candidate
    candidate_login = {
        "email": "john@example.com",
        "password": "password123"
    }
    
    response = requests.post(f"{base_url}/auth/login", json=candidate_login)
    candidate_token = response.json()["token"]
    candidate_headers = {"Authorization": f"Bearer {candidate_token}"}
    
    # Login as recruiter
    recruiter_login = {
        "email": "jane@example.com",
        "password": "password123"
    }
    
    response = requests.post(f"{base_url}/auth/login", json=recruiter_login)
    recruiter_token = response.json()["token"]
    recruiter_headers = {"Authorization": f"Bearer {recruiter_token}"}
    
    # Test candidate-only endpoint with candidate token
    print("Testing candidate-only endpoint with candidate token:")
    response = requests.get(f"{base_url}/auth/candidate-only", headers=candidate_headers)
    print(f"Status: {response.status_code}, Response: {response.json()}")
    
    # Test candidate-only endpoint with recruiter token (should fail)
    print("Testing candidate-only endpoint with recruiter token:")
    response = requests.get(f"{base_url}/auth/candidate-only", headers=recruiter_headers)
    print(f"Status: {response.status_code}, Response: {response.json()}")
    
    # Test recruiter-only endpoint with recruiter token
    print("Testing recruiter-only endpoint with recruiter token:")
    response = requests.get(f"{base_url}/auth/recruiter-only", headers=recruiter_headers)
    print(f"Status: {response.status_code}, Response: {response.json()}")
    
    # Test recruiter-only endpoint with candidate token (should fail)
    print("Testing recruiter-only endpoint with candidate token:")
    response = requests.get(f"{base_url}/auth/recruiter-only", headers=candidate_headers)
    print(f"Status: {response.status_code}, Response: {response.json()}")

if __name__ == "__main__":
    print("Testing role-based access control...")
    test_role_based_endpoints()
