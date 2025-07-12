import requests
import json

# Test the updated API endpoints
base_url = "http://localhost:8000"

def test_register():
    """Test user registration with new schema"""
    url = f"{base_url}/auth/register"
    
    # Test candidate registration
    candidate_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "password123",
        "role": "candidate"
    }
    
    response = requests.post(url, json=candidate_data)
    print(f"Candidate Registration Response: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    # Test recruiter registration
    recruiter_data = {
        "name": "Jane Smith",
        "email": "jane@example.com",
        "password": "password123",
        "role": "recruiter"
    }
    
    response = requests.post(url, json=recruiter_data)
    print(f"Recruiter Registration Response: {response.status_code}")
    print(f"Response body: {response.json()}")

def test_login():
    """Test user login"""
    url = f"{base_url}/auth/login"
    
    login_data = {
        "email": "john@example.com",
        "password": "password123"
    }
    
    response = requests.post(url, json=login_data)
    print(f"Login Response: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    if response.status_code == 200:
        return response.json()["token"]
    return None

def test_me_endpoint(token):
    """Test the /me endpoint"""
    url = f"{base_url}/auth/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    print(f"Me Endpoint Response: {response.status_code}")
    print(f"Response body: {response.json()}")

if __name__ == "__main__":
    print("Testing updated API endpoints...")
    
    # Test registration
    test_register()
    
    # Test login
    token = test_login()
    
    # Test me endpoint
    if token:
        test_me_endpoint(token)
