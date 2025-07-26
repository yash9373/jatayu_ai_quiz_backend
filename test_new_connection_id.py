#!/usr/bin/env python3
"""
Test script to verify the new connection_id approach using user_id + test_id format
"""

from unittest.mock import Mock, AsyncMock
from fastapi import WebSocket
from app.websocket.connection_manager import WebSocketConnectionManager, ConnectionState
import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_connection_id_format():
    """Test that connection_id uses the expected format"""
    print("Testing connection_id format...")

    # Create connection manager
    manager = WebSocketConnectionManager()

    # Mock WebSocket
    mock_websocket = Mock(spec=WebSocket)
    mock_websocket.accept = AsyncMock()

    # Test connection with test_id
    user_id = 123
    test_id = 456

    connection_id = await manager.connect(mock_websocket, user_id, test_id)
    expected_connection_id = f"{user_id}_{test_id}"

    print(f"Expected: {expected_connection_id}")
    print(f"Actual: {connection_id}")

    assert connection_id == expected_connection_id, f"Expected {expected_connection_id}, got {connection_id}"
    print("✓ Connection ID format is correct for test connection")

    # Test connection without test_id
    await manager.disconnect(connection_id)

    connection_id_general = await manager.connect(mock_websocket, user_id, None)
    expected_general_id = f"{user_id}_general"

    print(f"Expected general: {expected_general_id}")
    print(f"Actual general: {connection_id_general}")

    assert connection_id_general == expected_general_id, f"Expected {expected_general_id}, got {connection_id_general}"
    print("✓ Connection ID format is correct for general connection")

    # Clean up
    await manager.disconnect(connection_id_general)


async def test_reconnection_behavior():
    """Test that reconnection with same user_id and test_id uses same connection_id"""
    print("\nTesting reconnection behavior...")

    manager = WebSocketConnectionManager()

    # Mock WebSockets
    mock_websocket1 = Mock(spec=WebSocket)
    mock_websocket1.accept = AsyncMock()
    mock_websocket1.close = AsyncMock()

    mock_websocket2 = Mock(spec=WebSocket)
    mock_websocket2.accept = AsyncMock()

    user_id = 789
    test_id = 101

    # First connection
    connection_id1 = await manager.connect(mock_websocket1, user_id, test_id)
    print(f"First connection: {connection_id1}")

    # Second connection with same user_id and test_id should get same connection_id
    connection_id2 = await manager.connect(mock_websocket2, user_id, test_id)
    print(f"Second connection: {connection_id2}")

    assert connection_id1 == connection_id2, f"Connection IDs should be the same: {connection_id1} vs {connection_id2}"
    print("✓ Reconnection uses same connection_id")

    # Verify that the first websocket was closed
    mock_websocket1.close.assert_called_once()
    print("✓ Previous connection was properly closed")

    # Clean up
    await manager.disconnect(connection_id2)


async def test_multiple_tests_per_user():
    """Test that a user can have different connections for different tests"""
    print("\nTesting multiple tests per user...")

    manager = WebSocketConnectionManager()

    # Mock WebSockets
    mock_websocket1 = Mock(spec=WebSocket)
    mock_websocket1.accept = AsyncMock()

    mock_websocket2 = Mock(spec=WebSocket)
    mock_websocket2.accept = AsyncMock()

    user_id = 555
    test_id1 = 111
    test_id2 = 222

    # Connect to first test
    connection_id1 = await manager.connect(mock_websocket1, user_id, test_id1)
    expected_id1 = f"{user_id}_{test_id1}"

    print(f"Connection 1: {connection_id1} (expected: {expected_id1})")
    assert connection_id1 == expected_id1

    # Connect to second test (should replace the first connection in user_connections)
    connection_id2 = await manager.connect(mock_websocket2, user_id, test_id2)
    expected_id2 = f"{user_id}_{test_id2}"

    print(f"Connection 2: {connection_id2} (expected: {expected_id2})")
    assert connection_id2 == expected_id2

    # Both connections should have different IDs
    assert connection_id1 != connection_id2
    print("✓ Different tests generate different connection IDs")

    # Check that user_connections points to the latest connection
    latest_connection = manager.get_user_connection_id(user_id)
    assert latest_connection == connection_id2, f"User connection should point to latest: {latest_connection}"
    print("✓ User connection mapping points to latest connection")

    # Clean up
    await manager.disconnect(connection_id2)


async def main():
    """Run all tests"""
    print("Starting connection_id format tests...\n")

    try:
        await test_connection_id_format()
        await test_reconnection_behavior()
        await test_multiple_tests_per_user()

        print("\n🎉 All tests passed! The new connection_id approach is working correctly.")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
