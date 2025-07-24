import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Any, List
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.websocket.connection_manager import connection_manager, ConnectionState
from app.db.database import get_db
from app.services.websocket_assessment_service import assessment_graph_service
from app.services.mcq_generation.state import AgentState, Question, Response, GraphNodeState
from app.repositories.test_repo import TestRepository
from app.repositories.candidate_application_repo import CandidateApplicationRepository
from app.models.test import Test

logger = logging.getLogger(__name__)


class WebSocketMessageType:
    """Constants for WebSocket message types"""

    # Connection events
    CONNECT = "connect"
    DISCONNECT = "disconnect"

    # Authentication
    AUTH = "auth"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILED = "auth_failed"

    # Assessment lifecycle
    START_ASSESSMENT = "start_assessment"
    ASSESSMENT_STARTED = "assessment_started"
    ASSESSMENT_ERROR = "assessment_error"
    ASSESSMENT_COMPLETED = "assessment_completed"

    # Question handling
    GET_QUESTION = "get_question"
    QUESTION = "question"
    SUBMIT_ANSWER = "submit_answer"
    ANSWER_FEEDBACK = "answer_feedback"

    # Progress tracking
    PROGRESS_UPDATE = "progress_update"

    # System messages
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    PONG = "pong"

    # Chat messages
    CHAT_MESSAGE = "chat_message"
    SYSTEM_MESSAGE = "system_message"


