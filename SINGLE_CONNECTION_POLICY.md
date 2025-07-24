# Single Connection Policy Implementation

## Changes Made

The WebSocket connection manager has been modified to enforce a **single connection per candidate** policy. This ensures assessment integrity and prevents issues that could arise from multiple simultaneous sessions.

## Key Modifications

### 1. Data Structure Changes

**Before:**

```python
# Supported multiple connections per user
user_connections: Dict[int, Set[str]] = {}  # user_id -> {connection_ids}
```

**After:**

```python
# Single connection per user
user_connections: Dict[int, str] = {}  # user_id -> connection_id
```

### 2. Connection Establishment Logic

**New Behavior in `connect()` method:**

```python
# Check for existing connection and disconnect it
if user_id in self.user_connections:
    existing_connection_id = self.user_connections[user_id]
    logger.info(f"Disconnecting existing connection {existing_connection_id} for user {user_id}")
    await self.disconnect(existing_connection_id)

# Store single connection per user
self.user_connections[user_id] = connection_id
```

### 3. Cleanup Logic Updates

**Disconnect method** now handles single connection mapping:

```python
# Clean up user connection mapping (single connection per user)
if user_id in self.user_connections and self.user_connections[user_id] == connection_id:
    del self.user_connections[user_id]
```

### 4. Message Sending Simplification

**Before:**

```python
async def send_to_user(self, user_id: int, message: dict):
    connection_ids = list(self.user_connections[user_id])
    for connection_id in connection_ids:
        # Send to multiple connections...
```

**After:**

```python
async def send_to_user(self, user_id: int, message: dict):
    if user_id not in self.user_connections:
        return 0

    connection_id = self.user_connections[user_id]
    if await self.send_personal_message(connection_id, message):
        return 1
    return 0
```

### 5. New Utility Methods

Added helper methods for connection management:

```python
def has_active_connection(self, user_id: int) -> bool:
    """Check if a user has an active connection"""
    return user_id in self.user_connections

def get_user_connection_id(self, user_id: int) -> Optional[str]:
    """Get the connection ID for a user's active connection"""
    return self.user_connections.get(user_id)
```

## Behavioral Changes

### Connection Flow

1. **User connects for the first time** → Normal connection establishment
2. **User already has active connection** → Existing connection is automatically disconnected, new connection established
3. **User disconnects** → Connection removed from all tracking structures

### Scenarios Handled

#### Multiple Tab/Device Prevention

```
User Tab 1: Connected and taking assessment
User Tab 2: Attempts to connect
Result: Tab 1 connection automatically closed, Tab 2 becomes active
```

#### Network Recovery

```
User: Taking assessment, network drops
System: Connection marked as inactive, cleaned up after timeout
User: Reconnects with same credentials
Result: New connection established, assessment state recovered from database
```

#### Browser Refresh

```
User: Refreshes browser during assessment
Browser: Closes old WebSocket, opens new one
System: Establishes new connection (old one cleaned up automatically)
Result: Seamless continuation with state recovery
```

## Benefits

### 1. Assessment Integrity

- Prevents multiple simultaneous assessment sessions
- Eliminates potential for sharing or collaboration through multiple devices
- Ensures consistent assessment state

### 2. Resource Efficiency

- Reduced memory usage (single connection per user vs multiple)
- Simplified connection management
- Lower server resource consumption

### 3. Simplified Logic

- No need to handle message broadcasting to multiple user connections
- Cleaner state management
- Reduced complexity in user session tracking

### 4. Better User Experience

- Clear behavior: only one active session at a time
- Automatic handling of connection conflicts
- Seamless transition between devices/tabs

## Backward Compatibility

The changes maintain backward compatibility with existing client code:

- Same authentication flow
- Same message protocols
- Same reconnection logic
- Same assessment recovery mechanisms

The only difference is that multiple connections are no longer allowed - the system handles this transparently by disconnecting old connections.

## Monitoring and Debugging

The connection manager still provides the same monitoring capabilities:

- `get_active_connections_count()` - Total active connections
- `get_user_connections_count(user_id)` - Returns 0 or 1 (user has connection or not)
- `get_assessment_participants_count(test_id)` - Number of assessment participants
- `has_active_connection(user_id)` - New method to check user connection status

## Testing Considerations

When testing the system, consider these scenarios:

1. User opens multiple browser tabs - verify only one remains active
2. User switches devices during assessment - verify seamless transition
3. Network interruption and reconnection - verify state recovery
4. Concurrent connection attempts - verify proper handling
5. Assessment completion with multiple connection attempts - verify proper cleanup

This implementation ensures robust, secure, and efficient WebSocket connection management while maintaining assessment integrity.
