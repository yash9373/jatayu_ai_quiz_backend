# WebSocket System Summary

## Key Components Explained

### 1. Connection Manager (`connection_manager.py`)

**Purpose**: Central orchestrator for all WebSocket connections

**Core Concept**: Manages the "who's connected to what" problem with single connection policy

- Tracks active connections by unique ID
- Maps users to their single connection (enforces one connection per user)
- Groups assessment participants for broadcasting
- Handles cleanup of dead connections
- Automatically disconnects existing connection when user reconnects

### 2. Message Handler (`handler.py`)

**Purpose**: Processes incoming messages and orchestrates assessment flow

**Core Concept**: Implements the "conversation engine" for AI assessments

- Routes messages to appropriate handlers
- Manages assessment lifecycle (start → questions → answers → completion)
- Integrates with AI services for dynamic question generation
- Provides error handling and user feedback

## Lifecycle Management

### Connection Establishment

```
Client → WebSocket Connect + JWT Token → Authentication →
Check Existing Connection → Disconnect If Exists →
Register New Connection → Ready for Messages
```

### Assessment Flow

```
START_ASSESSMENT → Create Assessment Instance → Initialize AI → Generate First Question →
Answer Loop (Question → Answer → Feedback → Next Question) → Assessment Complete → Save Results
```

### Disconnection Handling

```
Disconnect Event → Cleanup Connection State → Preserve Assessment in Database →
(Optional) Reconnection → Check Existing Assessment → Recover State → Resume
```

## Message Flow After Authentication

Once authenticated, the client can send these message types:

### 1. `START_ASSESSMENT`

- **Purpose**: Begin taking a test
- **Process**: Validates access → Creates assessment instance → Initializes AI → Sends first question
- **Response**: `ASSESSMENT_STARTED` + first `QUESTION`

### 2. `SUBMIT_ANSWER`

- **Purpose**: Submit answer to current question
- **Process**: AI processes answer → Generates feedback → Updates progress → Determines next step
- **Response**: `ANSWER_FEEDBACK` + `PROGRESS_UPDATE` + (optional) next `QUESTION` or `ASSESSMENT_COMPLETED`

### 3. `GET_QUESTION`

- **Purpose**: Request next question manually
- **Process**: AI generates contextual question based on previous answers
- **Response**: `QUESTION` or `ASSESSMENT_COMPLETED` if done

### 4. `CHAT_MESSAGE`

- **Purpose**: Conversational interaction with AI
- **Process**: AI provides contextual help without revealing answers
- **Response**: `SYSTEM_MESSAGE` with AI response

### 5. `HEARTBEAT`

- **Purpose**: Keep connection alive
- **Process**: Updates activity timestamp
- **Response**: `PONG` with timestamp

## Disconnection & Reconnection Scenarios

### Scenario 1: Multiple Connection Attempt

```
User opens new tab/device while already connected →
New connection request → Authentication successful →
System detects existing connection →
Automatically disconnects old connection →
Establishes new connection →
User continues on new tab/device
```

### Scenario 2: Normal Disconnection

```
User closes browser → WebSocketDisconnect exception →
Connection manager cleans up → Assessment state preserved in database
```

### Scenario 3: Network Interruption

```
Network drops → Connection becomes inactive →
Background cleanup task removes stale connection →
Assessment state remains in database
```

### Scenario 4: Reconnection During Assessment

```
User reconnects with same token + test_id →
Authentication successful →
Connection manager checks for existing assessment →
Found in-progress assessment →
Recovers session state →
Sends current question/progress →
User continues where they left off
```

### Scenario 5: Reconnection After Completion

```
User reconnects after completing assessment →
Authentication successful →
Connection manager checks for existing assessment →
Found completed assessment →
Cannot recover (assessment finalized) →
Would need to start new attempt (if allowed)
```

## State Management

### Connection State

Each WebSocket connection maintains:

- User identity and authentication status
- Current test/assessment being taken
- Activity timestamps for cleanup
- Assessment progress and metadata

### Database Persistence

Assessment state is persisted including:

- Assessment instance ID and status
- Questions asked and answers given
- Progress percentage and timing
- Final results and completion status

### Recovery Logic

```python
# When user reconnects
existing_assessment = check_database_for_assessment(user_id, test_id)

if existing_assessment.status in ['started', 'in_progress']:
    # Can recover - user continues assessment
    recover_session(existing_assessment)
    resume_from_last_state()
elif existing_assessment.status in ['completed', 'abandoned']:
    # Cannot recover - assessment is finalized
    prevent_recovery()
    # May allow new attempt based on business rules
```

## Key Design Benefits

### 1. Resilience

- Automatic cleanup prevents resource leaks
- Database persistence enables seamless recovery
- Single connection policy prevents conflicts and ensures assessment integrity

### 2. Scalability

- Connection pooling with unique IDs
- Efficient lookup structures (user → connection, test → participants)
- Background cleanup prevents memory growth
- Reduced resource usage with one connection per user

### 3. Security

- JWT authentication on connection
- Per-test authorization validation
- Connection isolation and cleanup
- Prevention of multiple simultaneous sessions per user

### 4. User Experience

- Seamless reconnection with state recovery
- Real-time progress tracking
- Conversational AI interaction
- Graceful error handling

## Monitoring Points

### Health Metrics

- `connection_manager.get_active_connections_count()` - Total connections
- `connection_manager.get_user_connections_count(user_id)` - User's connections
- `connection_manager.get_assessment_participants_count(test_id)` - Test participants

### Debugging Information

- Connection details via `get_connection_info(connection_id)`
- Comprehensive logging at each lifecycle stage
- Error tracking with context

This architecture provides a robust foundation for real-time assessment delivery with excellent reliability and user experience.
