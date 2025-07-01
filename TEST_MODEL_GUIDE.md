# Test Model Implementation Guide

## Overview
This guide shows how to create a new `Test` model following the established patterns and best practices in your FastAPI application. The Test model includes proper authentication, authorization, and role-based access control.

## Database Schema

### Test Table Structure
```sql
CREATE TABLE test (
    test_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    text TEXT,
    job_description TEXT,
    created_by INTEGER NOT NULL REFERENCES "user"(user_id),
    updated_by INTEGER REFERENCES "user"(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);
```

### Key Features
- **Primary Key**: `test_id` following the naming convention
- **Foreign Keys**: Proper relationships to User table
- **Audit Fields**: `created_by`, `updated_by`, `created_at`, `updated_at`
- **Flexible Content**: Text fields for test content and job descriptions

## Implementation Steps

### 1. Model Definition (`app/models/test.py`)
```python
class Test(Base):
    __tablename__ = "test"
    
    test_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    text = Column(Text, nullable=True)
    job_description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("user.user_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
```

### 2. Schemas (`app/schemas/test_schema.py`)
```python
class TestCreate(BaseModel):
    name: str
    text: Optional[str] = None
    job_description: Optional[str] = None

class TestUpdate(BaseModel):
    name: Optional[str] = None
    text: Optional[str] = None
    job_description: Optional[str] = None

class TestResponse(BaseModel):
    test_id: int
    name: str
    text: Optional[str]
    job_description: Optional[str]
    created_by: int
    updated_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    creator_name: Optional[str] = None
    creator_role: Optional[UserRole] = None
```

### 3. Repository Layer (`app/repositories/test_repo.py`)
- **CRUD Operations**: Create, Read, Update, Delete
- **Relationship Loading**: Uses `joinedload` for efficient queries
- **Filtering**: Support for filtering by creator, pagination
- **Error Handling**: Proper exception handling

### 4. Service Layer (`app/services/test_service.py`)
- **Business Logic**: Authorization checks, validation
- **Role-Based Access**: Only creators and recruiters can modify
- **Data Transformation**: Format responses with user information
- **Error Handling**: HTTP exceptions with proper status codes

### 5. Controller Layer (`app/controllers/test_controller.py`)
- **REST Endpoints**: Standard CRUD operations
- **Authentication**: All endpoints require valid JWT token
- **Authorization**: Role-based access control
- **Dependency Injection**: Clean separation of concerns

## API Endpoints

### Authentication Required (All Endpoints)
All Test API endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

### Available Endpoints

#### 🔒 **RECRUITER-ONLY ACCESS** 
**ALL endpoints below are restricted to recruiters only. Candidates receive 403 Forbidden.**

#### 1. Create Test
```
POST /tests/
```
- **Access**: Recruiters only
- **Body**: TestCreate schema
- **Response**: TestResponse with creator info

#### 2. Get All Tests
```
GET /tests/?skip=0&limit=100
```
- **Access**: Recruiters only
- **Query Params**: Pagination support
- **Response**: List of TestSummary

#### 3. Get Test by ID
```
GET /tests/{test_id}
```
- **Access**: Recruiters only
- **Response**: TestResponse with full details

#### 4. Update Test
```
PUT /tests/{test_id}
```
- **Access**: Recruiters only
- **Body**: TestUpdate schema (partial updates supported)
- **Response**: Updated TestResponse

#### 5. Delete Test
```
DELETE /tests/{test_id}
```
- **Access**: Recruiters only
- **Response**: Success message

#### 6. Get My Tests
```
GET /tests/my-tests
```
- **Access**: Recruiters only
- **Response**: Tests created by current user

#### 7. Recruiter-Only Endpoint
```
GET /tests/recruiter/all
```
- **Access**: Recruiters only
- **Response**: All tests with recruiter privileges

## Role-Based Access Control

### Access Matrix (Updated - Recruiter-Only Access)
| Endpoint | Candidate | Recruiter |
|----------|-----------|-----------|
| Create Test | ❌ | ✅ |
| View Tests | ❌ | ✅ |
| Update Test | ❌ | ✅ |
| Delete Test | ❌ | ✅ |
| My Tests | ❌ | ✅ |
| All Endpoints | ❌ | ✅ |

### Security Model
**ALL Test APIs are RECRUITER-ONLY**
- ✅ **Recruiters**: Full access to all test operations
- ❌ **Candidates**: NO access to any test endpoints (403 Forbidden)
- 🔒 **Complete Isolation**: Candidates cannot view, create, or modify tests

### Security Features

#### 1. Authentication
- **JWT Tokens**: Stateless authentication
- **Token Validation**: Every request validates token
- **Expiration**: Tokens expire for security

#### 2. Authorization
- **Role Verification**: Checks user role before access
- **Owner Verification**: Users can only modify their own tests
- **Hierarchical Access**: Recruiters have elevated privileges

#### 3. Data Protection
- **Input Validation**: Pydantic schemas validate all inputs
- **SQL Injection Protection**: SQLAlchemy ORM prevents injections
- **Foreign Key Constraints**: Database-level referential integrity

## Testing Results

✅ **All tests passed successfully:**

### Authentication Tests
- ✅ Recruiter registration and login
- ✅ Candidate registration and login
- ✅ JWT token generation and validation

### Authorization Tests
- ✅ Only recruiters can create tests
- ✅ Candidates blocked from creating tests (403)
- ✅ Only creators/recruiters can update tests
- ✅ Candidates blocked from updating tests (403)
- ✅ Only creators/recruiters can delete tests
- ✅ Recruiter-only endpoints properly restricted

### Functionality Tests
- ✅ Test creation with proper audit fields
- ✅ Test retrieval with creator information
- ✅ Test updates with updater tracking
- ✅ Pagination support
- ✅ User-specific test filtering

## Best Practices Followed

### 1. Architecture Patterns
- **Clean Architecture**: Separation of concerns across layers
- **Dependency Injection**: Loose coupling between components
- **Repository Pattern**: Data access abstraction
- **Service Layer**: Business logic encapsulation

### 2. Database Design
- **Proper Relationships**: Foreign key constraints
- **Audit Trail**: Created/updated by and timestamps
- **Indexing**: Primary keys and frequently queried fields
- **Data Types**: Appropriate field types and constraints

### 3. Security Implementation
- **Authentication First**: All endpoints require valid tokens
- **Role-Based Authorization**: Granular access control
- **Input Validation**: Server-side validation for all inputs
- **Error Handling**: Consistent error responses

### 4. Code Quality
- **Type Hints**: Full type annotation support
- **Error Handling**: Comprehensive exception handling
- **Documentation**: Clear docstrings and comments
- **Testing**: Automated testing of all scenarios

## Extension Points

This implementation provides a solid foundation that can be extended with:

1. **Test Questions**: Add related question models
2. **Test Submissions**: Track candidate responses
3. **Scoring System**: Automated or manual grading
4. **Categories**: Organize tests by type/skill
5. **Templates**: Reusable test templates
6. **Analytics**: Test performance metrics

The architecture supports these extensions while maintaining security and performance standards.

## Migration Command
To apply the database changes:
```bash
python create_tables.py
```

This will create the new test table with proper relationships and constraints.
