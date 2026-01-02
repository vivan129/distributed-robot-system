# Google Gen AI SDK Study Guide

Comprehensive guide for using the new `google-genai` Python SDK in the robot project.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Key Concepts](#key-concepts)
- [Client Initialization](#client-initialization)
- [Content Generation](#content-generation)
- [Advanced Features](#advanced-features)
- [Function Calling](#function-calling)
- [Structured Output](#structured-output)
- [Streaming](#streaming)
- [Best Practices](#best-practices)
- [Migration from Old SDK](#migration-from-old-sdk)

---

## Overview

The new `google-genai` SDK provides a unified interface for:
- **Gemini Developer API** (using API key)
- **Vertex AI API** (using project/location)

### Key Features
- Type-safe API with Pydantic models
- Async support built-in
- Context managers for resource cleanup
- Function calling with automatic Python function support
- Structured output (JSON schemas, Pydantic models)
- Streaming responses
- Chat sessions
- File uploads (Developer API only)
- Caching and batch processing

---

## Installation

### Basic Installation

```bash
pip install google-genai
```

### With Optional Dependencies

```bash
# For faster async client
pip install google-genai[aiohttp]

# For SOCKS5 proxy support
pip install httpx[socks]
```

### Python Version Requirement

**Python 3.9+** is required.

---

## Key Concepts

### 1. Client vs Async Client

```python
from google import genai

# Sync client
client = genai.Client(api_key='YOUR_API_KEY')

# Async client
aclient = client.aio
```

### 2. Types Module

All configuration types are in `google.genai.types`:

```python
from google.genai import types

# Use typed configs instead of dicts
config = types.GenerateContentConfig(
    temperature=0.7,
    max_output_tokens=1024
)
```

### 3. Content Structure

**Contents** are converted to `list[types.Content]`:

```python
# Simple string (automatically converted)
contents = "Why is the sky blue?"

# Explicit Content
contents = types.Content(
    role='user',
    parts=[types.Part.from_text(text='Why is the sky blue?')]
)

# List of parts (grouped into single Content)
contents = [
    "What is this image?",
    types.Part.from_uri(
        file_uri='gs://path/to/image.jpg',
        mime_type='image/jpeg'
    )
]
```

### 4. Parts

**Parts** are building blocks of content:

```python
from google.genai import types

# Text part
part = types.Part.from_text(text="Hello")

# Image from URI
part = types.Part.from_uri(
    file_uri='gs://bucket/image.jpg',
    mime_type='image/jpeg'
)

# Image from bytes
with open('image.jpg', 'rb') as f:
    image_bytes = f.read()
part = types.Part.from_bytes(
    data=image_bytes,
    mime_type='image/jpeg'
)

# Function call
part = types.Part.from_function_call(
    name='get_weather',
    args={'location': 'Boston'}
)

# Function response
part = types.Part.from_function_response(
    name='get_weather',
    response={'result': 'sunny'}
)
```

---

## Client Initialization

### Gemini Developer API

```python
from google import genai

# Method 1: Explicit API key
client = genai.Client(api_key='YOUR_API_KEY')

# Method 2: Environment variable (GEMINI_API_KEY or GOOGLE_API_KEY)
client = genai.Client()
```

### Vertex AI API

```python
from google import genai

# Method 1: Explicit
client = genai.Client(
    vertexai=True,
    project='your-project-id',
    location='us-central1'
)

# Method 2: Environment variables
# GOOGLE_GENAI_USE_VERTEXAI=true
# GOOGLE_CLOUD_PROJECT=your-project-id
# GOOGLE_CLOUD_LOCATION=us-central1
client = genai.Client()
```

### Context Managers (Recommended)

```python
# Sync
with genai.Client(api_key='KEY') as client:
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents='Hello'
    )
    print(response.text)
# Client automatically closed

# Async
async with genai.Client().aio as aclient:
    response = await aclient.models.generate_content(
        model='gemini-2.0-flash',
        contents='Hello'
    )
    print(response.text)
# Async client automatically closed
```

### Configuration Options

```python
from google.genai import types

client = genai.Client(
    api_key='KEY',
    http_options=types.HttpOptions(
        api_version='v1',  # or 'v1alpha', 'beta' (default)
        base_url='https://custom-api.com',  # Custom endpoint
        headers={'Custom-Header': 'value'},
        client_args={'timeout': 30},  # httpx args
        async_client_args={'cookies': {...}},  # aiohttp args
    )
)
```

---

## Content Generation

### Basic Text Generation

```python
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Why is the sky blue?'
)

print(response.text)
```

### With Configuration

```python
from google.genai import types

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Write a story',
    config=types.GenerateContentConfig(
        temperature=0.9,
        top_p=0.95,
        top_k=40,
        max_output_tokens=2048,
        stop_sequences=['END'],
        presence_penalty=0.5,
        frequency_penalty=0.5,
    )
)
```

### System Instructions

```python
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='high',
    config=types.GenerateContentConfig(
        system_instruction='I say high, you say low',
        max_output_tokens=10,
    )
)
# Output: "low"
```

### Safety Settings

```python
from google.genai import types

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Say something controversial',
    config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category='HARM_CATEGORY_HATE_SPEECH',
                threshold='BLOCK_ONLY_HIGH'
            ),
            types.SafetySetting(
                category='HARM_CATEGORY_DANGEROUS_CONTENT',
                threshold='BLOCK_MEDIUM_AND_ABOVE'
            ),
        ]
    )
)
```

### Multimodal Input

```python
from google.genai import types

# Image from URI
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=[
        'What is in this image?',
        types.Part.from_uri(
            file_uri='gs://bucket/image.jpg',
            mime_type='image/jpeg'
        )
    ]
)

# Image from local file
with open('robot.jpg', 'rb') as f:
    image_data = f.read()

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=[
        'Describe this robot',
        types.Part.from_bytes(
            data=image_data,
            mime_type='image/jpeg'
        )
    ]
)
```

---

## Advanced Features

### 1. Chat Sessions

```python
# Create chat
chat = client.chats.create(
    model='gemini-2.0-flash',
    config=types.GenerateContentConfig(
        system_instruction='You are a helpful robot assistant',
        temperature=0.7,
    )
)

# Send messages
response1 = chat.send_message('Tell me a story')
print(response1.text)

response2 = chat.send_message('Summarize it in one sentence')
print(response2.text)

# Chat maintains history automatically
```

### 2. Token Counting

```python
# Count tokens before sending
token_response = client.models.count_tokens(
    model='gemini-2.0-flash',
    contents='Why is the sky blue?'
)

print(f"Total tokens: {token_response.total_tokens}")
print(f"Prompt tokens: {token_response.prompt_tokens}")
```

### 3. Caching (Context Caching)

```python
from google.genai import types

# Create cached content
cached_content = client.caches.create(
    model='gemini-2.0-flash',
    config=types.CreateCachedContentConfig(
        contents=[
            types.Content(
                role='user',
                parts=[
                    types.Part.from_uri(
                        file_uri='gs://bucket/large-doc.pdf',
                        mime_type='application/pdf'
                    )
                ]
            )
        ],
        system_instruction='Summarize this document',
        ttl='3600s',  # Cache for 1 hour
    )
)

# Use cached content
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='What are the key points?',
    config=types.GenerateContentConfig(
        cached_content=cached_content.name
    )
)
```

### 4. Batch Prediction

```python
from google.genai import types
import time

# Create batch job
job = client.batches.create(
    model='gemini-2.0-flash',
    src=[{
        "contents": [{"parts": [{"text": "Hello!"}], "role": "user"}],
        "config": {"response_modalities": ["text"]}
    }]
)

# Poll until complete
completed_states = {'JOB_STATE_SUCCEEDED', 'JOB_STATE_FAILED', 'JOB_STATE_CANCELLED'}

while job.state not in completed_states:
    print(f"Job state: {job.state}")
    time.sleep(10)
    job = client.batches.get(name=job.name)

print(f"Final state: {job.state}")
```

---

## Function Calling

### Automatic Python Function Support

The SDK automatically converts Python functions to tool declarations:

```python
from google.genai import types

def get_current_weather(location: str) -> str:
    """Returns the current weather.
    
    Args:
        location: The city and state, e.g. San Francisco, CA
    """
    return 'sunny'

def get_robot_status() -> dict:
    """Get current robot status.
    
    Returns:
        Dictionary with battery level and location
    """
    return {'battery': 85, 'location': 'kitchen'}

# Automatically calls functions and responds
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='What is the weather in Boston? Also check robot status.',
    config=types.GenerateContentConfig(
        tools=[get_current_weather, get_robot_status],
    )
)

print(response.text)  # Uses function results in response
```

### Disable Automatic Function Calling

```python
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='What is the weather in Boston?',
    config=types.GenerateContentConfig(
        tools=[get_current_weather],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=True
        )
    )
)

# Get function calls from response
for function_call in response.function_calls:
    print(f"Function: {function_call.name}")
    print(f"Args: {function_call.args}")
```

### Manual Function Declaration

```python
from google.genai import types

# Define function schema
function = types.FunctionDeclaration(
    name='move_robot',
    description='Move the robot in a direction',
    parameters_json_schema={
        'type': 'object',
        'properties': {
            'direction': {
                'type': 'string',
                'enum': ['forward', 'backward', 'left', 'right'],
                'description': 'Direction to move'
            },
            'duration': {
                'type': 'number',
                'description': 'Duration in seconds'
            }
        },
        'required': ['direction']
    }
)

tool = types.Tool(function_declarations=[function])

# Get function call
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Move forward for 3 seconds',
    config=types.GenerateContentConfig(
        tools=[tool],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=True
        )
    )
)

# Extract and execute
if response.function_calls:
    fc = response.function_calls[0]
    print(f"Direction: {fc.args['direction']}")
    print(f"Duration: {fc.args.get('duration', 2.0)}")
```

### Force Function Calling (ANY mode)

```python
from google.genai import types

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Hello',
    config=types.GenerateContentConfig(
        tools=[get_current_weather],
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode='ANY'  # Model MUST call a function
            )
        )
    )
)
```

---

## Structured Output

### JSON Schema

```python
user_schema = {
    'type': 'object',
    'properties': {
        'username': {'type': 'string'},
        'age': {'type': 'integer', 'minimum': 0},
        'email': {'type': 'string'}
    },
    'required': ['username', 'age']
}

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Generate a random user profile',
    config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_json_schema=user_schema
    )
)

print(response.text)  # JSON string
print(response.parsed)  # Parsed dict
```

### Pydantic Models

```python
from pydantic import BaseModel
from google.genai import types

class RobotCommand(BaseModel):
    action: str
    direction: str
    duration: float
    priority: int = 1

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Move forward for 3 seconds urgently',
    config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=RobotCommand
    )
)

command = RobotCommand.parse_raw(response.text)
print(f"Action: {command.action}")
print(f"Direction: {command.direction}")
print(f"Duration: {command.duration}")
print(f"Priority: {command.priority}")
```

### Enum Responses

```python
from enum import Enum

class Direction(Enum):
    FORWARD = 'forward'
    BACKWARD = 'backward'
    LEFT = 'left'
    RIGHT = 'right'
    STOP = 'stop'

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Which way should I go to reach the kitchen?',
    config=types.GenerateContentConfig(
        response_mime_type='text/x.enum',
        response_schema=Direction
    )
)

print(response.text)  # "left"
```

---

## Streaming

### Sync Streaming

```python
for chunk in client.models.generate_content_stream(
    model='gemini-2.0-flash',
    contents='Tell me a long story'
):
    print(chunk.text, end='', flush=True)
```

### Async Streaming

```python
async for chunk in await client.aio.models.generate_content_stream(
    model='gemini-2.0-flash',
    contents='Tell me a long story'
):
    print(chunk.text, end='', flush=True)
```

### Streaming with Chat

```python
chat = client.chats.create(model='gemini-2.0-flash')

for chunk in chat.send_message_stream('Tell me a story'):
    print(chunk.text, end='', flush=True)
```

---

## Best Practices

### 1. Use Context Managers

```python
# Good
with genai.Client(api_key='KEY') as client:
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents='Hello'
    )

# Avoid
client = genai.Client(api_key='KEY')
response = client.models.generate_content(...)
# Must manually call client.close()
```

### 2. Use Typed Configs

```python
from google.genai import types

# Good - Type-safe
config = types.GenerateContentConfig(
    temperature=0.7,
    max_output_tokens=1024
)

# Avoid - No type checking
config = {
    'temperature': 0.7,
    'max_output_tokens': 1024
}
```

### 3. Error Handling

```python
from google.genai import errors

try:
    response = client.models.generate_content(
        model='invalid-model',
        contents='Hello'
    )
except errors.APIError as e:
    print(f"API Error {e.code}: {e.message}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### 4. Token Management

```python
# Count tokens before sending
token_count = client.models.count_tokens(
    model='gemini-2.0-flash',
    contents=large_prompt
)

if token_count.total_tokens > 30000:
    print("Prompt too long, need to split or summarize")
else:
    response = client.models.generate_content(...)
```

### 5. Async for Performance

```python
import asyncio

async def process_multiple_requests():
    async with genai.Client().aio as aclient:
        tasks = [
            aclient.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt
            )
            for prompt in prompts
        ]
        responses = await asyncio.gather(*tasks)
        return responses

# Process many requests concurrently
responses = asyncio.run(process_multiple_requests())
```

### 6. Use Caching for Repeated Context

```python
# Cache large context (e.g., documentation, long PDFs)
cached = client.caches.create(
    model='gemini-2.0-flash',
    config=types.CreateCachedContentConfig(
        contents=[large_document],
        ttl='3600s'
    )
)

# Use cached context for multiple queries
for query in queries:
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=query,
        config=types.GenerateContentConfig(
            cached_content=cached.name
        )
    )
```

---

## Migration from Old SDK

### Old SDK (google-generativeai)

```python
import google.generativeai as genai

genai.configure(api_key='KEY')
model = genai.GenerativeModel('gemini-2.0-flash')

response = model.generate_content('Hello')
print(response.text)
```

### New SDK (google-genai)

```python
from google import genai

client = genai.Client(api_key='KEY')

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Hello'
)
print(response.text)
```

### Chat Migration

**Old SDK:**
```python
model = genai.GenerativeModel('gemini-2.0-flash')
chat = model.start_chat(history=[])

response = chat.send_message('Hello')
```

**New SDK:**
```python
chat = client.chats.create(model='gemini-2.0-flash')

response = chat.send_message('Hello')
```

### Function Calling Migration

**Old SDK:**
```python
model = genai.GenerativeModel(
    model_name='gemini-2.0-flash',
    tools=[function_declaration]
)
```

**New SDK:**
```python
# Just pass the Python function!
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='...',
    config=types.GenerateContentConfig(
        tools=[python_function]  # Automatic conversion
    )
)
```

---

## Robot-Specific Examples

### 1. Command Extraction with Structured Output

```python
from pydantic import BaseModel
from typing import Optional
from google.genai import types

class RobotCommand(BaseModel):
    intent: str  # "move", "speak", "scan", "none"
    direction: Optional[str] = None
    duration: float = 2.0
    speech_text: Optional[str] = None

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Move forward for 3 seconds and say hello',
    config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=RobotCommand
    )
)

cmd = RobotCommand.parse_raw(response.text)
```

### 2. Vision + Control

```python
import base64
from google.genai import types

# Capture from robot camera
with open('camera_frame.jpg', 'rb') as f:
    frame_bytes = f.read()

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=[
        'What do you see? Should I move forward?',
        types.Part.from_bytes(
            data=frame_bytes,
            mime_type='image/jpeg'
        )
    ]
)

print(response.text)
```

### 3. Conversation with Memory

```python
chat = client.chats.create(
    model='gemini-2.0-flash',
    config=types.GenerateContentConfig(
        system_instruction='''
        You are a helpful robot assistant.
        You can move (forward, backward, left, right).
        You have a camera and can see.
        Keep responses brief and friendly.
        ''',
        temperature=0.7,
    )
)

while True:
    user_input = input("You: ")
    if user_input.lower() == 'exit':
        break
    
    response = chat.send_message(user_input)
    print(f"Robot: {response.text}")
```

---

**Last Updated:** January 2026
**SDK Version:** google-genai 1.x