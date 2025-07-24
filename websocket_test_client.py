"""
WebSocket Assessment Test Client
Demonstrates how to connect and interact with the assessment WebSocket system
"""

import asyncio
import json
import websockets
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AssessmentWebSocketClient:
    """Test client for WebSocket assessment system"""

    def __init__(self, base_url="ws://localhost:8000"):
        self.base_url = base_url
        self.websocket = None
        self.connected = False

    async def connect(self, token, test_id=None):
        """Connect to WebSocket assessment endpoint"""
        try:
            url = f"{self.base_url}/ws/assessment?token={token}"
            if test_id:
                url += f"&test_id={test_id}"

            logger.info(f"Connecting to {url}")
            self.websocket = await websockets.connect(url)
            self.connected = True
            logger.info("Connected successfully")

            # Listen for messages
            await self._listen_for_messages()

        except Exception as e:
            logger.error(f"Connection failed: {e}")

    async def _listen_for_messages(self):
        """Listen for incoming messages"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self._handle_message(data)

        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")
            self.connected = False
        except Exception as e:
            logger.error(f"Error listening for messages: {e}")

    async def _handle_message(self, data):
        """Handle incoming WebSocket messages"""
        message_type = data.get("type")
        message_data = data.get("data", {})

        logger.info(f"Received: {message_type}")

        if message_type == "auth_success":
            logger.info(f"Authenticated as user {message_data.get('user_id')}")

        elif message_type == "assessment_started":
            logger.info(f"Assessment started: {message_data.get('test_name')}")
            logger.info(
                f"Total questions: {message_data.get('total_questions')}")
            logger.info(
                f"Time limit: {message_data.get('time_limit_minutes')} minutes")

        elif message_type == "question":
            await self._handle_question(message_data)

        elif message_type == "answer_feedback":
            await self._handle_answer_feedback(message_data)

        elif message_type == "progress_update":
            await self._handle_progress_update(message_data)

        elif message_type == "assessment_completed":
            await self._handle_assessment_completed(message_data)

        elif message_type == "error":
            logger.error(f"Server error: {message_data.get('error')}")

        elif message_type == "system_message":
            logger.info(f"System: {message_data.get('message')}")

    async def _handle_question(self, data):
        """Handle incoming question"""
        logger.info("=" * 60)
        logger.info(
            f"Question {data.get('question_number')}/{data.get('total_questions')}")
        logger.info(f"Skill: {data.get('skill_being_tested')}")
        logger.info(f"Difficulty: {data.get('difficulty_level')}")
        logger.info("")
        logger.info(f"Q: {data.get('question_text')}")
        logger.info("")

        for option in data.get('options', []):
            logger.info(f"   {option}")

        logger.info("")
        logger.info(f"Time limit: {data.get('time_limit_seconds')} seconds")
        logger.info("=" * 60)

        # Simulate user thinking time
        await asyncio.sleep(2)

        # Auto-select option A for demo (in real implementation, user would choose)
        await self.submit_answer(data.get('question_id'), 'A')

    async def _handle_answer_feedback(self, data):
        """Handle answer feedback"""
        is_correct = data.get('is_correct')
        explanation = data.get('explanation')
        score_gained = data.get('score_gained')
        total_score = data.get('total_score')

        if is_correct:
            logger.info("✅ Correct!")
        else:
            logger.info("❌ Incorrect")
            logger.info(f"Correct answer: {data.get('correct_option')}")

        logger.info(f"Explanation: {explanation}")
        logger.info(f"Score gained: {score_gained}")
        logger.info(f"Total score: {total_score}")
        logger.info("")

        # Wait a bit before requesting next question
        await asyncio.sleep(1)
        await self.get_next_question()

    async def _handle_progress_update(self, data):
        """Handle progress update"""
        answered = data.get('questions_answered')
        total = data.get('total_questions')
        percentage = data.get('completion_percentage', 0)

        logger.info(
            f"Progress: {answered}/{total} questions ({percentage:.1f}%)")

    async def _handle_assessment_completed(self, data):
        """Handle assessment completion"""
        logger.info("")
        logger.info("🎉 ASSESSMENT COMPLETED! 🎉")
        logger.info("")

        results = data.get('results', {})
        logger.info(f"Final Score: {results.get('percentage_score')}%")
        logger.info(f"Questions Answered: {results.get('total_questions')}")
        logger.info(f"Time Taken: {results.get('time_taken_minutes')} minutes")
        logger.info("")
        logger.info(data.get('message'))

        # Close connection
        if self.websocket:
            await self.websocket.close()

    async def start_assessment(self, test_id):
        """Start assessment for given test ID"""
        if not self.connected:
            logger.error("Not connected")
            return

        message = {
            "type": "start_assessment",
            "data": {"test_id": test_id}
        }

        await self.websocket.send(json.dumps(message))
        logger.info(f"Requested to start assessment {test_id}")

    async def get_next_question(self):
        """Request next question"""
        if not self.connected:
            logger.error("Not connected")
            return

        message = {
            "type": "get_question",
            "data": {}
        }

        await self.websocket.send(json.dumps(message))

    async def submit_answer(self, question_id, selected_option):
        """Submit answer for current question"""
        if not self.connected:
            logger.error("Not connected")
            return

        message = {
            "type": "submit_answer",
            "data": {
                "question_id": question_id,
                "selected_option": selected_option
            }
        }

        await self.websocket.send(json.dumps(message))
        logger.info(f"Submitted answer: {selected_option}")

    async def send_chat_message(self, message_text):
        """Send chat message"""
        if not self.connected:
            logger.error("Not connected")
            return

        message = {
            "type": "chat_message",
            "data": {"message": message_text}
        }

        await self.websocket.send(json.dumps(message))

    async def send_heartbeat(self):
        """Send heartbeat to keep connection alive"""
        if not self.connected:
            return

        message = {
            "type": "heartbeat",
            "data": {}
        }

        await self.websocket.send(json.dumps(message))


# Example usage and test scenarios
async def test_assessment_flow():
    """Test complete assessment flow"""
    logger.info("Starting WebSocket Assessment Test")

    # You'll need to replace this with a real JWT token
    test_token = "your_jwt_token_here"
    test_id = 1  # Replace with actual test ID

    client = AssessmentWebSocketClient()

    try:
        # Connect with assessment
        await client.connect(test_token, test_id)

    except Exception as e:
        logger.error(f"Test failed: {e}")


async def test_chat_only():
    """Test chat-only connection"""
    logger.info("Starting WebSocket Chat Test")

    test_token = "your_jwt_token_here"

    client = AssessmentWebSocketClient()
    client.base_url = client.base_url.replace("/ws/assessment", "/ws/chat")

    try:
        await client.connect(test_token)

        # Send some chat messages
        await asyncio.sleep(1)
        await client.send_chat_message("Hello, can you help me?")

        await asyncio.sleep(2)
        await client.send_chat_message("What should I expect in this assessment?")

        # Keep connection alive for a bit
        for _ in range(5):
            await asyncio.sleep(10)
            await client.send_heartbeat()

    except Exception as e:
        logger.error(f"Chat test failed: {e}")


if __name__ == "__main__":
    """
    Run WebSocket tests

    Before running:
    1. Start the FastAPI server: uvicorn main:app --reload
    2. Get a valid JWT token by logging in
    3. Update test_token and test_id variables above
    4. Run: python websocket_test_client.py
    """

    print("WebSocket Assessment Test Client")
    print("================================")
    print()
    print("Choose test scenario:")
    print("1. Full Assessment Flow")
    print("2. Chat Only")
    print()

    choice = input("Enter choice (1-2): ").strip()

    if choice == "1":
        asyncio.run(test_assessment_flow())
    elif choice == "2":
        asyncio.run(test_chat_only())
    else:
        print("Invalid choice")
