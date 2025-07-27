# Frontend WebSocket Integration Guide

## Overview

This guide provides comprehensive documentation for frontend developers to integrate with the Jatayu AI Quiz Backend WebSocket API. The system supports real-time assessment delivery with automatic reconnection, state recovery, and single connection enforcement.

## Table of Contents

1. [Connection Establishment](#connection-establishment)
2. [Authentication](#authentication)
3. [Message Protocol](#message-protocol)
4. [Assessment Flow](#assessment-flow)
5. [Error Handling](#error-handling)
6. [Reconnection & State Recovery](#reconnection--state-recovery)
7. [Complete Message Types Reference](#complete-message-types-reference)
8. [Important Implementation Notes](#important-implementation-notes)
9. [Code Examples](#code-examples)
10. [Best Practices](#best-practices)
11. [Important Implementation Notes](#important-implementation-notes)

---

## Connection Establishment

### WebSocket Endpoint

```
ws://localhost:8000/ws/assessment/{test_id}?token={jwt_token}
```

### Parameters

- `test_id`: Integer ID of the test to take
- `token`: JWT authentication token (URL-encoded)

### Connection Flow

1. **Authentication**: Server validates JWT token
2. **Authorization**: Server checks test access permissions
3. **Single Connection Policy**: Any existing connection for the user is automatically disconnected
4. **Connection Established**: Server sends connection confirmation

---

## Authentication

### JWT Token Requirements

Your JWT token must contain:

```json
{
  "user_id": 123,
  "exp": 1640995200
  // other claims...
}
```

### Example Connection

```javascript
const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...";
const testId = 42;
const wsUrl = `ws://localhost:8000/ws/assessment/${testId}?token=${encodeURIComponent(
  token
)}`;

const websocket = new WebSocket(wsUrl);
```

---

## Message Protocol

All messages are JSON objects with a `type` field indicating the message purpose.

### Message Structure

```typescript
interface WebSocketMessage {
  type: string;
  data?: any;
  error?: string;
  timestamp?: string;
}
```

### Message Types

#### 1. Connection Messages

**Authentication Success**

```json
{
  "type": "auth_success",
  "data": {
    "user_id": 123,
    "connection_id": "123_1640995200.123",
    "timestamp": "2024-01-01T12:00:00.000Z"
  }
}
```

**Connection Error**

```json
{
  "type": "error",
  "data": {
    "error": "Authentication failed",
    "timestamp": "2024-01-01T12:00:00.000Z"
  }
}
```

#### 2. Assessment Control Messages

**Start Assessment Request** (Client → Server)

```json
{
  "type": "start_assessment",
  "data": {
    "test_id": 42
  }
}
```

**Assessment Started Response** (Server → Client)

```json
{
  "type": "assessment_started",
  "data": {
    "assessment_id": 789,
    "thread_id": "789",
    "test_id": 42,
    "message": "Assessment session started successfully"
  }
}
```

**Assessment Recovery** (Server → Client)

```json
{
  "type": "assessment_recovered",
  "data": {
    "assessment_id": 789,
    "thread_id": "789",
    "progress": {
      "answered_questions": 3,
      "total_questions": 10,
      "percentage_complete": 30
    },
    "message": "Previous assessment session recovered"
  }
}
```

#### 3. Question Messages

**Request Next Question** (Client → Server)

```json
{
  "type": "get_question"
}
```

**Question Delivered** (Server → Client)

```json
{
  "type": "question",
  "data": {
    "question_id": "q_001",
    "thread_id": "789",
    "question": {
      "text": "What is the primary purpose of async/await in JavaScript?",
      "options": [
        { "id": "A", "text": "To handle synchronous operations" },
        { "id": "B", "text": "To handle asynchronous operations" },
        { "id": "C", "text": "To create loops" },
        { "id": "D", "text": "To define variables" }
      ],
      "difficulty": "medium",
      "skill": "JavaScript Programming",
      "time_limit": 60
    }
  }
}
```

#### 4. Answer Submission Messages

**Submit Answer** (Client → Server)

```json
{
  "type": "submit_answer",
  "data": {
    "question_id": "q_001",
    "selected_option": "B"
  }
}
```

**Answer Feedback** (Server → Client)

```json
{
  "type": "answer_feedback",
  "data": {
    "question_id": "q_001",
    "feedback": {
      "correct": true,
      "selected_option": "B",
      "correct_answer": "B",
      "message": "Correct answer!"
    },
    "progress": {
      "answered": 4,
      "total": 10,
      "percentage_complete": 40
    },
    "thread_id": "789"
  }
}
```

#### 5. Progress Messages

**Get Progress** (Client → Server)

```json
{
  "type": "get_progress"
}
```

**Progress Update** (Server → Client)

```json
{
  "type": "progress_update",
  "data": {
    "total_questions": 10,
    "answered_questions": 5,
    "percentage_complete": 50,
    "thread_id": "789"
  }
}
```

#### 6. Assessment Completion

**Complete Assessment** (Client → Server)

```json
{
  "type": "complete_assessment"
}
```

**Assessment Results** (Server → Client)

```json
{
  "type": "assessment_completed",
  "data": {
    "final_score": 85.5,
    "correct_answers": 8,
    "total_questions": 10,
    "assessment_id": 789,
    "thread_id": "789",
    "message": "Assessment completed successfully"
  }
}
```

#### 7. Chat and System Messages

**Send Chat Message** (Client → Server)

```json
{
  "type": "chat_message",
  "data": {
    "message": "I need help understanding this question"
  }
}
```

**System Message Response** (Server → Client)

```json
{
  "type": "system_message",
  "data": {
    "message": "I understand you said: 'I need help understanding this question'. I'm here to guide you through the assessment. Would you like me to generate the next question?",
    "timestamp": "2024-01-01T12:00:00.000Z"
  }
}
```

#### 8. Heartbeat/Keep-Alive Messages

**Heartbeat Ping** (Client → Server)

```json
{
  "type": "heartbeat"
}
```

**Heartbeat Pong** (Server → Client)

```json
{
  "type": "pong",
  "data": {
    "timestamp": "2024-01-01T12:00:00.000Z"
  }
}
```

---

## Complete Message Types Reference

### Client → Server Messages

| Message Type          | Required Data                    | Description                                        |
| --------------------- | -------------------------------- | -------------------------------------------------- |
| `start_assessment`    | `test_id`                        | Initiate an assessment session                     |
| `get_question`        | None                             | Request the next question (usually auto-generated) |
| `submit_answer`       | `question_id`, `selected_option` | Submit answer for current question                 |
| `chat_message`        | `message`                        | Send conversational message to AI                  |
| `heartbeat`           | None                             | Keep-alive ping message                            |
| `complete_assessment` | None                             | Finalize the assessment                            |
| `get_test_info`       | None                             | **[Testing]** Get comprehensive test information   |

### Server → Client Messages

| Message Type           | Data Fields                                                                                              | Description                                  |
| ---------------------- | -------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| `auth_success`         | `user_id`, `connection_id`, `timestamp`                                                                  | Authentication successful                    |
| `assessment_started`   | `test_id`, `assessment_id`, `thread_id`, `test_name`, `time_limit_minutes`, `total_questions`, `message` | Assessment session initialized               |
| `assessment_recovered` | `assessment_id`, `thread_id`, `progress`, `message`                                                      | Previous session recovered                   |
| `question`             | `question_id`, `thread_id`, `question` (with text, options, difficulty, skill, time_limit)               | Question delivered                           |
| `answer_feedback`      | `question_id`, `feedback`, `progress`, `thread_id`                                                       | Response to submitted answer                 |
| `progress_update`      | `total_questions`, `answered_questions`, `percentage_complete`, `thread_id`, `timestamp`                 | Progress tracking update                     |
| `assessment_completed` | `message`, `results`, `next_steps`                                                                       | Assessment finalization                      |
| `system_message`       | `message`, `timestamp`                                                                                   | AI system response (chat)                    |
| `pong`                 | `timestamp`                                                                                              | Heartbeat response                           |
| `error`                | `error`, `timestamp`                                                                                     | Error notification                           |
| `test_info`            | `message`, `test_info`, `timestamp`                                                                      | **[Testing]** Comprehensive test information |

### Detailed Payload Schemas

#### Question Payload Schema

```typescript
interface Question {
  question_id: string;
  thread_id: string;
  question: {
    text: string;
    options: Array<{
      id: string; // Usually "A", "B", "C", "D"
      text: string;
    }>;
    difficulty: "easy" | "medium" | "hard";
    skill: string; // e.g., "JavaScript Programming"
    time_limit: number; // seconds
  };
}
```

#### Answer Feedback Schema

```typescript
interface AnswerFeedback {
  question_id: string;
  feedback: {
    correct: boolean;
    selected_option: string;
    correct_answer: string;
    message: string;
  };
  progress: {
    answered: number;
    total: number;
    percentage_complete: number;
  };
  thread_id: string;
}
```

#### Assessment Results Schema

```typescript
interface AssessmentResults {
  message: string;
  results: {
    final_score?: number;
    correct_answers?: number;
    total_questions?: number;
    assessment_id?: number;
    thread_id?: string;
    // Additional result fields from backend
  };
  next_steps: string;
}
```

---

## Assessment Flow

### Typical Assessment Sequence

```mermaid
sequenceDiagram
    participant Client
    participant Server

    Client->>Server: Connect to WebSocket with JWT token
    Server->>Client: auth_success

    Client->>Server: start_assessment
    Server->>Client: assessment_started
    Server->>Client: question (first question auto-generated)

    loop Question Loop
        Client->>Server: submit_answer
        Server->>Client: answer_feedback
        Server->>Client: progress_update
        Server->>Client: question (next question)
    end

    Client->>Server: complete_assessment
    Server->>Client: assessment_completed
```

### State Management

The system maintains state across the entire assessment:

1. **Connection State**: User identity, test context
2. **Assessment State**: Progress, current question, answers
3. **Graph State**: AI conversation context, question generation state

---

## Error Handling

### Error Message Format

```json
{
  "type": "error",
  "data": {
    "error": "Error description",
    "timestamp": "2024-01-01T12:00:00.000Z"
  }
}
```

### Common Error Codes

| Code                | Description                | Action            |
| ------------------- | -------------------------- | ----------------- |
| `AUTH_FAILED`       | Invalid/expired token      | Re-authenticate   |
| `ACCESS_DENIED`     | No permission for test     | Check eligibility |
| `TEST_NOT_FOUND`    | Test doesn't exist         | Verify test ID    |
| `ASSESSMENT_FAILED` | Can't start assessment     | Contact support   |
| `QUESTION_ERROR`    | Question generation failed | Retry or report   |
| `INVALID_ANSWER`    | Answer format invalid      | Resubmit properly |
| `SESSION_EXPIRED`   | Assessment timed out       | Start new attempt |

### Error Handling Example

```javascript
websocket.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === "error") {
    const error = message.data?.error || "Unknown error";

    // Handle specific error patterns
    if (
      error.includes("Authentication failed") ||
      error.includes("Invalid token")
    ) {
      // Redirect to login
      window.location.href = "/login";
    } else if (error.includes("Access denied")) {
      // Show access denied message
      showError("You don't have permission to take this assessment");
    } else if (error.includes("Test not found")) {
      // Show test not found message
      showError("The requested assessment is not available");
    } else if (error.includes("Failed to generate question")) {
      // Retry question generation
      setTimeout(() => {
        sendMessage({ type: "get_question" });
      }, 2000);
    } else {
      // Generic error handling
      showError(error);
    }
  }
};
```

---

## Reconnection & State Recovery

### Automatic Reconnection

The system supports seamless reconnection with state recovery:

1. **Detection**: Client detects connection loss
2. **Reconnection**: Client reconnects with same credentials
3. **Recovery**: Server recovers previous assessment state
4. **Continuation**: Assessment continues from where it left off

### Reconnection Implementation

```javascript
class AssessmentWebSocket {
  constructor(testId, token) {
    this.testId = testId;
    this.token = token;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
    this.connect();
  }

  connect() {
    const wsUrl = `ws://localhost:8000/ws/assessment/${
      this.testId
    }?token=${encodeURIComponent(this.token)}`;
    this.websocket = new WebSocket(wsUrl);

    this.websocket.onopen = this.onOpen.bind(this);
    this.websocket.onmessage = this.onMessage.bind(this);
    this.websocket.onclose = this.onClose.bind(this);
    this.websocket.onerror = this.onError.bind(this);
  }

  onOpen() {
    console.log("WebSocket connected");
    this.reconnectAttempts = 0;
    this.reconnectDelay = 1000;

    // Request assessment state recovery
    this.send({
      type: "start_assessment",
      data: { test_id: this.testId },
    });
  }

  onClose(event) {
    console.log("WebSocket disconnected:", event.code, event.reason);

    if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect();
    }
  }

  onError(error) {
    console.error("WebSocket error:", error);
  }

  scheduleReconnect() {
    this.reconnectAttempts++;

    console.log(
      `Scheduling reconnect attempt ${this.reconnectAttempts} in ${this.reconnectDelay}ms`
    );

    setTimeout(() => {
      this.connect();
    }, this.reconnectDelay);

    // Exponential backoff
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
  }

  send(message) {
    if (this.websocket.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify(message));
    } else {
      console.warn("WebSocket not connected, message queued");
      // You might want to queue messages here
    }
  }
}
```

---

## Automatic Assessment Recovery

### Overview

The system now automatically recovers assessment state when users reconnect. This happens transparently during connection establishment.

### Recovery Process

1. **Connection Established**: User connects with `test_id` parameter
2. **Auto-Recovery Check**: System checks for existing in-progress assessments
3. **State Restoration**: If found, assessment state is automatically restored
4. **Recovery Notification**: Auth success message includes recovery information

### Recovery in Auth Success Message

When an assessment is auto-recovered, the `auth_success` message includes additional information:

```json
{
  "type": "auth_success",
  "data": {
    "user_id": 123,
    "connection_id": "123_456",
    "timestamp": "2025-01-20T10:30:00.000Z",
    "recovered_assessment": {
      "assessment_id": 789,
      "test_id": 456,
      "thread_id": "789",
      "is_in_assessment": true
    }
  }
}
```

### Frontend Handling

```javascript
wsConnection.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === "auth_success") {
    const { data } = message;

    if (data.recovered_assessment) {
      console.log("Assessment recovered:", data.recovered_assessment);

      // Update UI to show resumed assessment
      showAssessmentResumed(data.recovered_assessment);

      // Optionally request current question
      wsConnection.send(
        JSON.stringify({
          type: "get_question",
          data: {},
        })
      );
    } else {
      console.log("New connection established");
      showWelcomeScreen();
    }
  }
};
```

### Benefits

- **Seamless Experience**: Users can refresh browsers or reconnect without losing progress
- **Automatic**: No manual recovery action required
- **Transparent**: Frontend gets notified about recovery status
- **Robust**: Works across network disconnections and device switches

---

## Code Examples

### Complete React Hook Implementation

```typescript
import { useState, useEffect, useRef, useCallback } from "react";

interface Question {
  text: string;
  options: Array<{
    id: string;
    text: string;
  }>;
  difficulty: string;
  skill: string;
  time_limit: number;
}

interface Progress {
  answered: number;
  total: number;
  percentage_complete: number;
}

interface AssessmentState {
  connected: boolean;
  assessmentStarted: boolean;
  currentQuestion: Question | null;
  progress: Progress | null;
  error: string | null;
  completed: boolean;
  finalScore: number | null;
}

export const useAssessmentWebSocket = (testId: number, token: string) => {
  const [state, setState] = useState<AssessmentState>({
    connected: false,
    assessmentStarted: false,
    currentQuestion: null,
    progress: null,
    error: null,
    completed: false,
    finalScore: null,
  });

  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);

  const connect = useCallback(() => {
    const wsUrl = `ws://localhost:8000/ws/assessment/${testId}?token=${encodeURIComponent(
      token
    )}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("Connected to assessment WebSocket");
      websocketRef.current = ws;
      reconnectAttemptsRef.current = 0;

      setState((prev) => ({ ...prev, connected: true, error: null }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleMessage(message);
    };

    ws.onclose = (event) => {
      websocketRef.current = null;
      setState((prev) => ({ ...prev, connected: false }));

      if (!event.wasClean && reconnectAttemptsRef.current < 5) {
        scheduleReconnect();
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setState((prev) => ({ ...prev, error: "Connection error occurred" }));
    };
  }, [testId, token]);

  const scheduleReconnect = useCallback(() => {
    reconnectAttemptsRef.current++;
    const delay = Math.min(
      1000 * Math.pow(2, reconnectAttemptsRef.current - 1),
      30000
    );

    reconnectTimeoutRef.current = setTimeout(() => {
      connect();
    }, delay);
  }, [connect]);
  const handleMessage = (message: any) => {
    switch (message.type) {
      case "auth_success":
        // Auto-start assessment after successful authentication
        startAssessment();
        break;

      case "assessment_started":
        setState((prev) => ({
          ...prev,
          assessmentStarted: true,
          error: null,
        }));
        // First question is auto-generated, no need to request
        break;

      case "assessment_recovered":
        setState((prev) => ({
          ...prev,
          assessmentStarted: true,
          progress: message.data.progress,
          error: null,
        }));
        // Request current question after recovery
        requestQuestion();
        break;

      case "question":
        setState((prev) => ({
          ...prev,
          currentQuestion: message.data.question,
          error: null,
        }));
        break;

      case "answer_feedback":
        setState((prev) => ({
          ...prev,
          progress: message.data.progress,
        }));
        // Questions are auto-generated after feedback, no need to request
        break;

      case "progress_update":
        setState((prev) => ({
          ...prev,
          progress: message.data,
        }));
        break;

      case "system_message":
        // Handle system messages (e.g., chat responses)
        console.log("System message:", message.data.message);
        break;

      case "pong":
        // Handle heartbeat response
        console.log("Heartbeat response received");
        break;
          ...prev,
          currentQuestion: message.data.question,
          error: null,
        }));
        break;

      case "answer_feedback":
        setState((prev) => ({
          ...prev,
          progress: message.data.progress,
        }));
        // Auto-request next question
        if (message.data.progress.answered < message.data.progress.total) {
          setTimeout(() => requestQuestion(), 1000);
        }
        break;

      case "progress_update":
        setState((prev) => ({
          ...prev,
          progress: message.data,
        }));
        break;

      case "assessment_completed":
        setState((prev) => ({
          ...prev,
          completed: true,
          finalScore: message.data.final_score,
        }));
        break;

      case "error":
        setState((prev) => ({
          ...prev,
          error: message.error,
        }));
        break;
    }
  };

  const sendMessage = useCallback((message: any) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify(message));
    }
  }, []);

  const startAssessment = useCallback(() => {
    sendMessage({
      type: "start_assessment",
      data: { test_id: testId },
    });
  }, [sendMessage, testId]);

  const requestQuestion = useCallback(() => {
    sendMessage({ type: "get_question" });
  }, [sendMessage]);

  const submitAnswer = useCallback(
    (questionId: string, selectedOption: string) => {
      sendMessage({
        type: "submit_answer",
        data: {
          question_id: questionId,
          selected_option: selectedOption,
        },
      });
    },
    [sendMessage]
  );

  const completeAssessment = useCallback(() => {
    sendMessage({ type: "complete_assessment" });
  }, [sendMessage]);

  const getProgress = useCallback(() => {
    sendMessage({ type: "get_progress" });
  }, [sendMessage]);

  const sendChatMessage = useCallback(
    (message: string) => {
      sendMessage({
        type: "chat_message",
        data: { message },
      });
    },
    [sendMessage]
  );

  const sendHeartbeat = useCallback(() => {
    sendMessage({ type: "heartbeat" });
  }, [sendMessage]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, [connect]);

  return {
    ...state,
    submitAnswer,
    completeAssessment,
    getProgress,
    requestQuestion,
    sendChatMessage,
    sendHeartbeat,
  };
};
```

### React Component Usage

```tsx
import React, { useState } from "react";
import { useAssessmentWebSocket } from "./useAssessmentWebSocket";

