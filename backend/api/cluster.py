"""
Cluster information API endpoints
"""
from fastapi import APIRouter, HTTPException
from backend.core.slurm_interface import get_partitions, get_cluster_info
from backend.core.ssh_manager import ssh_manager

router = APIRouter(prefix="/api/cluster", tags=["Cluster"])

@router.get("/partitions")
async def list_partitions():
    """
    Get available SLURM partitions from the connected cluster
    """
    if not ssh_manager.is_connected():
        raise HTTPException(status_code=401, detail="Not connected to cluster. Please login first.")

    success, partitions, error = get_partitions()

    if not success:
        raise HTTPException(status_code=500, detail=error)

    return {
        "partitions": partitions,
        "count": len(partitions)
    }

@router.get("/info")
async def cluster_info():
    """
    Get basic cluster information
    """
    if not ssh_manager.is_connected():
        raise HTTPException(status_code=401, detail="Not connected to cluster. Please login first.")

    info = get_cluster_info()

    if "error" in info:
        raise HTTPException(status_code=500, detail=info["error"])

    return info
