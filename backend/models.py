from typing import List, Dict, Optional

from pydantic import BaseModel, Field, EmailStr

class ChatIn(BaseModel):
    text: str

class LeadIn(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    message: Optional[str] = ""
    history: Optional[List[Dict[str, str]]] = None

class ApiKeyCreate(BaseModel):
    name: Optional[str] = "Default"
    description: Optional[str] = ""

class ApiKeyResponse(BaseModel):
    api_key: str
    key_id: str
    name: str
    created_at: str
    message: str = "⚠️ IMPORTANT: Save this API key now. You won't be able to see it again!"

class ApiKeyListResponse(BaseModel):
    keys: List[Dict]