const AssessmentComponent: React.FC = () => {
  const testId = 42;
  const token = localStorage.getItem("authToken") || "";

  const {
    connected,
    assessmentStarted,
    currentQuestion,
    progress,
    error,
    completed,
    finalScore,
    submitAnswer,
    completeAssessment,
  } = useAssessmentWebSocket(testId, token);

  const [selectedOption, setSelectedOption] = useState<string>("");

  const handleSubmitAnswer = () => {
    if (currentQuestion && selectedOption) {
      submitAnswer("current_question_id", selectedOption);
      setSelectedOption("");
    }
  };

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  if (!connected) {
    return <div className="loading">Connecting to assessment...</div>;
  }

  if (completed) {
    return (
      <div className="completion">
        <h2>Assessment Completed!</h2>
        <p>Your Score: {finalScore}%</p>
      </div>
    );
  }

  if (!assessmentStarted) {
    return <div className="loading">Starting assessment...</div>;
  }

  if (!currentQuestion) {
    return <div className="loading">Loading question...</div>;
  }

  return (
    <div className="assessment">
      {progress && (
        <div className="progress">
          Progress: {progress.answered}/{progress.total} (
          {progress.percentage_complete.toFixed(1)}%)
        </div>
      )}

      <div className="question">
        <h3>{currentQuestion.text}</h3>

        <div className="options">
          {currentQuestion.options.map((option) => (
            <label key={option.id} className="option">
              <input
                type="radio"
                name="answer"
                value={option.id}
                checked={selectedOption === option.id}
                onChange={(e) => setSelectedOption(e.target.value)}
              />
              {option.text}
            </label>
          ))}
        </div>

        <button
          onClick={handleSubmitAnswer}
          disabled={!selectedOption}
          className="submit-btn"
        >
          Submit Answer
        </button>
      </div>

      {progress?.answered === progress?.total && (
        <button onClick={completeAssessment} className="complete-btn">
          Complete Assessment
        </button>
      )}
    </div>
  );
};

