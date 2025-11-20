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
