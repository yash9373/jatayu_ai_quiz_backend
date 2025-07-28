# Singleton pattern for NotificationService
_notification_service_instance = None
def get_notification_service():
    global _notification_service_instance
    if _notification_service_instance is None:
        _notification_service_instance = NotificationService()
    return _notification_service_instance
"""
Notification Service - Mock email/SMS service for now
Following Single Responsibility Principle
"""
import logging
from sendgrid.helpers.mail import Mail, Email, To, Content
import ssl
import os
import sendgrid
from app.models.test import Test
from app.models.user import User
from datetime import datetime
from typing import Dict, Any, List
_notification_service_instance = None


def get_notification_service():
    global _notification_service_instance
    if _notification_service_instance is None:
        _notification_service_instance = NotificationService()
    return _notification_service_instance


# NotificationService class for sending emails
ssl._create_default_https_context = ssl._create_unverified_context


class NotificationService:
    def __init__(self):
        api_key = os.environ.get("SENDGRID_API_KEY")
        self.sg = sendgrid.SendGridAPIClient(api_key=api_key)
        # Use your verified sender email
        self.from_email = Email("kolheyashodip8@gmail.com")

    def send_email(self, to_email: str, subject: str, html_content: str) -> int:
        to = To(to_email)
        content = Content("text/html", html_content)
        mail = Mail(self.from_email, to, subject, content)
        mail_json = mail.get()
        response = self.sg.client.mail.send.post(request_body=mail_json)
        # Optionally log or handle response
        return response.status_code

    def send_account_creation_email(self, to_email: str, username: str, password: str) -> int:
        subject = "Your Jatayu Account Created"
        html_content = f"""
            <p>Hello,</p>
            <p>Your account has been created.</p>
            <p><b>Username:</b> {username}<br><b>Password:</b> {password}</p>
            <p>Please change your password after first login.</p>
        """
        return self.send_email(to_email, subject, html_content)

    def send_shortlisting_status_email(self, to_email: str, status: str, extra_info: str = None) -> int:
        subject = "Your Application Status Update"
        html_content = f"<p>Hello,</p><p>Your application status: <b>{status}</b>.</p>"
        if extra_info:
            html_content += f"<p>{extra_info}</p>"
        return self.send_email(to_email, subject, html_content)

    def notify_test_deleted(self, test_name: str, test_id: int, recruiter_email: str) -> int:
        subject = "Test Deleted Notification"
        html_content = f"""
            <p>Hello,</p>
            <p>The test <b>{test_name}</b> (ID: {test_id}) has been deleted from your account.</p>
            <p>If this was not intended, please contact support.</p>
        """
        return self.send_email(recruiter_email, subject, html_content)