export default AssessmentComponent;
```

---

## Best Practices

### 1. Connection Management

- **Always handle reconnection**: Network issues are common
- **Implement exponential backoff**: Prevent server overload
- **Clean up connections**: Avoid memory leaks

### 2. State Management

- **Trust server state**: Server maintains authoritative state
- **Handle recovery gracefully**: Users expect seamless reconnection
- **Show connection status**: Keep users informed

### 3. User Experience

- **Loading states**: Show progress during connections/requests
- **Error feedback**: Provide clear, actionable error messages
- **Offline handling**: Handle network disconnections gracefully

### 4. Security

- **Secure token storage**: Use appropriate storage mechanisms
- **Token refresh**: Handle token expiration
- **Validate inputs**: Client-side validation for better UX

### 5. Performance

- **Message queuing**: Queue messages during disconnection
- **Debounce rapid actions**: Prevent message flooding
- **Cleanup timeouts**: Clear intervals and timeouts

### 6. Testing

- **Test reconnection**: Simulate network issues
- **Test recovery**: Verify state recovery works
- **Test error scenarios**: Handle various error conditions

---

## Important Implementation Notes

### Auto-Generated First Question

The backend automatically generates and sends the first question after `assessment_started`. Frontend should not send `get_question` after starting an assessment.

### Thread ID Management

- `thread_id` is always equal to `assessment_id` (both are the database assessment instance ID)
- `thread_id` is used for maintaining conversation state with the AI
- Always include `thread_id` in question-related operations

### Assessment Recovery

When reconnecting, the system automatically checks for existing assessment sessions and sends `assessment_recovered` instead of `assessment_started` if a session exists.

### Single Connection Policy

The backend enforces one connection per user. New connections automatically disconnect existing ones for the same user.

### Chat Functionality

The system supports conversational messages via `chat_message` type, which receives `system_message` responses from the AI.

### Automatic Progress Updates

Progress updates are automatically sent after each answer submission, eliminating the need to manually request progress.

---

## Troubleshooting

### Common Issues

1. **Connection Fails**

   - Check WebSocket URL format
   - Verify JWT token is valid and not expired
   - Ensure test_id exists and is accessible

2. **No Questions Received**

   - Verify assessment was started successfully
   - Check if assessment is in recoverable state
   - Look for error messages

3. **Answers Not Accepted**

   - Ensure question_id matches current question
   - Verify option format (usually single character)
   - Check if assessment is still active

4. **Reconnection Issues**
   - Implement proper error handling
   - Use exponential backoff
   - Check server-side connection limits

### Debug Tips

```javascript
// Enable debug logging
websocket.onmessage = (event) => {
  console.log("📨 Received:", JSON.parse(event.data));
  // ... handle message
};

