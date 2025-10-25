"""
Authentication API endpoints
"""
from fastapi import APIRouter, HTTPException
from backend.models.session import SSHLoginRequest, SSHLoginResponse
from backend.core.ssh_manager import ssh_manager
from backend.core.database import get_connection
from datetime import datetime

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=SSHLoginResponse)
async def login(request: SSHLoginRequest):
    """
    Authenticate and connect to remote HPC cluster via SSH
    """
    # Attempt SSH connection
    success, message = ssh_manager.connect(
        hostname=request.hostname,
        username=request.username,
        password=request.password
    )

    if not success:
        raise HTTPException(status_code=401, detail=message)

    # Store session in database
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sessions (hostname, username, last_active)
        VALUES (?, ?, ?)
    """, (request.hostname, request.username, datetime.now()))

    session_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return SSHLoginResponse(
        success=True,
        message=message,
        session_id=session_id
    )

@router.post("/logout")
async def logout():
    """Disconnect from SSH session"""
    ssh_manager.disconnect()
    return {"success": True, "message": "Disconnected"}

@router.get("/status")
async def status():
    """Check SSH connection status"""
    is_connected = ssh_manager.is_connected()

    return {
        "connected": is_connected,
        "hostname": ssh_manager.hostname if is_connected else None,
        "username": ssh_manager.username if is_connected else None
    }
