# backend/api_keys.py
import os
import json
import secrets
import hashlib
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path

# Path to store API keys
API_KEYS_FILE = Path(__file__).parent / "data" / "api_keys.json"


def _ensure_api_keys_file():
    """Ensure the API keys file exists."""
    API_KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not API_KEYS_FILE.exists():
        with open(API_KEYS_FILE, "w") as f:
            json.dump({}, f)


def _load_api_keys() -> Dict:
    """Load API keys from file."""
    _ensure_api_keys_file()
    try:
        with open(API_KEYS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save_api_keys(keys: Dict):
    """Save API keys to file."""
    _ensure_api_keys_file()
    with open(API_KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=2)


def _hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key(name: str = "Default", description: str = "") -> Dict[str, str]:
    """
    Generate a new API key.
    
    Returns:
        Dict with 'api_key' (plain text) and 'key_id' (for management)
    """
    # Generate a secure random API key (32 bytes = 64 hex characters)
    api_key = secrets.token_urlsafe(32)
    key_id = secrets.token_urlsafe(16)
    key_hash = _hash_api_key(api_key)
    
    keys = _load_api_keys()
    keys[key_id] = {
        "key_hash": key_hash,
        "name": name,
        "description": description,
        "created_at": datetime.utcnow().isoformat(),
        "last_used": None,
        "is_active": True,
        "usage_count": 0
    }
    _save_api_keys(keys)
    
    return {
        "api_key": api_key,  # Only returned once - store it securely!
        "key_id": key_id,
        "name": name,
        "created_at": keys[key_id]["created_at"]
    }


def validate_api_key(api_key: str) -> Optional[Dict]:
    """
    Validate an API key and return its metadata if valid.
    
    Returns:
        Dict with key metadata if valid, None otherwise
    """
    if not api_key:
        return None
    
    key_hash = _hash_api_key(api_key)
    keys = _load_api_keys()
    
    for key_id, key_data in keys.items():
        if key_data.get("key_hash") == key_hash and key_data.get("is_active", True):
            # Update last used timestamp and usage count
            key_data["last_used"] = datetime.utcnow().isoformat()
            key_data["usage_count"] = key_data.get("usage_count", 0) + 1
            _save_api_keys(keys)
            return {
                "key_id": key_id,
                "name": key_data.get("name", "Unknown"),
                **key_data
            }
    
    return None


def list_api_keys() -> List[Dict]:
    """List all API keys (without exposing the actual keys)."""
    keys = _load_api_keys()
    result = []
    for key_id, key_data in keys.items():
        result.append({
            "key_id": key_id,
            "name": key_data.get("name", "Unknown"),
            "description": key_data.get("description", ""),
            "created_at": key_data.get("created_at"),
            "last_used": key_data.get("last_used"),
            "is_active": key_data.get("is_active", True),
            "usage_count": key_data.get("usage_count", 0)
        })
    return result


def revoke_api_key(key_id: str) -> bool:
    """Revoke (deactivate) an API key."""
    keys = _load_api_keys()
    if key_id in keys:
        keys[key_id]["is_active"] = False
        _save_api_keys(keys)
        return True
    return False


def delete_api_key(key_id: str) -> bool:
    """Permanently delete an API key."""
    keys = _load_api_keys()
    if key_id in keys:
        del keys[key_id]
        _save_api_keys(keys)
        return True
    return False


def reactivate_api_key(key_id: str) -> bool:
    """Reactivate a revoked API key."""
    keys = _load_api_keys()
    if key_id in keys:
        keys[key_id]["is_active"] = True
        _save_api_keys(keys)
        return True
    return False

