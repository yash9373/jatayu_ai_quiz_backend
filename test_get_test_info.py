#!/usr/bin/env python3
"""
Test script for the get_test_info WebSocket message functionality.
This script demonstrates how to use the get_test_info message to retrieve
comprehensive assessment state information for debugging and testing purposes.

Usage:
    python test_get_test_info.py
"""

import asyncio
import json
import websockets
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestInfoTester:
    """Test client for get_test_info WebSocket message functionality"""

    def __init__(self, base_url="ws://localhost:8000", test_id=1, token="your_jwt_token_here"):
        self.base_url = base_url
        self.test_id = test_id
        self.token = token
        self.websocket = None
        self.received_messages = []

    async def connect(self):
        """Connect to WebSocket with authentication"""
        url = f"{self.base_url}/ws/assessment/{self.test_id}?token={self.token}"
        logger.info(f"Connecting to: {url}")

        try:
            self.websocket = await websockets.connect(url)
            logger.info("WebSocket connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    async def send_message(self, message_type, data=None):
        """Send a message to the WebSocket"""
        if not self.websocket:
            logger.error("WebSocket not connected")
            return False

        message = {
            "type": message_type,
            "data": data or {}
        }

        try:
            await self.websocket.send(json.dumps(message))
            logger.info(f"Sent message: {message_type}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    async def receive_messages(self, timeout=5):
        """Receive and process messages for a specified timeout"""
        try:
            await asyncio.wait_for(self._message_loop(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.info("Message receiving timeout reached")

    async def _message_loop(self):
        """Internal message receiving loop"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                self.received_messages.append(data)

                message_type = data.get("type", "unknown")
                logger.info(f"Received message: {message_type}")

                if message_type == "auth_success":
                    await self._handle_auth_success(data)
                elif message_type == "assessment_started":
                    await self._handle_assessment_started(data)
                elif message_type == "test_info":
                    await self._handle_test_info(data)
                elif message_type == "error":
                    await self._handle_error(data)
                else:
                    logger.info(
                        f"Received {message_type}: {json.dumps(data, indent=2)}")

        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error in message loop: {e}")

    async def _handle_auth_success(self, data):
        """Handle authentication success"""
        logger.info("Authentication successful!")
        auth_data = data.get("data", {})

        # Check for recovered assessment
        if "recovered_assessment" in auth_data:
            logger.info("Assessment recovered from previous session")
            recovered = auth_data["recovered_assessment"]
            logger.info(
                f"Recovered assessment_id: {recovered.get('assessment_id')}")
            logger.info(f"Recovered test_id: {recovered.get('test_id')}")
            logger.info(f"Recovered thread_id: {recovered.get('thread_id')}")
        else:
            logger.info("New connection, no previous assessment to recover")

        # Start assessment
        await self.send_message("start_assessment", {"test_id": self.test_id})

    async def _handle_assessment_started(self, data):
        """Handle assessment started"""
        logger.info("Assessment started successfully!")
        assessment_data = data.get("data", {})
        logger.info(f"Assessment ID: {assessment_data.get('assessment_id')}")
        logger.info(f"Thread ID: {assessment_data.get('thread_id')}")

        # Now request test info
        await self.send_message("get_test_info")

    async def _handle_test_info(self, data):
        """Handle test info response and analyze the data"""
        logger.info("Received test_info response!")

        test_info = data.get("data", {}).get("test_info", {})

        # Analyze connection info
        connection_info = test_info.get("connection_info", {})
        logger.info("=== CONNECTION INFO ===")
        logger.info(f"Connection ID: {connection_info.get('connection_id')}")
        logger.info(f"User ID: {connection_info.get('user_id')}")
        logger.info(f"Thread ID: {connection_info.get('thread_id')}")
        logger.info(f"Assessment ID: {connection_info.get('assessment_id')}")
        logger.info(
            f"Authenticated: {connection_info.get('is_authenticated')}")
        logger.info(
            f"In Assessment: {connection_info.get('is_in_assessment')}")
        logger.info(
            f"Graph Initialized: {connection_info.get('graph_initialized')}")

        # Analyze test details
        test_details = test_info.get("test_details", {})
        logger.info("=== TEST DETAILS ===")
        logger.info(f"Test ID: {test_details.get('test_id')}")
        logger.info(f"Test Name: {test_details.get('test_name')}")
        logger.info(f"Description: {test_details.get('description')}")
        logger.info(
            f"Time Limit: {test_details.get('time_limit_minutes')} minutes")
        logger.info(f"Total Questions: {test_details.get('total_questions')}")
        logger.info(f"Difficulty: {test_details.get('difficulty_level')}")
        logger.info(f"Status: {test_details.get('status')}")

        # Analyze assessment details
        assessment_details = test_info.get("assessment_details", {})
        if assessment_details:
            logger.info("=== ASSESSMENT DETAILS ===")
            logger.info(
                f"Assessment ID: {assessment_details.get('assessment_id')}")
            logger.info(f"Status: {assessment_details.get('status')}")
            logger.info(f"Started At: {assessment_details.get('started_at')}")
            logger.info(
                f"Questions Answered: {assessment_details.get('total_questions_answered')}")
        else:
            logger.info("=== ASSESSMENT DETAILS ===")
            logger.info("No assessment details available")

        # Analyze graph state
        graph_state = test_info.get("graph_state", {})
        logger.info("=== GRAPH STATE ===")
        logger.info(f"Has State: {graph_state.get('has_state')}")
        logger.info(f"Thread ID: {graph_state.get('thread_id')}")
        logger.info(
            f"Generated Questions: {graph_state.get('generated_questions_count')}")
        logger.info(f"Responses Count: {graph_state.get('responses_count')}")

        # Show questions if any
        generated_questions = graph_state.get("generated_questions", {})
        if generated_questions:
            logger.info("=== GENERATED QUESTIONS ===")
            for q_id, question in generated_questions.items():
                logger.info(
                    f"Question {q_id}: {question.get('question_text', 'N/A')}")
                logger.info(f"  Skill: {question.get('skill', 'N/A')}")
                logger.info(
                    f"  Difficulty: {question.get('difficulty', 'N/A')}")
                logger.info(
                    f"  Correct Answer: {question.get('correct_answer', 'N/A')}")

        # Show responses if any
        responses = graph_state.get("responses", {})
        if responses:
            logger.info("=== USER RESPONSES ===")
            for r_id, response in responses.items():
                logger.info(
                    f"Response {r_id}: {response.get('selected_option', 'N/A')}")
                logger.info(f"  Timestamp: {response.get('timestamp', 'N/A')}")

    async def _handle_error(self, data):
        """Handle error messages"""
        error_data = data.get("data", {})
        error_msg = error_data.get("error", "Unknown error")
        logger.error(f"Received error: {error_msg}")

    async def close(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            logger.info("WebSocket connection closed")


async def test_scenario_1_new_assessment():
    """Test get_test_info with a new assessment"""
    logger.info("=== TEST SCENARIO 1: New Assessment ===")

    tester = TestInfoTester(test_id=1, token="test_token_123")

    try:
        # Connect and run test
        if await tester.connect():
            await tester.receive_messages(timeout=10)

        # Analyze results
        test_info_messages = [
            msg for msg in tester.received_messages if msg.get("type") == "test_info"]

        if test_info_messages:
            logger.info("✅ Successfully received test_info message")
            test_info = test_info_messages[0]

            # Validate structure
            required_sections = [
                "connection_info", "test_details", "assessment_details", "graph_state"]
            test_info_data = test_info.get("data", {}).get("test_info", {})

            for section in required_sections:
                if section in test_info_data:
                    logger.info(f"✅ {section} section present")
                else:
                    logger.error(f"❌ {section} section missing")
        else:
            logger.error("❌ No test_info message received")

    except Exception as e:
        logger.error(f"Test scenario 1 failed: {e}")
    finally:
        await tester.close()


async def test_scenario_2_invalid_connection():
    """Test get_test_info with invalid connection"""
    logger.info("=== TEST SCENARIO 2: Invalid Connection ===")

    # Use invalid token to test error handling
    tester = TestInfoTester(test_id=999, token="invalid_token")

    try:
        if await tester.connect():
            # Try to send get_test_info without proper authentication
            await tester.send_message("get_test_info")
            await tester.receive_messages(timeout=5)

        # Check for error messages
        error_messages = [
            msg for msg in tester.received_messages if msg.get("type") == "error"]

        if error_messages:
            logger.info(
                "✅ Received expected error message for invalid connection")
        else:
            logger.warning(
                "⚠️ No error message received for invalid connection")

    except Exception as e:
        logger.info(f"✅ Expected connection failure: {e}")
    finally:
        await tester.close()


async def main():
    """Run all test scenarios"""
    logger.info("Starting get_test_info WebSocket tests...")

    # Note: Update these test scenarios based on your actual setup
    logger.info("\n📝 Test Prerequisites:")
    logger.info("1. WebSocket server running on localhost:8000")
    logger.info("2. Valid test_id (default: 1)")
    logger.info("3. Valid JWT token for authentication")
    logger.info("4. Update token and test_id in script for your environment")

    # Run test scenarios
    await test_scenario_1_new_assessment()
    await asyncio.sleep(2)  # Brief pause between tests
    await test_scenario_2_invalid_connection()

    logger.info("\n🏁 Test completed!")
    logger.info("\nTo run with your environment:")
    logger.info("1. Update the token variable with a valid JWT")
    logger.info("2. Update test_id with a valid test ID from your database")
    logger.info("3. Ensure WebSocket server is running")

if __name__ == "__main__":
    # Example usage with custom parameters
    print("Get Test Info WebSocket Tester")
    print("==============================")
    print()
    print("This script tests the get_test_info WebSocket message functionality.")
    print("Update the token and test_id variables below for your environment.")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
