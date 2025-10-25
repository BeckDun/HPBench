"""
File Browser API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.core.ssh_manager import ssh_manager
from backend.core.file_browser import (
    list_directory,
    verify_file,
    find_hpl_binaries,
    get_parent_directory
)

router = APIRouter(prefix="/api/files", tags=["Files"])


class DirectoryListRequest(BaseModel):
    """Directory list request model"""
    path: str = "~"


class FileVerifyRequest(BaseModel):
    """File verification request model"""
    path: str


@router.post("/list")
async def list_dir(request: DirectoryListRequest):
    """
    List contents of a directory on the cluster
    """
    if not ssh_manager.is_connected():
        raise HTTPException(status_code=401, detail="Not connected to cluster. Please login first.")

    success, entries, actual_path_or_error = list_directory(request.path)

    if not success:
        raise HTTPException(status_code=400, detail=actual_path_or_error)

    # Sort: directories first, then files, alphabetically within each group
    directories = [e for e in entries if e["type"] == "directory"]
    files = [e for e in entries if e["type"] != "directory"]

    directories.sort(key=lambda x: x["name"].lower())
    files.sort(key=lambda x: x["name"].lower())

    sorted_entries = directories + files

    return {
        "success": True,
        "path": actual_path_or_error,  # This is the actual path after expansion
        "parent": get_parent_directory(actual_path_or_error),
        "entries": sorted_entries,
        "total": len(sorted_entries)
    }


@router.post("/verify")
async def verify(request: FileVerifyRequest):
    """
    Verify a file exists and get its details
    """
    if not ssh_manager.is_connected():
        raise HTTPException(status_code=401, detail="Not connected to cluster. Please login first.")

    success, file_info, error = verify_file(request.path)

    if not success:
        raise HTTPException(status_code=404, detail=error)

    return {
        "success": True,
        "file": file_info
    }


@router.get("/find-hpl")
async def find_hpl():
    """
    Search for HPL binaries (xhpl) in common locations
    """
    if not ssh_manager.is_connected():
        raise HTTPException(status_code=401, detail="Not connected to cluster. Please login first.")

    success, found_paths, error = find_hpl_binaries()

    if not success:
        raise HTTPException(status_code=500, detail=error)

    return {
        "success": True,
        "found_count": len(found_paths),
        "paths": found_paths
    }
