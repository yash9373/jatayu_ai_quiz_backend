# WebSocket Assessment System

This document describes the WebSocket implementation for the AI-powered assessment chatbot system.

## Overview

The WebSocket system enables real-time communication between candidates and an AI interviewer during assessments. It handles authentication, question generation using MCQ graphs, answer processing, and progress tracking.

## Architecture

### Components

1. **Connection Manager** (`app/websocket/connection_manager.py`)

   - Manages WebSocket connections
   - Handles authentication and authorization
   - Tracks active sessions and assessment states
   - Provides connection lifecycle management

2. **WebSocket Handler** (`app/websocket/handler.py`)

   - Routes WebSocket messages to appropriate handlers
   - Manages the assessment conversation flow
   - Handles real-time communication with clients

3. **Assessment Graph Service** (`app/services/websocket_assessment_service.py`)

   - Integrates with MCQ generation graph
   - Manages assessment state and progress
   - Handles question generation and answer processing

4. **WebSocket Controller** (`app/controllers/websocket_controller.py`)
   - Defines WebSocket endpoints
   - Handles connection setup and dependency injection

## WebSocket Endpoints

### 1. Assessment Endpoint

```
ws://localhost:8000/ws/assessment?token=JWT_TOKEN&test_id=123
```

**Query Parameters:**

- `token` (required): JWT authentication token
- `test_id` (optional): Test ID for assessment session

### 2. Chat Endpoint

```
ws://localhost:8000/ws/chat?token=JWT_TOKEN
```

**Query Parameters:**

- `token` (required): JWT authentication token

## Message Protocol

### Message Structure

```json
{
  "type": "message_type",
  "data": {
    // Message-specific data
  }
}
```

### Supported Message Types

#### Client → Server Messages

1. **Start Assessment**

   ```json
   {
     "type": "start_assessment",
     "data": {
       "test_id": 123
     }
   }
   ```

2. **Get Question**

   ```json
   {
     "type": "get_question",
     "data": {}
   }
   ```

3. **Submit Answer**

   ```json
   {
     "type": "submit_answer",
     "data": {
       "question_id": "q_12345",
       "selected_option": "A"
     }
   }
   ```

4. **Chat Message**

   ```json
   {
     "type": "chat_message",
     "data": {
       "message": "Can you explain this concept?"
     }
   }
   ```

5. **Heartbeat**
   ```json
   {
     "type": "heartbeat",
     "data": {}
   }
   ```

#### Server → Client Messages

1. **Authentication Success**

   ```json
   {
     "type": "auth_success",
     "data": {
       "user_id": 456,
       "connection_id": "456_1234567890",
       "timestamp": "2025-07-19T10:00:00Z"
     }
   }
   ```

2. **Assessment Started**

   ```json
   {
     "type": "assessment_started",
     "data": {
       "test_id": 123,
       "test_name": "Backend Developer Assessment",
       "time_limit_minutes": 60,
       "total_questions": 15,
       "message": "Assessment started! I'm your AI interviewer..."
     }
   }
   ```

3. **Question**

   ```json
   {
     "type": "question",
     "data": {
       "question_id": "q_12345",
       "node_id": "skill_node_1",
       "question_text": "What is the primary benefit of microservices?",
       "options": ["A) Scalability", "B) Speed", "C) Cost", "D) Simplicity"],
       "time_limit_seconds": 120,
       "question_number": 5,
       "total_questions": 15,
       "skill_being_tested": "System Design",
       "difficulty_level": "Medium"
     }
   }
   ```

4. **Answer Feedback**

   ```json
   {
     "type": "answer_feedback",
     "data": {
       "question_id": "q_12345",
       "is_correct": true,
       "correct_option": "A",
       "selected_option": "A",
       "explanation": "Microservices indeed provide better scalability...",
       "score_gained": 10,
       "total_score": 50,
       "time_taken_seconds": 45,
       "progress": {
         "questions_answered": 5,
         "total_questions": 15,
         "percentage_complete": 33.3
       }
     }
   }
   ```

5. **Progress Update**

   ```json
   {
     "type": "progress_update",
     "data": {
       "questions_answered": 5,
       "total_questions": 15,
       "current_score": 50,
       "time_elapsed_minutes": 10,
       "time_limit_minutes": 60,
       "completion_percentage": 33.3,
       "remaining_nodes": 3,
       "timestamp": "2025-07-19T10:10:00Z"
     }
   }
   ```

6. **Assessment Completed**

   ```json
   {
     "type": "assessment_completed",
     "data": {
       "message": "Assessment completed! Thank you for participating.",
       "results": {
         "assessment_id": "assess_456_1234567890",
         "total_questions": 15,
         "total_score": 120,
         "max_possible_score": 150,
         "percentage_score": 80,
         "time_taken_minutes": 45,
         "completion_status": "completed"
       },
       "next_steps": "Your results will be reviewed..."
     }
   }
   ```