websocket.send = (data) => {
  console.log("📤 Sending:", JSON.parse(data));
  WebSocket.prototype.send.call(websocket, data);
};
```

---

## Support

For technical support or questions:

- Check server logs for detailed error information
- Verify network connectivity and WebSocket support
- Contact the backend development team with connection details

---

_This documentation covers the complete frontend integration for the Jatayu AI Quiz Backend WebSocket API. Keep this guide updated as the API evolves._

---

## Testing and Debug Messages

### Get Test Information (`get_test_info` → `test_info`)

**Purpose**: For testing and debugging purposes, retrieve comprehensive information about the current test session. This message provides complete visibility into the connection state, test configuration, assessment progress, and underlying graph state.

**Requirements**:

- Must have an active assessment session (be authenticated and in assessment)
- Connection must have a valid `thread_id` and `assessment_id`

**Client Request:**

```json
{
  "type": "get_test_info",
  "data": {}
}
```

**Server Response:**

```json
{
  "type": "test_info",
  "data": {
    "message": "Test information retrieved for thread_id: 789",
    "test_info": {
      "connection_info": {
        "connection_id": "123_456",
        "user_id": 123,
        "thread_id": "789",
        "assessment_id": 789,
        "is_authenticated": true,
        "is_in_assessment": true,
        "graph_initialized": true,
        "connected_at": "2025-01-20T10:00:00.000Z",
        "last_activity": "2025-01-20T10:30:00.000Z",
        "assessment_started_at": "2025-01-20T10:05:00.000Z"
      },
      "test_details": {
        "test_id": 456,
        "test_name": "Frontend Developer Assessment",
        "description": "Comprehensive assessment for frontend development skills",
        "time_limit_minutes": 60,
        "total_questions": 20,
        "difficulty_level": "intermediate",
        "status": "live",
        "created_at": "2025-01-15T08:00:00.000Z",
        "assessment_deadline": "2025-01-25T18:00:00.000Z"
      },
      "assessment_details": {
        "assessment_id": 789,
        "status": "in_progress",
        "started_at": "2025-01-20T10:05:00.000Z",
        "completed_at": null,
        "score": null,
        "total_questions_answered": 0
      },
      "graph_state": {
        "has_state": true,
        "thread_id": "789",
        "generated_questions_count": 3,
        "responses_count": 2,
        "generated_questions": {
          "1": {
            "question_text": "What is the virtual DOM in React?",
            "options": [
              { "id": "A", "text": "A virtual representation of the real DOM" },
              { "id": "B", "text": "A testing framework for React" },
              { "id": "C", "text": "A state management library" },
              { "id": "D", "text": "A CSS-in-JS solution" }
            ],
            "correct_answer": "A",
            "difficulty": "medium",
            "skill": "React Development"
          },
          "2": {
            "question_text": "What is JSX in React?",
            "options": [
              { "id": "A", "text": "JavaScript XML syntax extension" },
              { "id": "B", "text": "Java Syntax Extension" },
              { "id": "C", "text": "JSON Extended Syntax" },
              { "id": "D", "text": "JavaScript eXtended" }
            ],
            "correct_answer": "A",
            "difficulty": "easy",
            "skill": "React Fundamentals"
          }
        },
        "responses": {
          "1": {
            "selected_option": "A",
            "timestamp": "2025-01-20T10:15:00.000Z"
          },
          "2": {
            "selected_option": "A",
            "timestamp": "2025-01-20T10:20:00.000Z"
          }
        }
      }
    },
    "timestamp": "2025-01-20T10:30:00.000Z"
  }
}
```

**Error Cases:**

If no active assessment is found:

```json
{
  "type": "error",
  "data": {
    "error": "No active assessment found for this connection",
    "timestamp": "2025-01-20T10:30:00.000Z"
  }
}
```

If connection is not found:

```json
{
  "type": "error",
  "data": {
    "error": "Connection not found",
    "timestamp": "2025-01-20T10:30:00.000Z"
  }
}
```

**Data Structure Details:**

- **connection_info**: Real-time WebSocket connection state and metadata
- **test_details**: Static test configuration from the database
- **assessment_details**: Current assessment instance progress and status
- **graph_state**: AI conversation graph state including all generated questions and responses

**Graph State Information:**

The `graph_state` section provides detailed insight into the AI assessment engine:

- `has_state`: Whether the connection has an active graph state
- `generated_questions_count`: Total number of questions generated by AI
- `responses_count`: Number of questions answered by the candidate
- `generated_questions`: Complete question objects with metadata
- `responses`: User responses with timestamps

**Question Object Structure:**

Each question in `generated_questions` contains:

- `question_text`: The actual question text
- `options`: Array of answer choices with `id` and `text`
- `correct_answer`: The correct option ID
- `difficulty`: Question difficulty level
- `skill`: Associated skill area

**Response Object Structure:**

Each response in `responses` contains:

- `selected_option`: The option ID selected by the user
- `timestamp`: When the answer was submitted
  "connection_id": "123_456",
  "user_id": 123,
  "thread_id": "789",
  "assessment_id": 789,
  "is_authenticated": true,
  "is_in_assessment": true,
  "graph_initialized": true,
  "connected_at": "2025-01-20T10:00:00.000Z",
  "last_activity": "2025-01-20T10:30:00.000Z",
  "assessment_started_at": "2025-01-20T10:05:00.000Z"
  },
  "test_details": {
  "test_id": 456,
  "test_name": "Frontend Developer Assessment",
  "description": "Comprehensive assessment for frontend development skills",
  "time_limit_minutes": 60,
  "total_questions": 20,
  "difficulty_level": "intermediate",
  "status": "live",
  "created_at": "2025-01-15T08:00:00.000Z",
  "assessment_deadline": "2025-01-25T18:00:00.000Z"
  },
  "assessment_details": {
  "assessment_id": 789,
  "status": "in_progress",
  "started_at": "2025-01-20T10:05:00.000Z",
  "completed_at": null,
  "score": null,
  "total_questions_answered": 5
  },
  "graph_state": {
  "has_state": true,
  "thread_id": "789",
  "generated_questions_count": 3,
  "responses_count": 2,
  "generated_questions": {
  "1": {
  "question_text": "What is React?",
  "options": ["A library", "A framework", "A language"],
  "correct_answer": "A library",
  "difficulty": "easy"
  },
  "2": {
  "question_text": "What is JSX?",
  "options": ["JavaScript XML", "Java Syntax", "JSON Extended"],
  "correct_answer": "JavaScript XML",
  "difficulty": "medium"
  }
  },
  "responses": {
  "1": {
  "selected_option": "A library",
  "timestamp": "2025-01-20T10:15:00.000Z"
  },
  "2": {
  "selected_option": "JavaScript XML",
  "timestamp": "2025-01-20T10:20:00.000Z"
  }
  }
  }
  },
  "timestamp": "2025-01-20T10:30:00.000Z"
  }
  }

````

**Use Cases:**

- **Development & Testing**: Inspect assessment state during development
- **Debugging**: Troubleshoot connection or assessment issues
- **State Verification**: Verify thread_id and assessment_id mapping after recovery
- **Progress Monitoring**: Check real-time assessment progress and timing
- **Test Configuration Validation**: Ensure test settings are loaded correctly
- **Graph State Analysis**: Examine AI-generated questions and user responses

**Frontend Implementation Examples:**

#### Basic Usage

```javascript
// Request test information for debugging
function requestTestInfo() {
  if (wsConnection.readyState === WebSocket.OPEN) {
    wsConnection.send(
      JSON.stringify({
        type: "get_test_info",
        data: {},
      })
    );
  } else {
    console.warn("WebSocket not connected");
  }
}

