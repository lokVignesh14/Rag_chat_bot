# API Key Usage Guide for KR Power Chatbot

## Overview
The KR Power Chatbot API now requires API keys for authentication. All endpoints (except API key management) require a valid API key.

## Generating an API Key

### Endpoint
```
POST /api/keys/generate
```

### Request Body
```json
{
  "name": "My Application",
  "description": "API key for KR Power integration"
}
```

### Response
```json
{
  "api_key": "your-generated-api-key-here",
  "key_id": "key-identifier",
  "name": "My Application",
  "created_at": "2024-01-01T00:00:00",
  "message": "⚠️ IMPORTANT: Save this API key now. You won't be able to see it again!"
}
```

**⚠️ IMPORTANT:** The API key is only shown once. Save it securely!

## Using API Keys

You can provide the API key in two ways:

### Method 1: Authorization Bearer Token (Recommended)
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about cable trays"}'
```

### Method 2: X-API-Key Header
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about cable trays"}'
```

## Python Example

```python
import requests

API_KEY = "your-api-key-here"
BASE_URL = "http://localhost:8000"

# Using Bearer token
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

response = requests.post(
    f"{BASE_URL}/chat",
    headers=headers,
    json={
        "message": "Tell me about cable trays",
        "session_id": "my-session"
    }
)

print(response.json())
```

## JavaScript/Node.js Example

```javascript
const API_KEY = "your-api-key-here";
const BASE_URL = "http://localhost:8000";

fetch(`${BASE_URL}/chat`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${API_KEY}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    message: "Tell me about cable trays",
    session_id: "my-session"
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

## Managing API Keys

### List All API Keys
```
GET /api/keys
```

### Revoke an API Key
```
POST /api/keys/{key_id}/revoke
```

### Reactivate a Revoked Key
```
POST /api/keys/{key_id}/reactivate
```

### Delete an API Key
```
DELETE /api/keys/{key_id}
```

## Protected Endpoints

The following endpoints require API key authentication:
- `POST /chat` - Main chat endpoint
- `POST /lead` - Lead form submission
- `POST /stt` - Speech-to-text
- `POST /tts` - Text-to-speech

## Error Responses

### Missing API Key
```json
{
  "detail": "API key required. Provide it via 'Authorization: Bearer <key>' header or 'X-API-Key' header."
}
```

### Invalid API Key
```json
{
  "detail": "Invalid or inactive API key."
}
```

