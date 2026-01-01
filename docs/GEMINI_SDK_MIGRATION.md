# Gemini SDK Migration Guide

## Overview

Google has deprecated the `google-generativeai` package (End-of-Life: November 30, 2025) and replaced it with the new **`google-genai`** SDK.

This project has been updated to use the new SDK. This guide explains what changed and how to upgrade.

## What Changed

### Package Name
- **Old**: `google-generativeai==0.3.2`
- **New**: `google-genai>=0.2.0`

### Import Statements
```python
# OLD (Deprecated)
import google.generativeai as genai

# NEW (Current)
from google import genai
from google.genai import types
```

### Client Initialization

#### Old SDK
```python
import google.generativeai as genai

# Configure
genai.configure(api_key='YOUR_API_KEY')

# Create model
model = genai.GenerativeModel(
    model_name='gemini-2.0-flash-exp',
    generation_config={
        "temperature": 0.7,
        "max_output_tokens": 1024,
    }
)

# Start chat
chat = model.start_chat(history=[])
response = chat.send_message("Hello!")
print(response.text)
```

#### New SDK
```python
from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key='YOUR_API_KEY')

# Generate content
response = client.models.generate_content(
    model='gemini-2.0-flash-exp',
    contents='Hello!',
    config=types.GenerateContentConfig(
        temperature=0.7,
        max_output_tokens=1024,
    )
)

print(response.text)
```

## Migration Steps for This Project

### 1. Update Dependencies

```bash
cd pc_server

# Remove old package
pip uninstall google-generativeai

# Install new package
pip install google-genai

# Or reinstall all requirements
pip install -r requirements.txt
```

### 2. No Code Changes Needed!

The `pc_server/modules/ai_brain.py` has already been updated to use the new SDK. The changes are internal - the public API remains the same.

### 3. Verify Installation

```bash
python3 -c "from google import genai; print('New SDK installed successfully!')"
```

### 4. Test the AI Brain

```bash
cd pc_server/modules
python3 ai_brain.py
```

## Key Differences

### Chat History Management

**Old SDK**: Built-in chat history with `start_chat()`
```python
chat = model.start_chat(history=[])
chat.send_message("Hello")
# History managed automatically
```

**New SDK**: Manual history management
```python
# We maintain history in self.chat_history
self.chat_history.append({'role': 'user', 'content': user_input})
self.chat_history.append({'role': 'assistant', 'content': response_text})
```

### Configuration

**Old SDK**: Dictionary-based config
```python
generation_config={"temperature": 0.7}
```

**New SDK**: Typed configuration objects
```python
config=types.GenerateContentConfig(temperature=0.7)
```

## New Features in google-genai

### 1. Function Calling
```python
def get_weather(location: str) -> str:
    """Get current weather."""
    return 'sunny'

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='What is the weather in Boston?',
    config=types.GenerateContentConfig(tools=[get_weather]),
)
```

### 2. Structured Output
```python
from pydantic import BaseModel

class Recipe(BaseModel):
    name: str
    ingredients: list[str]
    steps: list[str]

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Give me a recipe for chocolate chip cookies',
    config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=Recipe,
    ),
)
```

### 3. Multimodal Inputs
```python
from google.genai import types

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=[
        types.Part.from_text('What is in this image?'),
        types.Part.from_uri(
            file_uri='gs://your-bucket/image.jpg',
            mime_type='image/jpeg'
        )
    ]
)
```

### 4. Grounding with Google Search
```python
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='What are the latest developments in AI?',
    config=types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())]
    ),
)
```

## API Version Selection

The new SDK defaults to beta endpoints. You can select stable v1:

```python
client = genai.Client(
    api_key='YOUR_API_KEY',
    http_options=types.HttpOptions(api_version='v1')
)
```

## Troubleshooting

### Import Error
```
ImportError: cannot import name 'genai' from 'google'
```

**Solution**: Ensure you installed `google-genai`, not `google-generativeai`
```bash
pip uninstall google-generativeai
pip install google-genai
```

### API Key Not Working
```
AuthenticationError: Invalid API key
```

**Solution**: Verify your API key in `.env`
```bash
cat .env | grep GEMINI_API_KEY
```

Get a new key at: https://ai.google.dev/

### Model Not Found
```
ResourceNotFoundError: Model not found
```

**Solution**: Update model name in `config/robot_config.yaml`
```yaml
ai:
  model: "gemini-2.0-flash-exp"  # or "gemini-1.5-flash"
```

Available models:
- `gemini-2.0-flash-exp` (recommended)
- `gemini-1.5-flash`
- `gemini-1.5-pro`
- `gemini-2.0-flash-thinking-exp`

## Resources

- **New SDK Documentation**: https://googleapis.github.io/python-genai/
- **Migration Guide**: https://ai.google.dev/gemini-api/docs/migrate-to-genai
- **GitHub Repository**: https://github.com/googleapis/python-genai
- **API Reference**: https://ai.google.dev/api

## Timeline

| Date | Event |
|------|-------|
| **May 2025** | google-genai reaches General Availability (GA) |
| **November 30, 2025** | google-generativeai End-of-Life |
| **May 2026** | Vertex AI GenerativeModel module deprecated |

## Questions?

If you encounter any issues with the migration:
1. Check the [troubleshooting section](#troubleshooting) above
2. Open an issue on GitHub: https://github.com/vivan129/distributed-robot-system/issues
3. Consult the official docs: https://googleapis.github.io/python-genai/

---

**Migration Status**: ✅ Complete

**Last Updated**: January 1, 2026