# Manual API Testing Guide for Assessment Endpoints
# Use this to test your Assessment API manually

## Prerequisites
Make sure your server is running:
```bash
uvicorn main:app --reload
```

## Test Sequence

### 1. Check Server Status
```
GET http://127.0.0.1:8000/docs
Expected: 200 OK (FastAPI docs page)
```

### 2. Login as Recruiter
```
POST http://127.0.0.1:8000/auth/login
Content-Type: application/json

{
    "email": "recruiter@company.com",
    "password": "recruiter123"
}

Expected Response:
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 3. Create Test Candidate
```
POST http://127.0.0.1:8000/auth/register
Content-Type: application/json

{
    "name": "Test Candidate",
    "email": "candidate@example.com",
    "password": "candidate123",
    "role": "candidate"
}

Expected Response:
{
    "user_id": 6
}
```

### 4. Create Assessment Test
```
POST http://127.0.0.1:8000/tests/
Content-Type: application/json
Authorization: Bearer {your_token_here}

{
    "test_name": "Python Developer Assessment",
    "job_description": "Comprehensive Python development assessment",
    "parsed_job_description": {
        "skills": ["Python", "FastAPI", "SQLAlchemy", "PostgreSQL"],
        "level": "Mid-Senior",
        "experience": "2-5 years"
    },
    "skill_graph": {
        "technical_skills": {
            "python": {"weight": 0.3, "max_score": 100},
            "web_frameworks": {"weight": 0.25, "max_score": 100},
            "databases": {"weight": 0.25, "max_score": 100},
            "testing": {"weight": 0.2, "max_score": 100}
        },
        "assessment_criteria": {
            "code_quality": "Clean, readable, well-documented code",
            "problem_solving": "Logical approach to complex problems",
            "best_practices": "Following Python and web development best practices"
        }
    },
    "scheduled_at": "2025-07-15T14:00:00"
}

Expected Response:
{
    "test_id": 2,
    "test_name": "Python Developer Assessment",
    "job_description": "Comprehensive Python development assessment",
    ...
}
```

### 5. Start Assessment (Recruiter assigns test to candidate)
```
POST http://127.0.0.1:8000/assessments/
Content-Type: application/json
Authorization: Bearer {your_token_here}

{
    "test_id": 2,
    "candidate_id": 6
}

Expected Response:
{
    "assessment_id": 1,
    "started_at": "2025-07-01T...",
    "test_id": 2,
    "candidate_id": 6,
    "test_name": "Python Developer Assessment",
    "candidate_name": "Test Candidate",
    "candidate_email": "candidate@example.com",
    ...
}
```

### 6. Update Assessment with Scores (After candidate completes)
```
PUT http://127.0.0.1:8000/assessments/1
Content-Type: application/json
Authorization: Bearer {your_token_here}

{
    "remark": "Candidate demonstrated strong Python fundamentals and good problem-solving approach. Code quality was excellent with proper error handling. Areas for improvement include database optimization and advanced testing techniques.",
    "resume_score": 85,
    "skill_graph": {
        "python": {
            "score": 88,
            "notes": "Excellent understanding of Python syntax, data structures, and OOP concepts",
            "questions_attempted": 10,
            "questions_correct": 8
        },
        "web_frameworks": {
            "score": 75,
            "notes": "Good grasp of FastAPI basics, needs experience with advanced features like middleware",
            "questions_attempted": 8,
            "questions_correct": 6
        },
        "databases": {
            "score": 70,
            "notes": "Solid SQL fundamentals, could improve on complex joins and performance optimization",
            "questions_attempted": 6,
            "questions_correct": 4
        },
        "testing": {
            "score": 65,
            "notes": "Basic understanding of unit testing, needs exposure to integration and mocking",
            "questions_attempted": 5,
            "questions_correct": 3
        },
        "overall_assessment": {
            "strengths": [
                "Clean code structure",
                "Good problem decomposition",
                "Excellent communication during technical discussion"
            ],
            "areas_for_improvement": [
                "Database performance optimization",
                "Advanced testing strategies",
                "Error handling in distributed systems"
            ],
            "recommendation": "Strong hire with mentoring support for database and testing skills"
        }
    },
    "score": 78
}

