"""
Jobs API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from backend.core.slurm_interface import (
    submit_test_job,
    submit_hpl_sweep,
    get_multiple_job_statuses
)
from backend.core.ssh_manager import ssh_manager
from backend.core.database import get_connection
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

class SweepSubmissionRequest(BaseModel):
    """Sweep submission request model"""
    configurations: List[HPLConfiguration]
    nodes: int
    cpus_per_node: int
    partition: str
    sweep_name: Optional[str] = None
    xhpl_path: str = "xhpl"
    time_limit: str = "01:00:00"

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

@router.post("/sweep/submit")
async def submit_sweep(request: SweepSubmissionRequest):
    """
    Submit HPL parameter sweep to cluster
    """
    if not ssh_manager.is_connected():
        raise HTTPException(status_code=401, detail="Not connected to cluster. Please login first.")

    # Get current session (for simplicity, using session_id=1 or create logic to track current session)
    conn = get_connection()
    cursor = conn.cursor()

    # Get or create session
    cursor.execute("SELECT id FROM sessions WHERE is_active = 1 ORDER BY last_active DESC LIMIT 1")
    session_row = cursor.fetchone()

    if not session_row:
        raise HTTPException(status_code=500, detail="No active session found")

    session_id = session_row[0]

    # Create sweep record
    sweep_name = request.sweep_name or f"Sweep_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    cursor.execute("""
        INSERT INTO sweeps (session_id, name, total_jobs, nodes, cpus_per_node, partition)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, sweep_name, len(request.configurations), request.nodes, request.cpus_per_node, request.partition))

    sweep_id = cursor.lastrowid
    conn.commit()

    # Submit jobs to SLURM
    result = submit_hpl_sweep(
        configurations=request.configurations,
        nodes=request.nodes,
        cpus_per_node=request.cpus_per_node,
        partition=request.partition,
        sweep_id=sweep_id,
        xhpl_path=request.xhpl_path,
        time_limit=request.time_limit
    )

    if not result.get("success"):
        conn.close()
        raise HTTPException(status_code=500, detail=result.get("error", "Sweep submission failed"))

    # Store configurations and job IDs in database
    for job_info in result["submitted_jobs"]:
        config = request.configurations[job_info["config_id"] - 1]
        cursor.execute("""
            INSERT INTO hpl_configurations
            (sweep_id, slurm_job_id, n, nb, p, q, pfact, nbmin, rfact, bcast, depth, swap, l1, u, equil, align, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'SUBMITTED')
        """, (
            sweep_id,
            job_info["slurm_job_id"],
            config.n, config.nb, config.p, config.q,
            config.pfact, config.nbmin, config.rfact, config.bcast,
            config.depth, config.swap, config.l1, config.u, config.equil, config.align
        ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "sweep_id": sweep_id,
        "sweep_name": sweep_name,
        "submitted_count": result["submitted_count"],
        "failed_count": result["failed_count"],
        "submitted_jobs": result["submitted_jobs"],
        "failed_jobs": result["failed_jobs"]
    }

@router.get("/sweeps")
async def list_sweeps():
    """
    Get list of all parameter sweeps
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, total_jobs, completed_jobs, nodes, cpus_per_node, partition, created_at
        FROM sweeps
        ORDER BY created_at DESC
    """)

    sweeps = []
    for row in cursor.fetchall():
        sweeps.append({
            "id": row[0],
            "name": row[1],
            "total_jobs": row[2],
            "completed_jobs": row[3],
            "nodes": row[4],
            "cpus_per_node": row[5],
            "partition": row[6],
            "created_at": row[7]
        })

    conn.close()

    return {
        "sweeps": sweeps,
        "count": len(sweeps)
    }

@router.get("/sweep/{sweep_id}/status")
async def get_sweep_status(sweep_id: int):
    """
    Get detailed status of a parameter sweep with all jobs
    """
    if not ssh_manager.is_connected():
        raise HTTPException(status_code=401, detail="Not connected to cluster. Please login first.")

    conn = get_connection()
    cursor = conn.cursor()

    # Get sweep info
    cursor.execute("""
        SELECT id, name, total_jobs, completed_jobs, nodes, cpus_per_node, partition, created_at
        FROM sweeps
        WHERE id = ?
    """, (sweep_id,))

    sweep_row = cursor.fetchone()
    if not sweep_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Sweep not found")

    sweep_info = {
        "id": sweep_row[0],
        "name": sweep_row[1],
        "total_jobs": sweep_row[2],
        "completed_jobs": sweep_row[3],
        "nodes": sweep_row[4],
        "cpus_per_node": sweep_row[5],
        "partition": sweep_row[6],
        "created_at": sweep_row[7]
    }

    # Get all configurations/jobs for this sweep
    cursor.execute("""
        SELECT id, slurm_job_id, n, nb, p, q, status, submitted_at, completed_at
        FROM hpl_configurations
        WHERE sweep_id = ?
        ORDER BY id
    """, (sweep_id,))

    jobs = []
    slurm_job_ids = []

    for row in cursor.fetchall():
        job = {
            "config_id": row[0],
            "slurm_job_id": row[1],
            "n": row[2],
            "nb": row[3],
            "p": row[4],
            "q": row[5],
            "status": row[6],
            "submitted_at": row[7],
            "completed_at": row[8]
        }
        jobs.append(job)
        if row[1]:  # If has SLURM job ID
            slurm_job_ids.append(row[1])

    # Query current status from SLURM
    status_result = get_multiple_job_statuses(slurm_job_ids)

    if status_result.get("success"):
        job_statuses = status_result.get("job_statuses", {})

        # Update jobs with current SLURM status
        for job in jobs:
            slurm_job_id = job["slurm_job_id"]
            if slurm_job_id in job_statuses:
                slurm_status = job_statuses[slurm_job_id]
                job["current_status"] = slurm_status.get("status", "UNKNOWN")
                job["time_used"] = slurm_status.get("time_used") or slurm_status.get("elapsed")
                job["time_left"] = slurm_status.get("time_left")
                job["in_queue"] = slurm_status.get("in_queue", False)

                # Update database with current status
                new_status = slurm_status.get("status", "UNKNOWN")
                cursor.execute("""
                    UPDATE hpl_configurations
                    SET status = ?
                    WHERE id = ?
                """, (new_status, job["config_id"]))

    # Calculate summary statistics
    status_counts = {}
    for job in jobs:
        status = job.get("current_status", job.get("status", "UNKNOWN"))
        status_counts[status] = status_counts.get(status, 0) + 1

    conn.commit()
    conn.close()

    return {
        "sweep": sweep_info,
        "jobs": jobs,
        "status_counts": status_counts
    }
