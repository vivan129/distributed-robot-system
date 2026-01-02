# API Reference

Complete reference for SocketIO events and REST endpoints.

## Table of Contents

- [SocketIO Events](#socketio-events)
  - [PC Namespace (/pc)](#pc-namespace-pc)
  - [Pi Namespace (/pi)](#pi-namespace-pi)
- [Data Structures](#data-structures)
- [Error Handling](#error-handling)

## SocketIO Events

### PC Namespace (/pc)

Events for communication between PC dashboard and server.

#### Client to Server Events

##### `connect`
Client connects to server.

**Emitted by:** PC Dashboard

**Response:** `status` event with connection state

**Example:**
```javascript
socket.emit('connect', namespace='/pc');
```

##### `voice_data`
Send audio data for processing.

**Emitted by:** PC Dashboard

**Payload:**
```javascript
{
  audio: ArrayBuffer  // Raw audio data
}
```

**Example:**
```javascript
socket.emit('voice_data', {
  audio: audioBuffer
}, namespace='/pc');
```

##### `manual_command`
Send text command directly.

**Emitted by:** PC Dashboard

**Payload:**
```javascript
{
  text: string  // Text command
}
```

**Example:**
```javascript
socket.emit('manual_command', {
  text: "Move forward 3 seconds"
}, namespace='/pc');
```

##### `movement_command`
Send manual movement command.

**Emitted by:** PC Dashboard

**Payload:**
```javascript
{
  direction: string,  // "forward", "backward", "left", "right"
  duration: number    // Seconds (optional, default: 2.0)
}
```

**Example:**
```javascript
socket.emit('movement_command', {
  direction: 'forward',
  duration: 3.0
}, namespace='/pc');
```

##### `stop_command`
Emergency stop command.

**Emitted by:** PC Dashboard

**Payload:** Empty object `{}`

**Example:**
```javascript
socket.emit('stop_command', {}, namespace='/pc');
```

#### Server to Client Events

##### `status`
Connection status update.

**Emitted by:** Server

**Payload:**
```javascript
{
  connected: boolean,      // PC dashboard connected
  pi_connected: boolean    // Pi client connected
}
```

##### `bot_response`
AI response text.

**Emitted by:** Server

**Payload:**
```javascript
{
  text: string  // AI response
}
```

##### `pi_status`
Raspberry Pi connection status.

**Emitted by:** Server

**Payload:**
```javascript
{
  connected: boolean  // Pi connection state
}
```

##### `camera_view`
Camera frame from Pi.

**Emitted by:** Server

**Payload:**
```javascript
{
  frame: string  // Base64-encoded JPEG
}
```

##### `slam_map`
SLAM map visualization.

**Emitted by:** Server

**Payload:**
```javascript
{
  map: string  // Base64-encoded PNG
}
```

##### `ultrasonic_data`
Ultrasonic sensor distance.

**Emitted by:** Server

**Payload:**
```javascript
{
  distance: number  // Distance in cm
}
```

##### `obstacle_alert`
Obstacle detected warning.

**Emitted by:** Server

**Payload:**
```javascript
{
  distance: number  // Distance to obstacle in cm
}
```

##### `movement_status`
Movement command status.

**Emitted by:** Server

**Payload:**
```javascript
{
  status: string,  // "complete" or "stopped"
  data: object     // Additional data (optional)
}
```

---

### Pi Namespace (/pi)

Events for communication between Raspberry Pi client and server.

#### Client to Server Events

##### `connect`
Pi connects to server.

**Emitted by:** Raspberry Pi

**Response:** Server registers Pi connection

##### `pi_connected`
Pi reports ready status.

**Emitted by:** Raspberry Pi

**Payload:**
```python
{
    'status': 'ready'
}
```

##### `camera_frame`
Send camera frame to server.

**Emitted by:** Raspberry Pi

**Payload:**
```python
{
    'frame': str  # Base64-encoded JPEG
}
```

**Example:**
```python
import base64
import cv2

_, buffer = cv2.imencode('.jpg', frame)
frame_b64 = base64.b64encode(buffer).decode('utf-8')

socket.emit('camera_frame', {
    'frame': frame_b64
}, namespace='/pi')
```

##### `lidar_scan`
Send LiDAR scan data.

**Emitted by:** Raspberry Pi

**Payload:**
```python
{
    'ranges': List[float],  # Distances in meters
    'angles': List[float]   # Angles in degrees
}
```

##### `ultrasonic_data`
Send ultrasonic sensor reading.

**Emitted by:** Raspberry Pi

**Payload:**
```python
{
    'distance': float  # Distance in cm
}
```

##### `movement_complete`
Report movement completed.

**Emitted by:** Raspberry Pi

**Payload:**
```python
{
    'direction': str,  # Direction moved
    'duration': float  # Actual duration
}
```

##### `stop_complete`
Report stop completed.

**Emitted by:** Raspberry Pi

**Payload:** Empty dict `{}`

#### Server to Client Events

##### `movement`
Execute movement command.

**Emitted by:** Server

**Payload:**
```python
{
    'direction': str,  # "forward", "backward", "left", "right"
    'duration': float  # Seconds
}
```

**Expected Response:** `movement_complete` event

##### `stop`
Emergency stop.

**Emitted by:** Server

**Payload:** Empty dict `{}`

**Expected Response:** `stop_complete` event

##### `face_animation`
Display face animation.

**Emitted by:** Server

**Payload:**
```python
{
    'animation': dict,  # Animation keyframes
    'duration': float   # Total duration in seconds
}
```

**Animation Structure:**
```python
{
    'keyframes': [
        {
            'time': float,        # Time in seconds
            'mouth_shape': str,   # Phoneme/viseme
            'eye_state': str      # "open", "closed", "blink"
        }
    ]
}
```

##### `audio`
Play audio file.

**Emitted by:** Server

**Payload:**
```python
{
    'audio': str  # Base64-encoded audio (MP3)
}
```

---

## Data Structures

### Movement Command

```python
{
    'direction': str,  # Required: "forward"|"backward"|"left"|"right"|"stop"
    'duration': float  # Optional: seconds, default 2.0
}
```

### Camera Frame

```python
{
    'frame': str,      # Required: Base64-encoded JPEG
    'timestamp': float # Optional: Unix timestamp
}
```

### LiDAR Scan

```python
{
    'ranges': List[float],    # Required: distances in meters
    'angles': List[float],    # Required: angles in degrees
    'timestamp': float,       # Optional: Unix timestamp
    'quality': List[int]      # Optional: quality indicators
}
```

### Face Animation

```python
{
    'keyframes': [            # List of animation keyframes
        {
            'time': float,    # Time offset in seconds
            'mouth_shape': str,  # Phoneme: "A", "E", "I", "O", "U", etc.
            'mouth_width': float,    # 0.0 - 1.0
            'mouth_height': float,   # 0.0 - 1.0
            'eye_state': str,        # "open", "closed", "blink"
            'eye_width': float,      # 0.0 - 1.0
            'emotion': str           # Optional: "happy", "sad", etc.
        }
    ],
    'duration': float,        # Total animation duration
    'loop': bool              # Optional: loop animation
}
```

### AI Response

```python
{
    'text': str,              # AI response text
    'movement': Optional[dict],  # Movement command if extracted
    'timestamp': float        # Unix timestamp
}
```

---

## Error Handling

### Connection Errors

**Event:** `connect_error`

**Payload:**
```javascript
{
  message: string,
  code: string
}
```

**Common Codes:**
- `CONNECTION_REFUSED`: Server not running
- `TIMEOUT`: Connection timeout
- `AUTHENTICATION_FAILED`: Invalid credentials

### Runtime Errors

**Event:** `error`

**Payload:**
```javascript
{
  type: string,    // Error type
  message: string, // Error description
  data: object     // Additional context
}
```

**Error Types:**
- `HARDWARE_ERROR`: Hardware initialization/operation failed
- `PROCESSING_ERROR`: AI/vision processing failed
- `CONFIGURATION_ERROR`: Invalid configuration
- `TIMEOUT_ERROR`: Operation timeout

### Handling in Client

**JavaScript:**
```javascript
socket.on('error', (data) => {
  console.error(`Error: ${data.type} - ${data.message}`);
  // Handle error appropriately
});
```

**Python:**
```python
@sio.on('error', namespace='/pi')
def handle_error(data):
    logger.error(f"Error: {data['type']} - {data['message']}")
    # Handle error appropriately
```

---

## Rate Limiting

### Camera Frames
- **Max Rate:** 30 FPS
- **Recommended:** 10-15 FPS for stability

### LiDAR Scans
- **Max Rate:** 10 Hz
- **Recommended:** 5 Hz for normal operation

### Voice Commands
- **Cooldown:** 1 second between commands
- **Max Queue:** 5 commands

---

## Example Usage

### JavaScript Dashboard

```javascript
const socket = io('http://192.168.1.100:5000/pc');

// Connect
socket.on('connect', () => {
  console.log('Connected to server');
});

// Receive bot response
socket.on('bot_response', (data) => {
  displayMessage(data.text);
});

// Send voice command
function sendVoice(audioData) {
  socket.emit('voice_data', {
    audio: audioData
  });
}

// Manual movement
function moveForward() {
  socket.emit('movement_command', {
    direction: 'forward',
    duration: 2.0
  });
}

// Emergency stop
function emergencyStop() {
  socket.emit('stop_command', {});
}
```

### Python Raspberry Pi Client

```python
import socketio

sio = socketio.Client()

# Connect to server
@sio.event
def connect():
    print('Connected to server')
    sio.emit('pi_connected', {'status': 'ready'}, namespace='/pi')

# Handle movement
@sio.on('movement', namespace='/pi')
def handle_movement(data):
    direction = data['direction']
    duration = data['duration']
    
    # Execute movement
    motors.move(direction, duration)
    
    # Report completion
    sio.emit('movement_complete', {
        'direction': direction,
        'duration': duration
    }, namespace='/pi')

# Connect
sio.connect('http://192.168.1.100:5000', namespaces=['/pi'])
sio.wait()
```

---

**Last Updated:** January 2026