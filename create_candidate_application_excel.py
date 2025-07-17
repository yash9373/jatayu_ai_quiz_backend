#!/usr/bin/env python3
"""
Script to create an Excel template for candidate application bulk upload
This file contains all the columns needed for the candidate application create API
"""

import pandas as pd
from datetime import datetime
import os

def create_candidate_application_excel():
    """Create Excel file with candidate application columns"""
    
    # Define columns based on CandidateApplicationCreate schema and model
    columns = [
        'email',                    # Required - candidate email
        'name',                     # Optional - candidate name
        'test_id',                  # Required - test to apply for
        'resume_link',              # Required - link to resume file
        'user_id',                  # Optional - will be auto-created if not provided
        'resume_text',              # Optional - extracted text from resume
        'parsed_resume',            # Optional - AI parsed resume data
        'resume_score',             # Optional - AI calculated resume score (0-100)
        'skill_match_percentage',   # Optional - percentage match with job requirements
        'experience_score',         # Optional - experience score (0-100)
        'education_score',          # Optional - education score (0-100)
        'ai_reasoning',             # Optional - AI reasoning for scores
        'is_shortlisted',           # Optional - whether candidate is shortlisted
        'shortlist_reason',         # Optional - reason for shortlisting/rejection
        'screening_completed_at',   # Optional - when AI screening was completed
        'notified_at',              # Optional - when candidate was notified
        'applied_at',               # Optional - application timestamp
        'updated_at'                # Optional - last update timestamp
    ]
    
    # Create sample data with proper data types and examples
    sample_data = [
        {
            'email': 'john.doe@example.com',
            'name': 'John Doe',
            'test_id': 1,
            'resume_link': 'https://example.com/resumes/john_doe.pdf',
            'user_id': '',  # Will be auto-created
            'resume_text': 'Sample resume text...',
            'parsed_resume': '{"skills": ["Python", "React"], "experience": "5 years"}',
            'resume_score': 85,
            'skill_match_percentage': 92.5,
            'experience_score': 80,
            'education_score': 75,
            'ai_reasoning': 'Strong technical skills match requirements',
            'is_shortlisted': True,
            'shortlist_reason': 'Excellent skill match and experience',
            'screening_completed_at': datetime.now().isoformat(),
            'notified_at': '',
            'applied_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        },
        {
            'email': 'jane.smith@example.com',
            'name': 'Jane Smith',
            'test_id': 1,
            'resume_link': 'https://example.com/resumes/jane_smith.pdf',
            'user_id': '',  # Will be auto-created
            'resume_text': '',
            'parsed_resume': '',
            'resume_score': '',
            'skill_match_percentage': '',
            'experience_score': '',
            'education_score': '',
            'ai_reasoning': '',
            'is_shortlisted': '',
            'shortlist_reason': '',
            'screening_completed_at': '',
            'notified_at': '',
            'applied_at': '',
            'updated_at': ''
        }
    ]
    
    # Create DataFrame
    df = pd.DataFrame(sample_data, columns=columns)
    
    # Create Excel file with multiple sheets
    excel_filename = 'candidate_applications_template.xlsx'
    
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        # Main template sheet
        df.to_excel(writer, sheet_name='Applications_Template', index=False)
        
        # Instructions sheet
        instructions_data = [
            ['Field Name', 'Required', 'Data Type', 'Description', 'Example'],
            ['email', 'Yes', 'String', 'Candidate email address', 'john.doe@example.com'],
            ['name', 'No', 'String', 'Candidate full name', 'John Doe'],
            ['test_id', 'Yes', 'Integer', 'ID of the test to apply for', '1'],
            ['resume_link', 'Yes', 'String', 'URL/path to resume file', 'https://example.com/resume.pdf'],
            ['user_id', 'No', 'Integer', 'User ID (auto-created if empty)', '123'],
            ['resume_text', 'No', 'String', 'Extracted text from resume', 'Resume content...'],
            ['parsed_resume', 'No', 'JSON String', 'AI parsed resume data', '{"skills": ["Python"]}'],
            ['resume_score', 'No', 'Integer (0-100)', 'AI calculated resume score', '85'],
            ['skill_match_percentage', 'No', 'Float (0-100)', 'Skill match percentage', '92.5'],
            ['experience_score', 'No', 'Integer (0-100)', 'Experience score', '80'],
            ['education_score', 'No', 'Integer (0-100)', 'Education score', '75'],
            ['ai_reasoning', 'No', 'String', 'AI reasoning for scores', 'Strong technical skills'],
            ['is_shortlisted', 'No', 'Boolean', 'Shortlisted status', 'True'],
            ['shortlist_reason', 'No', 'String', 'Reason for decision', 'Excellent match'],
            ['screening_completed_at', 'No', 'ISO DateTime', 'Screening completion time', '2025-07-15T10:30:00'],
            ['notified_at', 'No', 'ISO DateTime', 'Notification time', '2025-07-15T11:00:00'],
            ['applied_at', 'No', 'ISO DateTime', 'Application time', '2025-07-15T09:00:00'],
            ['updated_at', 'No', 'ISO DateTime', 'Last update time', '2025-07-15T12:00:00']
        ]
        
        instructions_df = pd.DataFrame(instructions_data[1:], columns=instructions_data[0])
        instructions_df.to_excel(writer, sheet_name='Field_Instructions', index=False)
        
        # API endpoint information
        api_info_data = [
            ['API Endpoint Information'],
            [''],
            ['Single Application API:'],
            ['Method: POST'],
            ['URL: /candidate-applications/single'],
            ['Content-Type: application/json'],
            [''],
            ['Bulk Application API:'],
            ['Method: POST'],
            ['URL: /candidate-applications/bulk'],
            ['Content-Type: application/json'],
            [''],
            ['Required Headers:'],
            ['Authorization: Bearer <your_jwt_token>'],
            [''],
            ['Minimum Required Fields:'],
            ['- email (string)'],
            ['- test_id (integer)'],
            ['- resume_link (string)'],
            [''],
            ['Notes:'],
            ['- Only recruiters can create applications'],
            ['- user_id will be auto-created if not provided'],
            ['- AI processing happens automatically'],
            ['- Boolean fields accept: true/false, True/False, 1/0'],
            ['- DateTime fields should be in ISO format: YYYY-MM-DDTHH:MM:SS']
        ]
        
        api_info_df = pd.DataFrame(api_info_data)
        api_info_df.to_excel(writer, sheet_name='API_Info', index=False, header=False)
    
    print(f"✅ Excel file created: {excel_filename}")
    print(f"📁 Location: {os.path.abspath(excel_filename)}")
    print("\n📋 File contains:")
    print("   - Applications_Template: Main template with sample data")
    print("   - Field_Instructions: Detailed field descriptions")
    print("   - API_Info: API endpoint and usage information")
    print("\n🎯 Usage:")
    print("   1. Fill in the Applications_Template sheet")
    print("   2. Use the data for bulk API calls")
    print("   3. Minimum required: email, test_id, resume_link")

if __name__ == "__main__":
    create_candidate_application_excel()
