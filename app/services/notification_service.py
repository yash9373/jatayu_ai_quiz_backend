"""
Notification Service - Mock email/SMS service for now
Following Single Responsibility Principle
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from app.models.user import User
from app.models.test import Test

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for handling notifications (email/SMS)"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def send_test_created_notification(self, test: Test, creator: User) -> None:
        """Send notification when test is created"""
        message = f"""
        📧 EMAIL NOTIFICATION (Mock)
        
        To: {creator.email}
        Subject: Test Created Successfully - {test.test_name}
        
        Hi {creator.name},
        
        Your test "{test.test_name}" has been created successfully.
        
        Test Details:
        - Test ID: {test.test_id}
        - Status: {test.status}
        - Created: {test.created_at}
        
        Next Steps:
        1. Review test configuration
        2. Schedule the test
        3. Publish when ready
        
        Best regards,
        Jatayu Team
        """
        
        logger.info(f"[NOTIFICATION] Test created notification for {creator.email}")
        print(message)
    
    async def send_test_scheduled_notification(self, test: Test, creator: User) -> None:
        """Send notification when test is scheduled"""
        message = f"""
        📧 EMAIL NOTIFICATION (Mock)
        
        To: {creator.email}
        Subject: Test Scheduled - {test.test_name}
        
        Hi {creator.name},
        
        Your test "{test.test_name}" has been scheduled successfully.
        
        Schedule Details:
        - Test ID: {test.test_id}
        - Scheduled for: {test.scheduled_at}
        - Application Deadline: {test.application_deadline}
        - Assessment Deadline: {test.assessment_deadline}
        
        The test will be automatically published at the scheduled time.
        
        Best regards,
        Jatayu Team
        """
        
        logger.info(f"[NOTIFICATION] Test scheduled notification for {creator.email}")
        print(message)
    
    async def send_test_published_notification(self, test: Test, creator: User) -> None:
        """Send notification when test is published"""
        message = f"""
        📧 EMAIL NOTIFICATION (Mock)
        
        To: {creator.email}
        Subject: Test Published - {test.test_name}
        
        Hi {creator.name},
        
        Your test "{test.test_name}" is now live and available to candidates!
        
        Test Details:
        - Test ID: {test.test_id}
        - Status: Published
        - Published: {datetime.now()}
        - Application Deadline: {test.application_deadline}
        
        Candidates can now apply and take the assessment.
        
        Best regards,
        Jatayu Team
        """
        
        logger.info(f"[NOTIFICATION] Test published notification for {creator.email}")
        print(message)
    
    async def send_test_unpublished_notification(self, test: Test, creator: User) -> None:
        """Send notification when test is unpublished"""
        message = f"""
        📧 EMAIL NOTIFICATION (Mock)
        
        To: {creator.email}
        Subject: Test Unpublished - {test.test_name}
        
        Hi {creator.name},
        
        Your test "{test.test_name}" has been unpublished and is no longer available to candidates.
        
        Test Details:
        - Test ID: {test.test_id}
        - Status: Paused
        - Unpublished: {datetime.now()}
        
        You can republish the test anytime from your dashboard.
        
        Best regards,
        Jatayu Team
        """
        
        logger.info(f"[NOTIFICATION] Test unpublished notification for {creator.email}")
        print(message)
    
    async def send_candidate_notification(self, candidates: List[User], test: Test) -> None:
        """Send notification to candidates about new test"""
        for candidate in candidates:
            message = f"""
            📧 EMAIL NOTIFICATION (Mock)
            
            To: {candidate.email}
            Subject: New Assessment Available - {test.test_name}
            
            Hi {candidate.name},
            
            A new assessment "{test.test_name}" is now available for you to take.
            
            Test Details:
            - Test ID: {test.test_id}
            - Time Limit: {test.time_limit_minutes} minutes
            - Total Questions: {test.total_questions}
            - Total Marks: {test.total_marks}
            - Application Deadline: {test.application_deadline}
            
            Please log in to your dashboard to start the assessment.
            
            Best regards,
            Jatayu Team
            """
            
            logger.info(f"[NOTIFICATION] Candidate notification sent to {candidate.email}")
            print(message)
    
    async def send_ai_processing_notification(self, test: Test, creator: User, status: str) -> None:
        """Send notification about AI processing status"""
        message = f"""
        📧 EMAIL NOTIFICATION (Mock)
        
        To: {creator.email}
        Subject: AI Processing {status} - {test.test_name}
        
        Hi {creator.name},
        
        AI processing for your test "{test.test_name}" is {status}.
        
        Process Details:
        - Test ID: {test.test_id}
        - Status: {status}
        - Time: {datetime.now()}
        
        {"Your job description has been parsed and skill graph generated successfully!" if status == "completed" else "Processing your job description and generating skill graph..."}
        
        Best regards,
        Jatayu Team
        """
        
        logger.info(f"[NOTIFICATION] AI processing {status} notification for {creator.email}")
        print(message)

# Singleton instance
notification_service = NotificationService()

def get_notification_service() -> NotificationService:
    """Get notification service instance"""
    return notification_service