// Handle test info response
wsConnection.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === "test_info") {
    const { test_info } = message.data;

    console.log("Connection Info:", test_info.connection_info);
    console.log("Test Details:", test_info.test_details);
    console.log("Assessment Status:", test_info.assessment_details);
    console.log("Graph State:", test_info.graph_state);

    // Display in debug panel
    updateDebugPanel(test_info);
  }
};
````

#### Advanced Debug Panel

```javascript
function createDebugPanel(testInfo) {
  const debugPanel = document.createElement("div");
  debugPanel.className = "debug-panel";

  debugPanel.innerHTML = `
    <h3>Assessment Debug Information</h3>
    
    <div class="debug-section">
      <h4>Connection Status</h4>
      <p>Connection ID: ${testInfo.connection_info.connection_id}</p>
      <p>User ID: ${testInfo.connection_info.user_id}</p>
      <p>Thread ID: ${testInfo.connection_info.thread_id}</p>
      <p>Assessment ID: ${testInfo.connection_info.assessment_id}</p>
      <p>Authenticated: ${testInfo.connection_info.is_authenticated}</p>
      <p>In Assessment: ${testInfo.connection_info.is_in_assessment}</p>
      <p>Graph Initialized: ${testInfo.connection_info.graph_initialized}</p>
    </div>
    
    <div class="debug-section">
      <h4>Test Configuration</h4>
      <p>Test Name: ${testInfo.test_details.test_name}</p>
      <p>Time Limit: ${testInfo.test_details.time_limit_minutes} minutes</p>
      <p>Total Questions: ${testInfo.test_details.total_questions}</p>
      <p>Difficulty: ${testInfo.test_details.difficulty_level}</p>
      <p>Status: ${testInfo.test_details.status}</p>
    </div>
    
    <div class="debug-section">
      <h4>Assessment Progress</h4>
      <p>Status: ${testInfo.assessment_details?.status || "Not started"}</p>
      <p>Questions Answered: ${
        testInfo.assessment_details?.total_questions_answered || 0
      }</p>
      <p>Started: ${
        testInfo.assessment_details?.started_at || "Not started"
      }</p>
      <p>Score: ${testInfo.assessment_details?.score || "Not calculated"}</p>
    </div>
    
    <div class="debug-section">
      <h4>AI Graph State</h4>
      <p>Has State: ${testInfo.graph_state.has_state}</p>
      <p>Questions Generated: ${
        testInfo.graph_state.generated_questions_count
      }</p>
      <p>Responses Count: ${testInfo.graph_state.responses_count}</p>
    </div>
  `;

  return debugPanel;
}

// Usage in development tools
function addDebugControls() {
  const debugControls = document.createElement("div");
  debugControls.className = "debug-controls";
  debugControls.style.cssText = `
    position: fixed;
    top: 10px;
    right: 10px;
    background: rgba(0,0,0,0.8);
    color: white;
    padding: 10px;
    border-radius: 5px;
    z-index: 9999;
  `;

  debugControls.innerHTML = `
    <button onclick="requestTestInfo()">Get Test Info</button>
    <button onclick="toggleDebugPanel()">Toggle Debug Panel</button>
  `;

  document.body.appendChild(debugControls);
}
```

