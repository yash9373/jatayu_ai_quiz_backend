#!/usr/bin/env python3
"""
Test script to verify the assessment auto-recovery functionality
"""

from unittest.mock import Mock, AsyncMock
from fastapi import WebSocket
from app.websocket.connection_manager import WebSocketConnectionManager, ConnectionState
import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class MockDB:
    """Mock database session for testing"""
    pass


class MockAssessmentRepo:
    """Mock assessment repository for testing"""

    def __init__(self, mock_assessment=None):
        self.mock_assessment = mock_assessment

    async def get_user_assessment_for_test(self, user_id, test_id):
        if self.mock_assessment:
            return self.mock_assessment
        return None

    async def get_assessment_by_id(self, assessment_id):
        if self.mock_assessment and hasattr(self.mock_assessment, 'assessment_id'):
            if self.mock_assessment.assessment_id == assessment_id:
                return self.mock_assessment
        return None


class MockAssessment:
    """Mock assessment object"""

    def __init__(self, assessment_id, test_id, status='in_progress'):
        self.assessment_id = assessment_id
        self.test_id = test_id
        self.status = status


async def test_auto_recovery_on_reconnection():
    """Test that assessment state is auto-recovered on reconnection"""
    print("Testing assessment auto-recovery on reconnection...")

    # Create connection manager
    manager = WebSocketConnectionManager()

    # Mock WebSocket
    mock_websocket = Mock(spec=WebSocket)
    mock_websocket.accept = AsyncMock()

    # Mock database and assessment
    mock_db = MockDB()
    mock_assessment = MockAssessment(
        assessment_id=999, test_id=456, status='in_progress')

    # Patch the connection manager's method to use our mock
    original_check_existing = manager.check_existing_assessment
    original_recover_session = manager.recover_assessment_session

    async def mock_check_existing(user_id, test_id, db):
        if user_id == 123 and test_id == 456:
            return 999  # Return assessment_id
        return None

    async def mock_recover_session(connection_id, assessment_id, db):
        if assessment_id == 999:
            # Simulate recovery
            connection_state = manager.active_connections[connection_id]
            connection_state.start_assessment(456, 999)
            return True
        return False

    # Patch methods
    manager.check_existing_assessment = mock_check_existing
    manager.recover_assessment_session = mock_recover_session

    try:
        user_id = 123
        test_id = 456

        # Connect with auto-recovery
        connection_id = await manager.connect(mock_websocket, user_id, test_id, mock_db)
        expected_connection_id = f"{user_id}_{test_id}"

        print(f"Connection ID: {connection_id}")
        assert connection_id == expected_connection_id, f"Expected {expected_connection_id}, got {connection_id}"

        # Check if assessment was auto-recovered
        has_assessment = manager.has_active_assessment(connection_id)
        print(f"Has active assessment: {has_assessment}")
        assert has_assessment, "Assessment should be auto-recovered"

        # Check assessment status
        assessment_status = manager.get_assessment_status(connection_id)
        print(f"Assessment status: {assessment_status}")
        assert assessment_status is not None, "Assessment status should be available"
        assert assessment_status['assessment_id'] == 999, "Assessment ID should match"
        assert assessment_status['test_id'] == 456, "Test ID should match"
        assert assessment_status['is_in_assessment'] == True, "Should be in assessment"

        print("✓ Assessment auto-recovery works correctly")

        # Clean up
        await manager.disconnect(connection_id)

    finally:
        # Restore original methods
        manager.check_existing_assessment = original_check_existing
        manager.recover_assessment_session = original_recover_session


async def test_no_recovery_when_no_existing_assessment():
    """Test that no recovery happens when there's no existing assessment"""
    print("\nTesting no recovery when no existing assessment...")

    manager = WebSocketConnectionManager()

    mock_websocket = Mock(spec=WebSocket)
    mock_websocket.accept = AsyncMock()

    mock_db = MockDB()

    # Patch to return no existing assessment
    original_check_existing = manager.check_existing_assessment

    async def mock_check_existing(user_id, test_id, db):
        return None  # No existing assessment

    manager.check_existing_assessment = mock_check_existing

    try:
        user_id = 123
        test_id = 456

        # Connect without existing assessment
        connection_id = await manager.connect(mock_websocket, user_id, test_id, mock_db)

        # Check that no assessment was recovered
        has_assessment = manager.has_active_assessment(connection_id)
        print(f"Has active assessment: {has_assessment}")
        assert not has_assessment, "No assessment should be recovered"

        assessment_status = manager.get_assessment_status(connection_id)
        print(f"Assessment status: {assessment_status}")
        assert assessment_status is None, "Assessment status should be None"

        print("✓ No unwanted recovery when no existing assessment")

        # Clean up
        await manager.disconnect(connection_id)

    finally:
        # Restore original method
        manager.check_existing_assessment = original_check_existing


async def main():
    """Run all tests"""
    print("Starting assessment auto-recovery tests...\n")

    try:
        await test_auto_recovery_on_reconnection()
        await test_no_recovery_when_no_existing_assessment()

        print("\n🎉 All auto-recovery tests passed! Assessment state recovery is working correctly.")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
