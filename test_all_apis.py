"""
Comprehensive API Testing Script for Test Management System
This script creates a recruiter user and tests all test-related APIs
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
headers = {"Content-Type": "application/json"}

class TestAPIClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.headers = headers
        self.access_token = None
        self.recruiter_id = None
        self.recruiter_email = None
        self.recruiter_password = None
        self.test_id = None
        
    def log_response(self, response: requests.Response, test_name: str):
        """Log response details"""
        print(f"\n{'='*50}")
        print(f"TEST: {test_name}")
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response Text: {response.text}")
        print(f"{'='*50}")
        
    def create_recruiter_user(self) -> Dict[str, Any]:
        """Create a recruiter user for testing"""
        import random
        import time
        # Use timestamp to ensure uniqueness
        timestamp = int(time.time())
        random_id = random.randint(1000, 9999)
        
        user_data = {
            "name": f"Test Recruiter {timestamp}",
            "email": f"recruiter{timestamp}_{random_id}@test.com",
            "password": "TestPass123!",
            "role": "recruiter"
        }
        
        response = requests.post(
            f"{self.base_url}/auth/register",
            json=user_data,
            headers=self.headers
        )
        
        self.log_response(response, "Create Recruiter User")
        
        if response.status_code == 200:
            data = response.json()
            self.recruiter_id = data.get("user_id")
            self.recruiter_email = user_data["email"]
            self.recruiter_password = user_data["password"]
            return data
        else:
            print(f"Failed to create recruiter user: {response.text}")
            return None
            
    def login_recruiter(self) -> Dict[str, Any]:
        """Login as recruiter and get access token"""
        login_data = {
            "email": self.recruiter_email,
            "password": self.recruiter_password
        }
        
        response = requests.post(
            f"{self.base_url}/auth/login",
            json=login_data,
            headers=self.headers
        )
        
        self.log_response(response, "Login Recruiter")
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("token")  # Changed from "access_token"
            self.headers["Authorization"] = f"Bearer {self.access_token}"
            return data
        else:
            print(f"Failed to login: {response.text}")
            return None
            
    def create_test(self) -> Dict[str, Any]:
        """Create a new test"""
        test_data = {
            "test_name": "Python Developer Assessment",
            "job_description": "We are looking for a skilled Python developer with experience in FastAPI, SQLAlchemy, and async programming. The ideal candidate should have 3+ years of experience in backend development.",
            "resume_score_threshold": 70,
            "max_shortlisted_candidates": 50,
            "auto_shortlist": True,
            "total_questions": 25,
            "time_limit_minutes": 90,
            "total_marks": 100,
            "scheduled_at": (datetime.now() + timedelta(days=1)).isoformat(),
            "application_deadline": (datetime.now() + timedelta(days=7)).isoformat(),
            "assessment_deadline": (datetime.now() + timedelta(days=14)).isoformat()
        }
        
        response = requests.post(
            f"{self.base_url}/tests/",
            json=test_data,
            headers=self.headers
        )
        
        self.log_response(response, "Create Test")
        
        if response.status_code == 200:
            data = response.json()
            self.test_id = data.get("test_id")
            return data
        else:
            print(f"Failed to create test: {response.text}")
            return None
            
    def get_all_tests(self) -> Dict[str, Any]:
        """Get all tests"""
        response = requests.get(
            f"{self.base_url}/tests/",
            headers=self.headers
        )
        
        self.log_response(response, "Get All Tests")
        return response.json() if response.status_code == 200 else None
        
    def get_my_tests(self) -> Dict[str, Any]:
        """Get tests created by current user"""
        response = requests.get(
            f"{self.base_url}/tests/my-tests",
            headers=self.headers
        )
        
        self.log_response(response, "Get My Tests")
        return response.json() if response.status_code == 200 else None
        
    def get_test_by_id(self, test_id: int) -> Dict[str, Any]:
        """Get specific test by ID"""
        response = requests.get(
            f"{self.base_url}/tests/{test_id}",
            headers=self.headers
        )
        
        self.log_response(response, f"Get Test by ID ({test_id})")
        return response.json() if response.status_code == 200 else None
        
    def update_test(self, test_id: int) -> Dict[str, Any]:
        """Update test"""
        update_data = {
            "test_name": "Updated Python Developer Assessment",
            "resume_score_threshold": 75,
            "max_shortlisted_candidates": 40,
            "time_limit_minutes": 120
        }
        
        response = requests.put(
            f"{self.base_url}/tests/{test_id}",
            json=update_data,
            headers=self.headers
        )
        
        self.log_response(response, f"Update Test ({test_id})")
        return response.json() if response.status_code == 200 else None
        
    def schedule_test(self, test_id: int) -> Dict[str, Any]:
        """Schedule test for publishing"""
        schedule_data = {
            "scheduled_at": (datetime.now() + timedelta(hours=2)).isoformat(),
            "application_deadline": (datetime.now() + timedelta(days=10)).isoformat(),
            "assessment_deadline": (datetime.now() + timedelta(days=20)).isoformat()
        }
        
        response = requests.post(
            f"{self.base_url}/tests/{test_id}/schedule",
            json=schedule_data,
            headers=self.headers
        )
        
        self.log_response(response, f"Schedule Test ({test_id})")
        return response.json() if response.status_code == 200 else None
        
    def publish_test(self, test_id: int) -> Dict[str, Any]:
        """Publish test"""
        response = requests.post(
            f"{self.base_url}/tests/{test_id}/publish",
            headers=self.headers
        )
        
        self.log_response(response, f"Publish Test ({test_id})")
        return response.json() if response.status_code == 200 else None
        
    def get_test_status(self, test_id: int) -> Dict[str, Any]:
        """Get test status"""
        response = requests.get(
            f"{self.base_url}/tests/{test_id}/status",
            headers=self.headers
        )
        
        self.log_response(response, f"Get Test Status ({test_id})")
        return response.json() if response.status_code == 200 else None
        
    def unpublish_test(self, test_id: int) -> Dict[str, Any]:
        """Unpublish test"""
        response = requests.post(
            f"{self.base_url}/tests/{test_id}/unpublish",
            headers=self.headers
        )
        
        self.log_response(response, f"Unpublish Test ({test_id})")
        return response.json() if response.status_code == 200 else None
        
    def duplicate_test(self, test_id: int) -> Dict[str, Any]:
        """Duplicate test"""
        response = requests.post(
            f"{self.base_url}/tests/{test_id}/duplicate",
            headers=self.headers
        )
        
        self.log_response(response, f"Duplicate Test ({test_id})")
        return response.json() if response.status_code == 200 else None
        
    def delete_test(self, test_id: int) -> Dict[str, Any]:
        """Delete test"""
        response = requests.delete(
            f"{self.base_url}/tests/{test_id}",
            headers=self.headers
        )
        
        self.log_response(response, f"Delete Test ({test_id})")
        return response.json() if response.status_code == 200 else None
        
    def run_complete_test_suite(self):
        """Run complete test suite for all APIs"""
        print("🚀 Starting Complete Test API Suite")
        print("=" * 60)
        
        # Step 1: Create recruiter user
        print("\n1. Creating recruiter user...")
        user = self.create_recruiter_user()
        if not user:
            print("❌ Failed to create recruiter. Exiting.")
            return
            
        # Step 2: Login
        print("\n2. Logging in...")
        time.sleep(1)  # Small delay to ensure user is committed
        login_result = self.login_recruiter()
        if not login_result:
            print("❌ Failed to login. Exiting.")
            return
            
        # Step 3: Create test
        print("\n3. Creating test...")
        time.sleep(1)  # Small delay to ensure login is processed
        test = self.create_test()
        if not test:
            print("❌ Failed to create test. Exiting.")
            return
            
        test_id = self.test_id
        
        # Step 4: Get all tests
        print("\n4. Getting all tests...")
        self.get_all_tests()
        
        # Step 5: Get my tests
        print("\n5. Getting my tests...")
        self.get_my_tests()
        
        # Step 6: Get test by ID
        print("\n6. Getting test by ID...")
        self.get_test_by_id(test_id)
        
        # Step 7: Update test
        print("\n7. Updating test...")
        self.update_test(test_id)
        
        # Step 8: Schedule test
        print("\n8. Scheduling test...")
        self.schedule_test(test_id)
        
        # Step 9: Get test status
        print("\n9. Getting test status...")
        self.get_test_status(test_id)
        
        # Step 10: Publish test
        print("\n10. Publishing test...")
        self.publish_test(test_id)
        
        # Step 11: Get test status after publish
        print("\n11. Getting test status after publish...")
        self.get_test_status(test_id)
        
        # Step 12: Unpublish test
        print("\n12. Unpublishing test...")
        self.unpublish_test(test_id)
        
        # Step 13: Duplicate test
        print("\n13. Duplicating test...")
        duplicate_result = self.duplicate_test(test_id)
        duplicate_test_id = duplicate_result.get("test_id") if duplicate_result else None
        
        # Step 14: Get all tests to see duplicate
        print("\n14. Getting all tests to see duplicate...")
        self.get_all_tests()
        
        # Step 15: Delete duplicate test
        if duplicate_test_id:
            print(f"\n15. Deleting duplicate test ({duplicate_test_id})...")
            self.delete_test(duplicate_test_id)
        
        # Step 16: Delete original test
        print(f"\n16. Deleting original test ({test_id})...")
        self.delete_test(test_id)
        
        # Step 17: Final get all tests
        print("\n17. Final get all tests...")
        self.get_all_tests()
        
        print("\n✅ Complete Test Suite Finished!")
        print("=" * 60)

def main():
    """Main function to run the test suite"""
    client = TestAPIClient()
    client.run_complete_test_suite()

if __name__ == "__main__":
    main()
