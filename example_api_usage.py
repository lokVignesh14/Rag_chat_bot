#!/usr/bin/env python3
"""
Example script showing how to use the KR Power Chatbot API with API keys.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"  # Change to your server URL

def generate_api_key(name="Example Key", description="Example API key"):
    """Generate a new API key."""
    url = f"{BASE_URL}/api/keys/generate"
    payload = {
        "name": name,
        "description": description
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API Key Generated Successfully!")
        print(f"Key ID: {data['key_id']}")
        print(f"API Key: {data['api_key']}")
        print(f"⚠️  IMPORTANT: Save this API key now. You won't be able to see it again!")
        return data['api_key']
    else:
        print(f"❌ Error generating API key: {response.text}")
        return None


def chat_with_api_key(api_key, message, session_id="example-session"):
    """Send a chat message using an API key."""
    url = f"{BASE_URL}/chat"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "message": message,
        "session_id": session_id
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"\n🤖 Bot Response:")
        print(f"Reply: {data.get('reply', 'No reply')}")
        if data.get('cards'):
            print(f"Products found: {len(data['cards'])}")
        return data
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None


def list_api_keys():
    """List all API keys."""
    url = f"{BASE_URL}/api/keys"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(f"\n📋 API Keys:")
        for key in data.get('keys', []):
            print(f"  - {key['name']} (ID: {key['key_id']})")
            print(f"    Created: {key['created_at']}")
            print(f"    Last Used: {key.get('last_used', 'Never')}")
            print(f"    Active: {key['is_active']}")
            print(f"    Usage Count: {key.get('usage_count', 0)}")
        return data
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("KR Power Chatbot API - Example Usage")
    print("=" * 60)
    
    # Step 1: Generate an API key (only needed once)
    print("\n1. Generating API Key...")
    api_key = generate_api_key(
        name="KR Power Integration",
        description="API key for KR Power chatbot integration"
    )
    
    if not api_key:
        print("Failed to generate API key. Exiting.")
        exit(1)
    
    # Step 2: Use the API key to chat
    print("\n2. Testing Chat Endpoint...")
    chat_with_api_key(api_key, "Tell me about cable trays")
    
    # Step 3: List all API keys
    print("\n3. Listing All API Keys...")
    list_api_keys()
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)

