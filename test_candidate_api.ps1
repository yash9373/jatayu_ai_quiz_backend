# PowerShell Test Script for Candidate API
# Run this script to test all candidate endpoints

Write-Host "Starting Candidate API Tests..." -ForegroundColor Green
Write-Host "=" * 50

# Configuration
$baseUrl = "http://127.0.0.1:8000"
$contentType = "application/json"

# Test tracking
$testResults = @()
$testCount = 0
$passCount = 0

function Test-API {
    param(
        [string]$TestName,
        [string]$Method,
        [string]$Endpoint,
        [hashtable]$Body = $null,
        [string]$Token = $null,
        [int[]]$ExpectedStatus = @(200)
    )
    
    $global:testCount++
    
    try {
        $headers = @{
            "Content-Type" = $contentType
        }
        
        if ($Token) {
            $headers["Authorization"] = "Bearer $Token"
        }
        
        $uri = "$baseUrl$Endpoint"
        
        if ($Method -eq "GET") {
            $response = Invoke-WebRequest -Uri $uri -Method $Method -Headers $headers -ErrorAction Stop
        } else {
            $jsonBody = if ($Body) { $Body | ConvertTo-Json -Depth 10 } else { $null }
            $response = Invoke-WebRequest -Uri $uri -Method $Method -Headers $headers -Body $jsonBody -ErrorAction Stop
        }
        
        if ($response.StatusCode -in $ExpectedStatus) {
            Write-Host "PASS $TestName" -ForegroundColor Green
            $global:passCount++
            $global:testResults += @{Test=$TestName; Success=$true; Status=$response.StatusCode}
            return $response
        } else {
            Write-Host "FAIL $TestName - Unexpected status: $($response.StatusCode)" -ForegroundColor Red
            $global:testResults += @{Test=$TestName; Success=$false; Status=$response.StatusCode}
            return $null
        }
    }
    catch {
        $status = if ($_.Exception.Response) { $_.Exception.Response.StatusCode.value__ } else { "No Response" }
        if ($status -in $ExpectedStatus) {
            Write-Host "PASS $TestName" -ForegroundColor Green
            $global:passCount++
            $global:testResults += @{Test=$TestName; Success=$true; Status=$status}
        } else {
            Write-Host "FAIL $TestName - Status: $status, Error: $($_.Exception.Message)" -ForegroundColor Red
            $global:testResults += @{Test=$TestName; Success=$false; Status=$status}
        }
        return $null
    }
}

# Check server health
Write-Host "`nChecking Server Health..." -ForegroundColor Yellow
$healthCheck = Test-API "Server Health Check" "GET" "/docs"

if (-not $healthCheck) {
    Write-Host "❌ Server is not running! Please start the server first:" -ForegroundColor Red
    Write-Host "   uvicorn main:app --reload" -ForegroundColor Yellow
    exit 1
}

# Setup test users
Write-Host "`nSetting up test users..." -ForegroundColor Yellow

# Create recruiter
$recruiterData = @{
    name = "Test Recruiter"
    email = "recruiter@testcompany.com"
    password = "recruiter123"
    role = "recruiter"
}

$recruiterResponse = Test-API "Create Recruiter" "POST" "/auth/register" $recruiterData
$recruiterId = if ($recruiterResponse) { ($recruiterResponse.Content | ConvertFrom-Json).user_id } else { $null }

# Create candidate
$candidateData = @{
    name = "Test Candidate"
    email = "candidate@example.com"
    password = "candidate123"
    role = "candidate"
}

$candidateResponse = Test-API "Create Candidate" "POST" "/auth/register" $candidateData
$candidateId = if ($candidateResponse) { ($candidateResponse.Content | ConvertFrom-Json).user_id } else { $null }

# Login recruiter
$recruiterLogin = @{
    email = "recruiter@testcompany.com"
    password = "recruiter123"
}

$recruiterLoginResponse = Test-API "Recruiter Login" "POST" "/auth/login" $recruiterLogin
$recruiterToken = if ($recruiterLoginResponse) { ($recruiterLoginResponse.Content | ConvertFrom-Json).token } else { $null }

# Login candidate
$candidateLogin = @{
    email = "candidate@example.com"
    password = "candidate123"
}

$candidateLoginResponse = Test-API "Candidate Login" "POST" "/auth/login" $candidateLogin
$candidateToken = if ($candidateLoginResponse) { ($candidateLoginResponse.Content | ConvertFrom-Json).token } else { $null }