#### Automated State Monitoring

```javascript
class AssessmentStateMonitor {
  constructor(wsConnection) {
    this.ws = wsConnection;
    this.monitoringInterval = null;
    this.lastState = null;
  }

  startMonitoring(intervalMs = 30000) {
    this.monitoringInterval = setInterval(() => {
      this.checkState();
    }, intervalMs);
  }

  stopMonitoring() {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }
  }

  checkState() {
    this.ws.send(
      JSON.stringify({
        type: "get_test_info",
        data: {},
      })
    );
  }

  onStateReceived(testInfo) {
    const currentState = {
      questionsAnswered:
        testInfo.assessment_details?.total_questions_answered || 0,
      graphQuestions: testInfo.graph_state.generated_questions_count,
      graphResponses: testInfo.graph_state.responses_count,
      timestamp: new Date().toISOString(),
    };

    if (this.lastState) {
      // Check for changes
      if (currentState.questionsAnswered !== this.lastState.questionsAnswered) {
        console.log(
          `Progress update: ${currentState.questionsAnswered} questions answered`
        );
      }

      if (currentState.graphQuestions !== this.lastState.graphQuestions) {
        console.log(
          `New questions generated: ${currentState.graphQuestions} total`
        );
      }
    }

    this.lastState = currentState;
  }
}

// Usage
const stateMonitor = new AssessmentStateMonitor(wsConnection);
stateMonitor.startMonitoring(15000); // Check every 15 seconds
```