Expected Response:
{
    "assessment_id": 1,
    "score": 78,
    "resume_score": 85,
    "remark": "Candidate demonstrated strong Python fundamentals...",
    "skill_graph": { ... },
    ...
}
```

### 7. Get Assessment Details
```
GET http://127.0.0.1:8000/assessments/1
Authorization: Bearer {your_token_here}

Expected Response:
{
    "assessment_id": 1,
    "started_at": "2025-07-01T...",
    "test_id": 2,
    "candidate_id": 6,
    "remark": "Candidate demonstrated strong Python fundamentals...",
    "resume_score": 85,
    "skill_graph": { ... },
    "score": 78,
    "test_name": "Python Developer Assessment",
    "candidate_name": "Test Candidate",
    "candidate_email": "candidate@example.com"
}
```

### 8. List All Assessments
```
GET http://127.0.0.1:8000/assessments/
Authorization: Bearer {your_token_here}

Expected Response:
[
    {
        "assessment_id": 1,
        "started_at": "2025-07-01T...",
        "test_name": "Python Developer Assessment",
        "candidate_name": "Test Candidate",
        "score": 78
    }
]
```

### 9. Get Assessments by Candidate (Future endpoint)
```
GET http://127.0.0.1:8000/assessments/candidate/6
Authorization: Bearer {your_token_here}

Expected Response: List of assessments for that candidate
```

### 10. Get Assessments by Test (Future endpoint)
```
GET http://127.0.0.1:8000/assessments/test/2
Authorization: Bearer {your_token_here}

Expected Response: List of all assessments for that test
```

## Error Cases to Test

### 1. Unauthorized Access
```
POST http://127.0.0.1:8000/assessments/
Content-Type: application/json
# No Authorization header

Expected: 401 Unauthorized
```

### 2. Candidate Trying to Access Other's Assessment
```
# Login as candidate first, then try to access assessment they didn't take
GET http://127.0.0.1:8000/assessments/1
Authorization: Bearer {candidate_token}

Expected: 403 Forbidden
```

### 3. Invalid Data
```
POST http://127.0.0.1:8000/assessments/
Content-Type: application/json
Authorization: Bearer {your_token_here}

{
    "test_id": 999,  # Non-existent test
    "candidate_id": 6
}

Expected: 404 Not Found or 400 Bad Request
```

### 4. Invalid Score Range
```
PUT http://127.0.0.1:8000/assessments/1
Content-Type: application/json
Authorization: Bearer {your_token_here}

{
    "score": 150  # Invalid score > 100
}

Expected: 422 Validation Error
```

## PowerShell Testing Commands

You can copy-paste these PowerShell commands to test:

```powershell
# Login
$loginBody = @{email="recruiter@company.com"; password="recruiter123"} | ConvertTo-Json
$loginResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
$token = $loginResponse.token
$headers = @{Authorization="Bearer $token"}

# Create candidate
$candidateBody = @{name="Test Candidate"; email="candidate@example.com"; password="candidate123"; role="candidate"} | ConvertTo-Json
$candidateResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/register" -Method Post -Body $candidateBody -ContentType "application/json"
$candidateId = $candidateResponse.user_id

# Start assessment (will fail until you create the controller)
$assessmentBody = @{test_id=1; candidate_id=$candidateId} | ConvertTo-Json
$assessmentResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/assessments/" -Method Post -Body $assessmentBody -ContentType "application/json" -Headers $headers
```

## Next Steps

1. First create the assessment_controller.py file (based on my previous explanation)
2. Create the assessment model, schemas, repository, and service
3. Run the migration to create the assessment table
4. Test each endpoint one by one using the commands above

Remember: The assessment endpoints will return 404 until you implement the assessment_controller!