Write-Host "Candidate ID: $candidateId" -ForegroundColor Cyan
Write-Host "Recruiter Token: $($recruiterToken.Substring(0,20))..." -ForegroundColor Cyan
Write-Host "Candidate Token: $($candidateToken.Substring(0,20))..." -ForegroundColor Cyan

# Test candidate CRUD operations
Write-Host "`nTesting Candidate CRUD Operations..." -ForegroundColor Yellow

# Create candidate profile
$candidateProfile = @{
    candidate_id = $candidateId
    resume = "I am a skilled software developer with 3 years of experience in Python, JavaScript, and cloud technologies."
    parsed_resume = @{
        personal_info = @{
            name = "Test Candidate"
            email = "candidate@example.com"
            phone = "+1-555-0123"
        }
        experience = @(
            @{
                company = "Tech Solutions Inc."
                position = "Software Developer"
                duration = "2021-2024"
                responsibilities = @(
                    "Developed REST APIs using Python and FastAPI",
                    "Built responsive web applications with React",
                    "Managed PostgreSQL databases"
                )
            }
        )
        skills = @("Python", "JavaScript", "FastAPI", "React", "PostgreSQL", "Docker", "AWS")
        education = @(
            @{
                degree = "Bachelor of Computer Science"
                institution = "University of Technology"
                year = "2021"
            }
        )
        certifications = @(
            "AWS Certified Developer Associate",
            "Python Professional Certification"
        )
    }
}

Test-API "Create Candidate Profile" "POST" "/candidates/" $candidateProfile $candidateToken | Out-Null

# Get candidate profile (as candidate)
Test-API "Get Own Profile (Candidate)" "GET" "/candidates/$candidateId" $null $candidateToken | Out-Null

# Update candidate profile
$updateData = @{
    resume = "Updated resume with more recent experience and new skills in cloud computing."
    parsed_resume = @{
        personal_info = @{
            name = "Test Candidate"
            email = "candidate@example.com"
            phone = "+1-555-0123"
        }
        skills = @("Python", "JavaScript", "FastAPI", "React", "PostgreSQL", "Docker", "AWS", "Microservices", "Redis")
    }
}

Test-API "Update Own Profile (Candidate)" "PUT" "/candidates/$candidateId" $updateData $candidateToken | Out-Null

# Get candidate profile (as recruiter)
Test-API "Get Candidate Profile (Recruiter)" "GET" "/candidates/$candidateId" $null $recruiterToken | Out-Null

# List all candidates (as recruiter)
Test-API "List All Candidates (Recruiter)" "GET" "/candidates/" $null $recruiterToken | Out-Null

# Test security rules
Write-Host "`nTesting Security and Access Control..." -ForegroundColor Yellow

# Candidate cannot list all candidates
Test-API "Candidate Cannot List All" "GET" "/candidates/" $null $candidateToken @(403) | Out-Null

# Unauthenticated access should be blocked
Test-API "Unauthenticated Access Blocked" "GET" "/candidates/" $null $null @(401) | Out-Null

# Test edge cases
Write-Host "`nTesting Edge Cases..." -ForegroundColor Yellow

# Create duplicate candidate profile
$duplicateProfile = @{
    candidate_id = $candidateId
    resume = "This should fail as profile already exists"
}

Test-API "Duplicate Profile Rejected" "POST" "/candidates/" $duplicateProfile $candidateToken @(400) | Out-Null

# Invalid candidate ID
Test-API "Invalid ID Handled" "GET" "/candidates/99999" $null $recruiterToken @(404) | Out-Null

# Print summary
Write-Host "`n" + "=" * 50
Write-Host "Test Summary" -ForegroundColor Green
Write-Host "=" * 50

$failCount = $testCount - $passCount
$successRate = [math]::Round(($passCount / $testCount) * 100, 1)

Write-Host "Total Tests: $testCount"
Write-Host "Passed: $passCount" -ForegroundColor Green
Write-Host "Failed: $failCount" -ForegroundColor Red
Write-Host "Success Rate: $successRate%"

if ($failCount -gt 0) {
    Write-Host "`nFailed Tests:" -ForegroundColor Red
    $testResults | Where-Object { -not $_.Success } | ForEach-Object {
        Write-Host "  - $($_.Test): Status $($_.Status)" -ForegroundColor Red
    }
}

Write-Host "`nTesting Complete!" -ForegroundColor Green

if ($failCount -eq 0) {
    Write-Host "All tests passed! Candidate API is working perfectly!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Some tests failed. Please check the implementation." -ForegroundColor Yellow
    exit 1
}