**Important Notes:**

- **Development Only**: This message type is intended for testing and debugging purposes
- **Authentication Required**: Must have an active assessment session to use
- **Performance**: Avoid frequent polling in production; use for debugging only
- **State Visibility**: Provides complete visibility into internal assessment state
- **Thread Safety**: Safe to call during active assessment without affecting user experience

#### TypeScript Type Definitions

For better development experience, here are the TypeScript interfaces for the `test_info` response:

```typescript
interface ConnectionInfo {
  connection_id: string;
  user_id: number;
  thread_id: string;
  assessment_id: number;
  is_authenticated: boolean;
  is_in_assessment: boolean;
  graph_initialized: boolean;
  connected_at: string;
  last_activity: string;
  assessment_started_at: string;
}

interface TestDetails {
  test_id: number;
  test_name: string;
  description: string;
  time_limit_minutes: number;
  total_questions: number;
  difficulty_level: string;
  status: string;
  created_at: string;
  assessment_deadline: string;
}

interface AssessmentDetails {
  assessment_id: number;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  score: number | null;
  total_questions_answered: number;
}

interface QuestionOption {
  id: string;
  text: string;
}

interface GeneratedQuestion {
  question_text: string;
  options: QuestionOption[];
  correct_answer: string;
  difficulty: string;
  skill: string;
}

interface UserResponse {
  selected_option: string;
  timestamp: string;
}

interface GraphState {
  has_state: boolean;
  thread_id: string;
  generated_questions_count: number;
  responses_count: number;
  generated_questions: Record<string, GeneratedQuestion>;
  responses: Record<string, UserResponse>;
}

interface TestInfo {
  connection_info: ConnectionInfo;
  test_details: TestDetails;
  assessment_details: AssessmentDetails | null;
  graph_state: GraphState;
}

interface TestInfoMessage {
  type: "test_info";
  data: {
    message: string;
    test_info: TestInfo;
    timestamp: string;
  };
}

// Usage example with proper typing
const handleTestInfo = (message: TestInfoMessage) => {
  const { test_info } = message.data;

  // Type-safe access to all properties
  console.log(
    `Assessment ${test_info.assessment_details?.assessment_id} for test "${test_info.test_details.test_name}"`
  );
  console.log(
    `Progress: ${test_info.graph_state.responses_count}/${test_info.graph_state.generated_questions_count} questions answered`
  );

  // Iterate through questions with type safety
  Object.entries(test_info.graph_state.generated_questions).forEach(
    ([questionId, question]) => {
      console.log(`Question ${questionId}: ${question.question_text}`);
      console.log(
        `Skill: ${question.skill}, Difficulty: ${question.difficulty}`
      );
    }
  );
};
```
