"""
Session and authentication models
"""
from pydantic import BaseModel
from typing import Optional

class SSHLoginRequest(BaseModel):
    """SSH login request model"""
    hostname: str
    username: str
    password: str

class SSHLoginResponse(BaseModel):
    """SSH login response model"""
    success: bool
    message: str
    session_id: Optional[int] = None
