"""
Jobs API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from backend.core.slurm_interface import submit_test_job
from backend.core.ssh_manager import ssh_manager
from backend.models.hpl_params import ParameterSweepRequest, HPLConfiguration
from backend.core.parameter_generator import (
    generate_parameter_sweep,
    get_recommended_nb_values,
    calculate_recommended_pq
)

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

class TestJobRequest(BaseModel):
    """Test job request model"""
    nodes: int
    cpus_per_node: int
    partition: str

@router.post("/test")
async def test_slurm(request: TestJobRequest):
    """
    Submit a test SLURM job that runs hostname to verify configuration
    """
    if not ssh_manager.is_connected():
        raise HTTPException(status_code=401, detail="Not connected to cluster. Please login first.")

    result = submit_test_job(
        nodes=request.nodes,
        cpus_per_node=request.cpus_per_node,
        partition=request.partition
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Test job failed"))

    return result

@router.post("/parameters/generate")
async def generate_parameters(request: ParameterSweepRequest):
    """
    Generate HPL parameter sweep combinations based on range
    """
    configurations = generate_parameter_sweep(
        param_range=request.parameter_range,
        max_combinations=request.max_combinations or 100
    )

    return {
        "total_configurations": len(configurations),
        "configurations": configurations
    }

@router.get("/parameters/recommended-nb")
async def get_nb_recommendations():
    """
    Get recommended NB (block size) values
    """
    return {
        "nb_values": get_recommended_nb_values(),
        "description": "Commonly used block sizes for HPL"
    }

@router.get("/parameters/recommended-pq/{total_processes}")
async def get_pq_recommendations(total_processes: int):
    """
    Get recommended P and Q values for given total processes
    """
    pq_pairs = calculate_recommended_pq(total_processes)

    return {
        "total_processes": total_processes,
        "pq_pairs": pq_pairs,
        "description": "Recommended P x Q process grid configurations (Q >= P preferred)"
    }
