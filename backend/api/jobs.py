"""
Jobs API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
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
from backend.core.result_collector import (
    retrieve_and_parse_result,
    retrieve_sweep_results,
    list_result_files
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
    try:
        configurations = generate_parameter_sweep(
            param_range=request.parameter_range,
            max_combinations=request.max_combinations or 100
        )

        return {
            "total_configurations": len(configurations),
            "configurations": configurations
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter range: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating parameters: {str(e)}")

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

@router.post("/sweep/{sweep_id}/collect-results")
async def collect_sweep_results(sweep_id: int):
    """
    Collect and parse results for all completed jobs in a sweep
    """
    if not ssh_manager.is_connected():
        raise HTTPException(status_code=401, detail="Not connected to cluster. Please login first.")

    conn = get_connection()
    cursor = conn.cursor()

    # Get all configurations for this sweep
    cursor.execute("""
        SELECT id, slurm_job_id, n, nb, p, q, status
        FROM hpl_configurations
        WHERE sweep_id = ?
    """, (sweep_id,))

    configs = []
    for row in cursor.fetchall():
        configs.append({
            "config_id": row[0],
            "slurm_job_id": row[1],
            "n": row[2],
            "nb": row[3],
            "p": row[4],
            "q": row[5],
            "status": row[6]
        })

    if not configs:
        conn.close()
        raise HTTPException(status_code=404, detail="No configurations found for this sweep")

    # Collect results for each configuration
    collected_count = 0
    failed_count = 0
    results_summary = []

    for config in configs:
        config_id = config["config_id"]

        # Check if result already exists
        cursor.execute("SELECT id FROM results WHERE config_id = ?", (config_id,))
        existing_result = cursor.fetchone()

        # Skip if already collected (unless you want to re-collect)
        # if existing_result:
        #     continue

        # Retrieve and parse result
        success, result, error_content, error_message = retrieve_and_parse_result(sweep_id, config_id)

        if success and result:
            # Store or update result in database
            if existing_result:
                cursor.execute("""
                    UPDATE results
                    SET gflops = ?, time = ?, residual = ?, passed = ?,
                        error_message = ?, job_info = ?, error_content = ?,
                        retrieved_at = CURRENT_TIMESTAMP
                    WHERE config_id = ?
                """, (
                    result.gflops,
                    result.time,
                    result.residual_check,
                    result.passed,
                    result.error_message,
                    json.dumps(result.job_info),
                    error_content,
                    config_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO results
                    (config_id, gflops, time, residual, passed, error_message, job_info, error_content)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    config_id,
                    result.gflops,
                    result.time,
                    result.residual_check,
                    result.passed,
                    result.error_message,
                    json.dumps(result.job_info),
                    error_content
                ))

            collected_count += 1
            results_summary.append({
                "config_id": config_id,
                "success": True,
                "gflops": result.gflops,
                "passed": result.passed
            })
        else:
            failed_count += 1
            results_summary.append({
                "config_id": config_id,
                "success": False,
                "error": error_message
            })

    conn.commit()
    conn.close()

    return {
        "success": True,
        "sweep_id": sweep_id,
        "total_configs": len(configs),
        "collected_count": collected_count,
        "failed_count": failed_count,
        "results": results_summary
    }

@router.get("/sweep/{sweep_id}/results")
async def get_sweep_results(sweep_id: int):
    """
    Get parsed results for a sweep
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get sweep info
    cursor.execute("""
        SELECT id, name, total_jobs, nodes, cpus_per_node, partition, created_at
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
        "nodes": sweep_row[3],
        "cpus_per_node": sweep_row[4],
        "partition": sweep_row[5],
        "created_at": sweep_row[6]
    }

    # Get all results with configuration info
    cursor.execute("""
        SELECT
            c.id, c.n, c.nb, c.p, c.q, c.slurm_job_id, c.status,
            r.gflops, r.time, r.residual, r.passed, r.error_message,
            r.job_info, r.retrieved_at
        FROM hpl_configurations c
        LEFT JOIN results r ON c.id = r.config_id
        WHERE c.sweep_id = ?
        ORDER BY c.id
    """, (sweep_id,))

    results = []
    for row in cursor.fetchall():
        job_info = json.loads(row[12]) if row[12] else {}

        results.append({
            "config_id": row[0],
            "n": row[1],
            "nb": row[2],
            "p": row[3],
            "q": row[4],
            "slurm_job_id": row[5],
            "status": row[6],
            "gflops": row[7],
            "time": row[8],
            "residual": row[9],
            "passed": row[10],
            "error_message": row[11],
            "job_info": job_info,
            "retrieved_at": row[13],
            "has_result": row[7] is not None
        })

    conn.close()

    # Calculate statistics
    valid_results = [r for r in results if r["gflops"] is not None]
    best_result = max(valid_results, key=lambda r: r["gflops"]) if valid_results else None

    stats = {
        "total_configs": len(results),
        "completed_with_results": len(valid_results),
        "best_gflops": best_result["gflops"] if best_result else None,
        "best_config": {
            "n": best_result["n"],
            "nb": best_result["nb"],
            "p": best_result["p"],
            "q": best_result["q"]
        } if best_result else None
    }

    return {
        "sweep": sweep_info,
        "results": results,
        "statistics": stats
    }

@router.get("/config/{config_id}/result")
async def get_config_result(config_id: int):
    """
    Get detailed result for a specific configuration
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get configuration info
    cursor.execute("""
        SELECT
            c.id, c.sweep_id, c.n, c.nb, c.p, c.q, c.slurm_job_id, c.status,
            r.gflops, r.time, r.residual, r.passed, r.error_message,
            r.job_info, r.error_content, r.retrieved_at
        FROM hpl_configurations c
        LEFT JOIN results r ON c.id = r.config_id
        WHERE c.id = ?
    """, (config_id,))

    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Configuration not found")

    job_info = json.loads(row[13]) if row[13] else {}

    result = {
        "config_id": row[0],
        "sweep_id": row[1],
        "n": row[2],
        "nb": row[3],
        "p": row[4],
        "q": row[5],
        "slurm_job_id": row[6],
        "status": row[7],
        "gflops": row[8],
        "time": row[9],
        "residual": row[10],
        "passed": row[11],
        "error_message": row[12],
        "job_info": job_info,
        "error_content": row[14],
        "retrieved_at": row[15],
        "has_result": row[8] is not None
    }

    conn.close()

    return result