7. **Error**

   ```json
   {
     "type": "error",
     "data": {
       "error": "Authentication failed",
       "timestamp": "2025-07-19T10:00:00Z"
     }
   }
   ```

8. **System Message**
   ```json
   {
     "type": "system_message",
     "data": {
       "message": "I understand you said: 'help me'...",
       "timestamp": "2025-07-19T10:05:00Z"
     }
   }
   ```

## Authentication

WebSocket connections require JWT token authentication:

1. Token provided via query parameter: `?token=YOUR_JWT_TOKEN`
2. Token validated using existing security module
3. User ID extracted from token for session management
4. Invalid tokens result in connection closure with code 4001

## Assessment Flow

### 1. Connection Establishment

1. Client connects with JWT token
2. Server authenticates and creates connection
3. Server sends `auth_success` message

### 2. Assessment Initialization

1. Client sends `start_assessment` with `test_id`
2. Server validates test access and timing
3. Server initializes MCQ generation graph
4. Server sends `assessment_started` message
5. Server automatically generates first question

### 3. Question-Answer Cycle

1. Server sends `question` message
2. Client displays question with timer
3. Client sends `submit_answer` within time limit
4. Server processes answer and sends `answer_feedback`
5. Server sends `progress_update`
6. Cycle repeats until assessment complete

### 4. Assessment Completion

1. Server determines assessment is complete
2. Server calculates final results
3. Server sends `assessment_completed` message
4. Session cleanup performed

## MCQ Graph Integration

### Graph Initialization

```python
# Initialize assessment graph with test data
graph_initialized = await assessment_graph_service.initialize_assessment_graph(
    connection_id, test, user_id, db
)
```

### Question Generation

```python
# Generate next question using graph
question_data = await assessment_graph_service.generate_question(connection_id)
```

### Answer Processing

```python
# Process answer and update graph state
feedback_data = await assessment_graph_service.process_answer(
    connection_id, question_id, selected_option
)
```

## Error Handling

### Connection Errors

- **4001**: Authentication failed
- **4003**: Assessment access denied
- **4004**: Invalid message format

### Message Errors

- Invalid JSON format
- Missing required fields
- Unknown message types
- Processing failures

## Security Features

### Authentication & Authorization

- JWT token validation
- User session management
- Test access validation
- Time-based access control

### Connection Management

- Automatic cleanup of inactive connections
- Session timeout handling
- Connection state tracking
- Memory leak prevention

## Configuration

### Environment Variables

```env
SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Connection Limits

- Max idle time: 30 minutes
- Cleanup interval: 5 minutes
- Default question timeout: 120 seconds

## Deployment Considerations

### WebSocket Support

- Ensure reverse proxy supports WebSocket upgrades
- Configure proper timeout values
- Handle connection persistence across server restarts

### Load Balancing

- Use sticky sessions for WebSocket connections
- Consider Redis for shared session storage
- Monitor connection distribution

### Monitoring

- Track active connections count
- Monitor assessment completion rates
- Log connection errors and patterns

## TODO Items

### High Priority

- [ ] Implement comprehensive test scheduler validation
- [ ] Add database persistence for assessment results
- [ ] Implement proper candidate application linking
- [ ] Add comprehensive error recovery mechanisms

### Medium Priority

- [ ] Implement AI chat functionality for help/support
- [ ] Add real-time progress sync across multiple devices
- [ ] Implement assessment pause/resume functionality
- [ ] Add detailed analytics and metrics collection

### Low Priority

- [ ] Add support for multimedia questions
- [ ] Implement collaborative assessment features
- [ ] Add custom question types support
- [ ] Implement assessment templates

## Testing

### Unit Tests

```bash
# Run WebSocket handler tests
python -m pytest tests/websocket/test_handler.py

# Run connection manager tests
python -m pytest tests/websocket/test_connection_manager.py

# Run assessment service tests
python -m pytest tests/services/test_websocket_assessment_service.py
```

### Integration Tests

```bash
# Test full assessment flow
python -m pytest tests/integration/test_websocket_assessment.py

# Test authentication flows
python -m pytest tests/integration/test_websocket_auth.py
```

### Manual Testing

Use WebSocket client tools like `wscat` for manual testing:

```bash
# Connect to assessment endpoint
wscat -c "ws://localhost:8000/ws/assessment?token=YOUR_TOKEN&test_id=123"

# Send messages
{"type": "get_question", "data": {}}
```

## Performance Optimization

### Memory Management

- Connection cleanup for idle sessions
- Graph state optimization
- Message queuing for high load

### Scalability

- Consider horizontal scaling with shared state
- Implement connection pooling
- Use efficient serialization methods

---

This WebSocket implementation provides a robust foundation for real-time AI-powered assessments with comprehensive error handling, security, and scalability considerations.
