"""
Complete test script that creates users, authenticates, and creates tests
Run this script to set up and test your backend completely
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"

# Test data
RECRUITER_DATA = {
    "name": "John Recruiter",
    "email": "recruiter_test@example.com",
    "password": "password123",
    "role": "recruiter"
}

CANDIDATE_DATA = {
    "name": "Jane Candidate",
    "email": "candidate_test@example.com", 
    "password": "password123",
    "role": "candidate"
}

TEST_DATA = {
    "test_name": "Senior Python Developer Position",
    "job_description": """
We are looking for a Senior Python Developer with 5+ years of experience to join our dynamic team.

Required Skills:
- Python programming (Django/FastAPI)
- PostgreSQL database management
- AWS cloud services
- Docker containerization
- Git version control
- REST API development

Preferred Skills:
- Machine Learning libraries (scikit-learn, pandas)
- React frontend development
- Kubernetes orchestration
- CI/CD pipelines

Responsibilities:
- Design and develop scalable backend services
- Collaborate with frontend developers
- Optimize database performance
- Deploy applications to AWS
- Mentor junior developers

Requirements:
- Bachelor's degree in Computer Science or related field
- 5+ years of Python development experience
- Strong problem-solving skills
- Excellent communication abilities
    """,
    "scheduled_at": "2025-07-15T10:00:00Z"
}

def register_user(user_data: dict):
    """Register a new user"""
    print(f"🔧 Registering user: {user_data['email']} as {user_data['role']}")
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ User registered successfully: ID {result['user_id']}")
        return result["user_id"]
    elif response.status_code == 400 and "already registered" in response.text.lower():
        print(f"ℹ️  User already exists: {user_data['email']}")
        return True  # User exists, continue
    else:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return None

def login_user(email: str, password: str):
    """Login user and get token"""
    print(f"🔐 Logging in user: {email}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        result = response.json()
        token = result["access_token"]
        print(f"✅ Login successful for {email}")
        return token
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def get_headers(token: str):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {token}"}

def create_test(test_data: dict, token: str):
    """Create a new test"""
    print(f"📝 Creating test: {test_data['test_name']}")
    
    headers = get_headers(token)
    response = requests.post(f"{BASE_URL}/tests/", json=test_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        test_id = result["test_id"]
        print(f"✅ Test created successfully: ID {test_id}")
        print(f"   Test Name: {result['test_name']}")
        print(f"   Created At: {result['created_at']}")
        return test_id
    else:
        print(f"❌ Test creation failed: {response.status_code} - {response.text}")
        return None

def get_test_details(test_id: int, token: str):
    """Get test details to check AI processing"""
    print(f"📊 Getting test details for ID: {test_id}")
    
    headers = get_headers(token)
    response = requests.get(f"{BASE_URL}/tests/{test_id}", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Test details retrieved:")
        print(f"   Test Name: {result['test_name']}")
        print(f"   Has Job Description: {bool(result.get('job_description'))}")
        print(f"   Has Parsed JD: {bool(result.get('parsed_job_description'))}")
        print(f"   Has Skill Graph: {bool(result.get('skill_graph'))}")
        print(f"   Creator: {result.get('creator_name', 'Unknown')}")
        return result
    else:
        print(f"❌ Failed to get test details: {response.status_code} - {response.text}")
        return None

def candidate_apply_for_test(test_id: int, token: str):
    """Candidate applies for the test"""
    print(f"📤 Candidate applying for test ID: {test_id}")
    
    application_data = {
        "test_id": test_id,
        "resume_link": "https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit"  # Sample Google Drive link
    }
    
    headers = get_headers(token)
    response = requests.post(f"{BASE_URL}/applications/apply", json=application_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        application_id = result["application_id"]
        print(f"✅ Application submitted successfully: ID {application_id}")
        print(f"   Status: {result['application_status']}")
        print(f"   Applied At: {result['applied_at']}")
        return application_id
    else:
        print(f"❌ Application failed: {response.status_code} - {response.text}")
        return None

def check_applications_for_test(test_id: int, token: str):
    """Recruiter checks applications for test"""
    print(f"👀 Checking applications for test ID: {test_id}")
    
    headers = get_headers(token)
    response = requests.get(f"{BASE_URL}/applications/test/{test_id}", headers=headers)
    
    if response.status_code == 200:
        applications = response.json()
        print(f"✅ Found {len(applications)} applications:")
        for app in applications:
            print(f"   - Application ID: {app['application_id']}")
            print(f"     Candidate: {app['candidate_name']} ({app['candidate_email']})")
            print(f"     Status: {app['application_status']}")
            print(f"     AI Score: {app.get('resume_score', 'Not screened yet')}")
            print(f"     Shortlisted: {app['is_shortlisted']}")
        return applications
    else:
        print(f"❌ Failed to get applications: {response.status_code} - {response.text}")
        return []

def run_ai_screening(test_id: int, token: str):
    """Run AI screening on applications"""
    print(f"🤖 Running AI screening for test ID: {test_id}")
    
    screening_data = {
        "test_id": test_id,
        "min_resume_score": 60
    }
    
    headers = get_headers(token)
    response = requests.post(f"{BASE_URL}/applications/ai-screening/batch", json=screening_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ AI screening completed:")
        print(f"   Total Applications: {result['total_applications']}")
        print(f"   Successful Screenings: {result['successful_screenings']}")
        print(f"   Failed Screenings: {result['failed_screenings']}")
        print(f"   Message: {result['message']}")
        return result
    else:
        print(f"❌ AI screening failed: {response.status_code} - {response.text}")
        return None

def get_analytics(test_id: int, token: str):
    """Get analytics for the test"""
    print(f"📊 Getting analytics for test ID: {test_id}")
    
    headers = get_headers(token)
    response = requests.get(f"{BASE_URL}/applications/analytics/test/{test_id}", headers=headers)
    
    if response.status_code == 200:
        analytics = response.json()
        print(f"✅ Analytics retrieved:")
        print(f"   Total Applications: {analytics['total_applications']}")
        print(f"   Screened Applications: {analytics['screened_applications']}")
        print(f"   Shortlisted Applications: {analytics['shortlisted_applications']}")
        print(f"   Average AI Score: {analytics.get('average_ai_score', 'N/A')}")
        print(f"   Shortlist Rate: {analytics['shortlist_rate']:.1f}%")
        print(f"   Screening Completion: {analytics['screening_completion_rate']:.1f}%")
        return analytics
    else:
        print(f"❌ Failed to get analytics: {response.status_code} - {response.text}")
        return None

def main():
    """Run the complete test workflow"""
    print("🚀 Starting Complete Backend Test")
    print("=" * 50)
    print(f"Testing against: {BASE_URL}")
    print("=" * 50)
    
    try:
        # Step 1: Register users
        print("\n📋 STEP 1: USER REGISTRATION")
        recruiter_id = register_user(RECRUITER_DATA)
        candidate_id = register_user(CANDIDATE_DATA)
        
        if not recruiter_id or not candidate_id:
            print("❌ User registration failed. Cannot continue.")
            return
        
        # Step 2: Login users
        print("\n🔐 STEP 2: USER AUTHENTICATION")
        recruiter_token = login_user(RECRUITER_DATA["email"], RECRUITER_DATA["password"])
        candidate_token = login_user(CANDIDATE_DATA["email"], CANDIDATE_DATA["password"])
        
        if not recruiter_token or not candidate_token:
            print("❌ User authentication failed. Cannot continue.")
            return
        
        # Step 3: Create test (as recruiter)
        print("\n📝 STEP 3: TEST CREATION")
        test_id = create_test(TEST_DATA, recruiter_token)
        
        if not test_id:
            print("❌ Test creation failed. Cannot continue.")
            return
        
        # Step 4: Wait for background AI processing
        print("\n⏳ STEP 4: WAITING FOR BACKGROUND AI PROCESSING")
        print("Waiting 5 seconds for job description parsing...")
        time.sleep(5)
        
        # Step 5: Check test details
        print("\n📊 STEP 5: CHECKING TEST DETAILS")
        test_details = get_test_details(test_id, recruiter_token)
        
        # Step 6: Candidate applies for test
        print("\n📤 STEP 6: CANDIDATE APPLICATION")
        application_id = candidate_apply_for_test(test_id, candidate_token)
        
        if not application_id:
            print("❌ Application failed. Cannot continue.")
            return
        
        # Step 7: Wait for background resume processing
        print("\n⏳ STEP 7: WAITING FOR BACKGROUND RESUME PROCESSING")
        print("Waiting 5 seconds for resume processing...")
        time.sleep(5)
        
        # Step 8: Recruiter checks applications
        print("\n👀 STEP 8: CHECKING APPLICATIONS")
        applications = check_applications_for_test(test_id, recruiter_token)
        
        # Step 9: Run AI screening
        print("\n🤖 STEP 9: AI SCREENING")
        screening_result = run_ai_screening(test_id, recruiter_token)
        
        # Step 10: Get final analytics
        print("\n📊 STEP 10: FINAL ANALYTICS")
        analytics = get_analytics(test_id, recruiter_token)
        
        # Final summary
        print("\n" + "=" * 50)
        print("🎉 COMPLETE BACKEND TEST SUMMARY")
        print("=" * 50)
        print(f"✅ Recruiter created: {RECRUITER_DATA['email']}")
        print(f"✅ Candidate created: {CANDIDATE_DATA['email']}")
        print(f"✅ Test created: ID {test_id}")
        print(f"✅ Application submitted: ID {application_id}")
        print(f"✅ AI screening completed")
        print(f"📊 Final metrics:")
        if analytics:
            print(f"   - Total applications: {analytics['total_applications']}")
            print(f"   - Shortlisted: {analytics['shortlisted_applications']}")
            print(f"   - Average score: {analytics.get('average_ai_score', 'N/A')}")
        print("🎯 All backend operations working correctly!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure your FastAPI server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
