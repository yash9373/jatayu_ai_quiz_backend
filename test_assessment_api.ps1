# PowerShell script to test Assessment API
# Run this in PowerShell: .\test_assessment_api.ps1

Write-Host "🧪 Assessment API Test Suite" -ForegroundColor Cyan
Write-Host "=" * 50

# Check if server is running
Write-Host "🌐 Checking server status..." -ForegroundColor Yellow
try {
    $serverCheck = Invoke-RestMethod -Uri "http://127.0.0.1:8000/docs" -Method Get -ErrorAction Stop
    Write-Host "✅ Server is running!" -ForegroundColor Green
} catch {
    Write-Host "❌ Server is not running. Start it with: uvicorn main:app --reload" -ForegroundColor Red
    exit 1
}

# Step 1: Login as recruiter
Write-Host "`n🔐 Testing Login..." -ForegroundColor Yellow
$loginBody = @{
    email = "recruiter@company.com"
    password = "recruiter123"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
    $token = $loginResponse.token
    $headers = @{Authorization = "Bearer $token"}
    Write-Host "✅ Login successful!" -ForegroundColor Green
} catch {
    Write-Host "❌ Login failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 2: Create a test candidate
Write-Host "`n👤 Creating test candidate..." -ForegroundColor Yellow
$candidateBody = @{
    name = "Test Candidate"
    email = "candidate@example.com"
    password = "candidate123"
    role = "candidate"
} | ConvertTo-Json

try {
    $candidateResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/register" -Method Post -Body $candidateBody -ContentType "application/json"
    $candidateId = $candidateResponse.user_id
    Write-Host "✅ Candidate created with ID: $candidateId" -ForegroundColor Green
} catch {
    Write-Host "❌ Candidate creation failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 3: Create a test
Write-Host "`n📝 Creating test for assessments..." -ForegroundColor Yellow
$testBody = @{
    test_name = "Python Assessment Test"
    job_description = "Assessment for Python developer position"
    parsed_job_description = @{
        skills = @("Python", "FastAPI", "SQLAlchemy")
        level = "Mid-Level"
        experience = "2-5 years"
    }
    skill_graph = @{
        technical = @{
            python = @{weight = 0.4; max_score = 100}
            web_frameworks = @{weight = 0.3; max_score = 100}
            databases = @{weight = 0.3; max_score = 100}
        }
    }
    scheduled_at = "2025-07-15T10:00:00"
} | ConvertTo-Json -Depth 5

try {
    $testResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/tests/" -Method Post -Body $testBody -ContentType "application/json" -Headers $headers
    $testId = $testResponse.test_id
    Write-Host "✅ Test created with ID: $testId" -ForegroundColor Green
} catch {
    Write-Host "❌ Test creation failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 4: Start Assessment (This will fail until we create the assessment controller)
Write-Host "`n🚀 Starting assessment..." -ForegroundColor Yellow
$assessmentBody = @{
    test_id = $testId
    candidate_id = $candidateId
} | ConvertTo-Json

try {
    $assessmentResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/assessments/" -Method Post -Body $assessmentBody -ContentType "application/json" -Headers $headers
    $assessmentId = $assessmentResponse.assessment_id
    Write-Host "✅ Assessment started with ID: $assessmentId" -ForegroundColor Green
    Write-Host "   Started at: $($assessmentResponse.started_at)" -ForegroundColor Cyan
    Write-Host "   Test: $($assessmentResponse.test_name)" -ForegroundColor Cyan
    Write-Host "   Candidate: $($assessmentResponse.candidate_name)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Assessment start failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   This is expected if assessment_controller doesn't exist yet" -ForegroundColor Yellow
    exit 1
}

# Step 5: Update Assessment with scores
Write-Host "`n📊 Updating assessment with scores..." -ForegroundColor Yellow
$updateBody = @{
    remark = "Candidate showed good understanding of Python fundamentals. Strong problem-solving skills demonstrated."
    resume_score = 85
    skill_graph = @{
        python = @{score = 88; notes = "Excellent knowledge of Python syntax and best practices"}
        web_frameworks = @{score = 75; notes = "Good understanding of FastAPI, needs more experience with advanced features"}
        databases = @{score = 70; notes = "Basic SQL knowledge, could improve on complex queries"}
        overall_assessment = @{
            strengths = @("Problem solving", "Code quality", "Communication")
            areas_for_improvement = @("Database optimization", "Testing practices")
        }
    }
    score = 78
} | ConvertTo-Json -Depth 5

try {
    $updateResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/assessments/$assessmentId" -Method Put -Body $updateBody -ContentType "application/json" -Headers $headers
    Write-Host "✅ Assessment updated successfully!" -ForegroundColor Green
    Write-Host "   Overall Score: $($updateResponse.score)" -ForegroundColor Cyan
    Write-Host "   Resume Score: $($updateResponse.resume_score)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Assessment update failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 6: Get Assessment details
Write-Host "`n📋 Retrieving assessment details..." -ForegroundColor Yellow
try {
    $getResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/assessments/$assessmentId" -Method Get -Headers $headers
    Write-Host "✅ Assessment retrieved successfully!" -ForegroundColor Green
    Write-Host "   Assessment ID: $($getResponse.assessment_id)" -ForegroundColor Cyan
    Write-Host "   Test: $($getResponse.test_name)" -ForegroundColor Cyan
    Write-Host "   Candidate: $($getResponse.candidate_name) ($($getResponse.candidate_email))" -ForegroundColor Cyan
    Write-Host "   Scores - Overall: $($getResponse.score), Resume: $($getResponse.resume_score)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Assessment retrieval failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 7: List all assessments
Write-Host "`n📊 Listing all assessments..." -ForegroundColor Yellow
try {
    $listResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/assessments/" -Method Get -Headers $headers
    Write-Host "✅ Found $($listResponse.Count) assessments" -ForegroundColor Green
    
    foreach ($assessment in $listResponse) {
        Write-Host "   ID: $($assessment.assessment_id) - $($assessment.test_name) - $($assessment.candidate_name) - Score: $($assessment.score)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ Assessment listing failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎉 Assessment API test completed!" -ForegroundColor Green
Write-Host "`n📋 What was tested:" -ForegroundColor Cyan
Write-Host "✅ Server connectivity" -ForegroundColor Green
Write-Host "✅ User authentication" -ForegroundColor Green
Write-Host "✅ Candidate creation" -ForegroundColor Green
Write-Host "✅ Test creation" -ForegroundColor Green
Write-Host "✅ Assessment start (will fail until controller is created)" -ForegroundColor Yellow
Write-Host "✅ Assessment update" -ForegroundColor Yellow
Write-Host "✅ Assessment retrieval" -ForegroundColor Yellow
Write-Host "✅ Assessment listing" -ForegroundColor Yellow