class AssessmentWebSocketHandler:
    """
    Handles WebSocket communication for AI-powered assessment chatbot

    This class manages the entire conversation flow between the client and the AI
    assessment system. It orchestrates question generation, answer processing,
    progress tracking, and result finalization.

    Key Responsibilities:
    - Connection lifecycle management (authentication, authorization, cleanup)
    - Message routing based on message type
    - Assessment session orchestration
    - Error handling and user feedback
    - Integration with AI services for dynamic question generation

    Message Flow:
    1. Client connects -> Authentication -> Connection established
    2. Client requests assessment start -> Validation -> Assessment initialized
    3. Questions generated dynamically by AI -> Sent to client
    4. Client submits answers -> Processed by AI -> Feedback provided
    5. Assessment completion -> Results saved -> Final feedback sent

    Reconnection Support:
    The handler seamlessly supports reconnection scenarios by:
    - Checking for existing assessment sessions
    - Recovering assessment state from database
    - Resuming from the last known progress point
    """

    def __init__(self):
        pass

    async def handle_connection(
        self,
        websocket: WebSocket,
        token: Optional[str] = None,
        test_id: Optional[int] = None,
        db: AsyncSession = Depends(get_db)
    ):
        """
        Main WebSocket connection handler - orchestrates the entire connection lifecycle

        This is the entry point for all WebSocket connections. It handles the complete
        lifecycle from initial connection through authentication, authorization, message
        processing, and cleanup.

        Connection Lifecycle:
        1. Authentication: Validate JWT token and extract user identity
        2. Connection Establishment: Register connection with connection manager
        3. Authorization: Validate test access if test_id provided
        4. Message Loop: Process incoming messages until disconnection
        5. Cleanup: Remove connection and clean up resources

        Args:
            websocket: The WebSocket connection object
            token: JWT authentication token (required)
            test_id: Optional test ID if joining specific assessment
            db: Database session dependency

        Error Handling:
        - Authentication failures -> Close with 4001 (Unauthorized)
        - Authorization failures -> Close with 4003 (Forbidden)
        - Network disconnections -> Graceful cleanup and logging
        - Unexpected errors -> Error message + cleanup

        Reconnection Scenario:
        If a user reconnects with the same token and test_id, the system will:
        1. Authenticate the user
        2. Check for existing assessment sessions
        3. Recover state if assessment is in progress
        4. Resume from last known state
        """
        connection_id = None

        try:
            # Step 1: Authenticate the connection
            if not token:
                await websocket.close(code=4001, reason="Token required")
                return

            user_id = await connection_manager.authenticate_connection(websocket, token)
            if not user_id:
                await websocket.close(code=4001, reason="Authentication failed")
                return

            # Step 2: Establish connection in connection manager
            connection_id = await connection_manager.connect(websocket, user_id, test_id)

            # Step 3: Send authentication success confirmation
            await self._send_message(connection_id, {
                "type": WebSocketMessageType.AUTH_SUCCESS,
                "data": {
                    "user_id": user_id,
                    "connection_id": connection_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })

            # Step 4: If test_id provided, validate assessment access
            if test_id:
                access_granted = await connection_manager.validate_assessment_access(
                    connection_id, test_id, db
                )
                if not access_granted:
                    await self._send_error(connection_id, "Access denied for this assessment")
                    await websocket.close(code=4003, reason="Assessment access denied")
                    return

            # Step 5: Start message handling loop
            await self._handle_messages(connection_id, websocket, db)

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {connection_id}")
        except Exception as e:
            logger.error(f"Error in WebSocket handler: {str(e)}")
            if connection_id:
                await self._send_error(connection_id, f"Internal server error: {str(e)}")
        finally:
            # Cleanup: Always clean up resources on exit
            if connection_id:
                await connection_manager.disconnect(connection_id)
                # Clean up assessment service state
                assessment_graph_service.cleanup_connection(connection_id)

    async def _handle_messages(self, connection_id: str, websocket: WebSocket, db: AsyncSession):
        """
        Handle incoming WebSocket messages in a continuous loop

        This method runs continuously until the WebSocket connection is closed,
        processing each incoming message and routing it to the appropriate handler.

        Message Processing:
        1. Receive and parse JSON message
        2. Extract message type and data
        3. Route to appropriate handler method
        4. Handle errors and provide feedback

        Error Handling:
        - JSON parsing errors -> Send error message to client
        - Unknown message types -> Send error message to client  
        - Handler exceptions -> Log error and send error message
        - WebSocket disconnection -> Exit loop gracefully

        Activity Tracking:
        Each processed message updates the connection's last_activity timestamp
        through the connection manager, which is used for cleanup purposes.
        """

        while True:
            try:
                # Wait for message from client
                data = await websocket.receive_text()
                message = json.loads(data)

                message_type = message.get("type")
                message_data = message.get("data", {})

                logger.info(
                    f"Received message: {message_type} from {connection_id}")

                # Route message to appropriate handler
                await self._route_message(connection_id, message_type, message_data, db)

            except WebSocketDisconnect:
                # Normal disconnection - exit loop
                break
            except json.JSONDecodeError:
                # Invalid JSON - notify client
                await self._send_error(connection_id, "Invalid JSON format")
            except Exception as e:
                # Unexpected error - log and notify client
                logger.error(f"Error handling message: {str(e)}")
                await self._send_error(connection_id, f"Error processing message: {str(e)}")

    async def _route_message(self, connection_id: str, message_type: str, data: Dict, db: AsyncSession):
        """
        Route messages to appropriate handlers based on message type

        This method implements the message dispatching logic, mapping message types
        to their corresponding handler methods. It provides a clean separation of
        concerns and makes it easy to add new message types.

        Supported Message Types:
        - START_ASSESSMENT: Initialize a new assessment session
        - GET_QUESTION: Request the next question in sequence
        - SUBMIT_ANSWER: Submit an answer for the current question
        - CHAT_MESSAGE: Send conversational message to AI
        - HEARTBEAT: Keep-alive ping message

        Args:
            connection_id: Identifier for the WebSocket connection
            message_type: String identifying the type of message
            data: Dictionary containing message payload
            db: Database session for data operations

        Error Handling:
        If an unknown message type is received, an error is sent back to the client
        rather than raising an exception, allowing the connection to continue.
        """

        handlers = {
            WebSocketMessageType.START_ASSESSMENT: self._handle_start_assessment,
            WebSocketMessageType.GET_QUESTION: self._handle_get_question,
            WebSocketMessageType.SUBMIT_ANSWER: self._handle_submit_answer,
            WebSocketMessageType.CHAT_MESSAGE: self._handle_chat_message,
            WebSocketMessageType.HEARTBEAT: self._handle_heartbeat,
        }

        handler = handlers.get(message_type)
        if handler:
            await handler(connection_id, data, db)
        else:
            await self._send_error(connection_id, f"Unknown message type: {message_type}")

    async def _handle_start_assessment(self, connection_id: str, data: Dict, db: AsyncSession):
        """
        Handle assessment start request
        Initialize MCQ generation graph and begin assessment flow

        This method now properly handles thread_id management to ensure
        graph state persistence and recovery.
        """
        try:
            test_id = data.get("test_id")
            if not test_id:
                await self._send_error(connection_id, "test_id is required")
                return

            # Validate assessment access again
            access_granted = await connection_manager.validate_assessment_access(
                connection_id, test_id, db
            )
            if not access_granted:
                await self._send_error(connection_id, "Access denied for this assessment")
                return

            # Get test details
            test_repo = TestRepository(db)
            test = await test_repo.get_test_by_id(test_id)
            if not test:
                await self._send_error(connection_id, "Test not found")
                return

            # Start assessment session and create assessment instance
            assessment_id = await connection_manager.start_assessment_session(connection_id, test_id, db)

            if not assessment_id:
                await self._send_error(connection_id, "Failed to create assessment instance")
                return

            # Initialize MCQ generation graph with proper thread_id management
            graph_initialized = await assessment_graph_service.initialize_assessment_graph(
                connection_id, test, assessment_id,
                connection_manager.active_connections[connection_id].user_id, db
            )

            if not graph_initialized:
                await self._send_error(connection_id, "Failed to initialize assessment")
                return

            # Mark graph as initialized in connection state
            connection_manager.mark_graph_initialized(connection_id)

            await self._send_message(connection_id, {
                "type": WebSocketMessageType.ASSESSMENT_STARTED,
                "data": {
                    "test_id": test_id,
                    "assessment_id": assessment_id,
                    "thread_id": str(assessment_id),
                    "test_name": test.test_name,
                    "time_limit_minutes": test.time_limit_minutes,
                    "total_questions": test.total_questions,
                    "message": "Assessment started! I'm your AI interviewer. Let's begin with some questions based on the job requirements."
                }
            })

            # Generate first question automatically
            await self._generate_next_question(connection_id, test_id, db)

        except Exception as e:
            logger.error(f"Error starting assessment: {str(e)}", exc_info=True)
            await self._send_error(connection_id, f"Failed to start assessment: {str(e)}")

    async def _handle_get_question(self, connection_id: str, data: Dict, db: AsyncSession):
        """
        Handle request for next question
        Uses MCQ generation service to create contextual questions with proper thread_id management
        """
        try:
            question_data = await assessment_graph_service.generate_question(connection_id)

            if question_data:
                await self._send_message(connection_id, {
                    "type": WebSocketMessageType.QUESTION,
                    "data": question_data
                })
            else:
                # Assessment complete or error
                await self._finalize_assessment(connection_id, db)

        except Exception as e:
            logger.error(f"Error generating question: {str(e)}", exc_info=True)
            await self._send_error(connection_id, f"Failed to generate question: {str(e)}")

    async def _handle_submit_answer(self, connection_id: str, data: Dict, db: AsyncSession):
        """
        Handle answer submission
        Process the answer using proper thread_id management to maintain state
        """
        try:
            question_id = data.get("question_id")
            selected_option = data.get("selected_option")

            if not question_id or not selected_option:
                await self._send_error(connection_id, "question_id and selected_option are required")
                return

            # Process answer using the assessment service with thread_id
            feedback_data = await assessment_graph_service.process_answer(
                connection_id, question_id, selected_option
            )

            if not feedback_data:
                await self._send_error(connection_id, "Failed to process answer")
                return

            # Send feedback
            await self._send_message(connection_id, {
                "type": WebSocketMessageType.ANSWER_FEEDBACK,
                "data": feedback_data
            })

            # Send progress update
            progress_data = await assessment_graph_service.get_assessment_progress(connection_id)
            if progress_data:
                await self._send_progress_update(connection_id, progress_data)

            # Check if assessment is complete
            if feedback_data["progress"]["percentage_complete"] >= 100:
                await self._finalize_assessment(connection_id, db)

        except Exception as e:
            logger.error(f"Error processing answer: {str(e)}", exc_info=True)
            await self._send_error(connection_id, f"Failed to process answer: {str(e)}")

    async def _handle_chat_message(self, connection_id: str, data: Dict, db: AsyncSession):
        """
        Handle general chat messages during assessment
        Provides contextual responses and guidance
        """
        try:
            user_message = data.get("message", "").strip()

            if not user_message:
                await self._send_error(connection_id, "Message cannot be empty")
                return

            # TODO: Implement AI chat functionality
            # This could use the same LLM to provide contextual help
            # without revealing answers to current questions

            # Placeholder response
            response_message = f"I understand you said: '{user_message}'. I'm here to guide you through the assessment. Would you like me to generate the next question?"

            await self._send_message(connection_id, {
                "type": WebSocketMessageType.SYSTEM_MESSAGE,
                "data": {
                    "message": response_message,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })

        except Exception as e:
            logger.error(f"Error handling chat message: {str(e)}")
            await self._send_error(connection_id, f"Failed to process message: {str(e)}")

    async def _handle_heartbeat(self, connection_id: str, data: Dict, db: AsyncSession):
        """Handle heartbeat/ping messages to keep connection alive"""
        await self._send_message(connection_id, {
            "type": WebSocketMessageType.PONG,
            "data": {"timestamp": datetime.utcnow().isoformat()}
        })

    async def _generate_next_question(self, connection_id: str, test_id: Optional[int], db: AsyncSession):
        """
        Generate the next question using assessment graph service with proper thread_id management
        """
        try:
            question_data = await assessment_graph_service.generate_question(connection_id)

            if question_data:
                await self._send_message(connection_id, {
                    "type": WebSocketMessageType.QUESTION,
                    "data": question_data
                })
            else:
                # Assessment complete or no more questions
                await self._finalize_assessment(connection_id, db)

        except Exception as e:
            logger.error(f"Error generating question: {str(e)}", exc_info=True)
            await self._send_error(connection_id, f"Failed to generate question: {str(e)}")

    async def _send_message(self, connection_id: str, message: Dict):
        """Send a message to a specific connection"""
        success = await connection_manager.send_personal_message(connection_id, message)
        if not success:
            logger.warning(f"Failed to send message to {connection_id}")

    async def _send_error(self, connection_id: str, error_message: str):
        """Send an error message to a connection"""
        await self._send_message(connection_id, {
            "type": WebSocketMessageType.ERROR,
            "data": {
                "error": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }
        })

    async def _send_progress_update(self, connection_id: str, progress_data: Dict):
        """Send progress update to connection"""
        await self._send_message(connection_id, {
            "type": WebSocketMessageType.PROGRESS_UPDATE,
            "data": {
                **progress_data,
                "timestamp": datetime.utcnow().isoformat()
            }
        })

    async def _finalize_assessment(self, connection_id: str, db: AsyncSession):
        """
        Finalize assessment and save results using proper thread_id management
        """
        try:
            # Get final results from assessment service
            final_results = await assessment_graph_service.finalize_assessment(connection_id, db)

            if final_results:
                # Send completion message with results
                await self._send_message(connection_id, {
                    "type": WebSocketMessageType.ASSESSMENT_COMPLETED,
                    "data": {
                        "message": "Assessment completed! Thank you for participating.",
                        "results": final_results,
                        "next_steps": "Your results will be reviewed and you'll be contacted if shortlisted."
                    }
                })

                # Clean up assessment session
                await connection_manager.end_assessment_session(connection_id)

                logger.info(f"Assessment finalized for {connection_id}")
            else:
                await self._send_error(connection_id, "Failed to finalize assessment")

        except Exception as e:
            logger.error(
                f"Error finalizing assessment: {str(e)}", exc_info=True)
            await self._send_error(connection_id, f"Failed to complete assessment: {str(e)}")


# Global handler instance
websocket_handler = AssessmentWebSocketHandler()
