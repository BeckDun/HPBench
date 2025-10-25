"""
SLURM Interface for HPL-Sweep
Handles SLURM commands and job management
"""
from typing import List, Tuple, Dict, Optional
from backend.core.ssh_manager import ssh_manager
from backend.models.hpl_params import HPLConfiguration
from backend.core.parameter_generator import generate_hpl_dat_content
import time
import re

def get_partitions() -> Tuple[bool, List[str], str]:
    """
    Get available SLURM partitions from the cluster

    Returns:
        Tuple of (success: bool, partitions: List[str], error_message: str)
    """
    if not ssh_manager.is_connected():
        return False, [], "Not connected to cluster"

    # Use sinfo to get partition names
    stdout, stderr, exit_code = ssh_manager.execute_command(
        "sinfo -h -o '%P' | sort -u"
    )

    if exit_code != 0:
        return False, [], f"Failed to get partitions: {stderr}"

    # Parse partition names (remove asterisk from default partition)
    partitions = []
    for line in stdout.strip().split('\n'):
        partition = line.strip().replace('*', '')  # Remove default partition marker
        if partition:
            partitions.append(partition)

    return True, partitions, ""

def get_cluster_info() -> dict:
    """
    Get basic cluster information

    Returns:
        Dictionary with cluster info
    """
    if not ssh_manager.is_connected():
        return {"error": "Not connected to cluster"}

    info = {}

    # Get SLURM version
    stdout, stderr, exit_code = ssh_manager.execute_command("sinfo --version")
    if exit_code == 0:
        info["slurm_version"] = stdout.strip()

    # Get number of nodes
    stdout, stderr, exit_code = ssh_manager.execute_command("sinfo -h -o '%D'")
    if exit_code == 0:
        try:
            info["total_nodes"] = sum(int(x) for x in stdout.strip().split('\n') if x)
        except:
            info["total_nodes"] = "unknown"

    return info

def submit_test_job(nodes: int, cpus_per_node: int, partition: str) -> Dict[str, any]:
    """
    Submit a test SLURM job that runs hostname to verify configuration

    Args:
        nodes: Number of nodes to request
        cpus_per_node: CPUs per node
        partition: SLURM partition name

    Returns:
        Dictionary with test results
    """
    if not ssh_manager.is_connected():
        return {"success": False, "error": "Not connected to cluster"}

    # Create a simple test script
    test_script = f"""#!/bin/bash
#SBATCH --job-name=hpl_test
#SBATCH --nodes={nodes}
#SBATCH --ntasks-per-node={cpus_per_node}
#SBATCH --partition={partition}
#SBATCH --time=00:02:00
#SBATCH --output=hpl_test_%j.out

echo "=== HPL-Sweep Test Job ==="
echo "Hostname: $(hostname)"
echo "Date: $(date)"
echo "Nodes allocated: $SLURM_JOB_NUM_NODES"
echo "Tasks per node: {cpus_per_node}"
echo "Partition: {partition}"
echo ""
echo "Running hostname on all nodes:"
srun hostname
echo ""
echo "=== Test Complete ==="
"""

    # Write the script to a temporary file on the cluster
    script_path = "/tmp/hpl_test_job.sh"
    create_script_cmd = f"cat > {script_path} << 'EOFSCRIPT'\n{test_script}\nEOFSCRIPT"

    stdout, stderr, exit_code = ssh_manager.execute_command(create_script_cmd)
    if exit_code != 0:
        return {"success": False, "error": f"Failed to create test script: {stderr}"}

    # Submit the job
    stdout, stderr, exit_code = ssh_manager.execute_command(f"sbatch {script_path}")
    if exit_code != 0:
        return {"success": False, "error": f"Failed to submit test job: {stderr}"}

    # Extract job ID from sbatch output
    match = re.search(r'Submitted batch job (\d+)', stdout)
    if not match:
        return {"success": False, "error": f"Could not parse job ID from: {stdout}"}

    job_id = match.group(1)

    # Wait for job to complete (max 60 seconds)
    max_wait = 60
    wait_interval = 2
    elapsed = 0

    job_state = "UNKNOWN"
    while elapsed < max_wait:
        stdout, stderr, exit_code = ssh_manager.execute_command(f"squeue -j {job_id} -h -o '%T'")

        if exit_code != 0 or not stdout.strip():
            # Job no longer in queue, likely completed
            break

        job_state = stdout.strip()
        if job_state in ["COMPLETED", "FAILED", "CANCELLED"]:
            break

        time.sleep(wait_interval)
        elapsed += wait_interval

    # Get job output
    output_file = f"hpl_test_{job_id}.out"
    stdout, stderr, exit_code = ssh_manager.execute_command(f"cat {output_file} 2>&1")

    job_output = stdout if stdout else "No output file found"

    # Check if test passed
    test_passed = "=== Test Complete ===" in job_output and "Running hostname on all nodes:" in job_output

    # Clean up
    ssh_manager.execute_command(f"rm -f {script_path} {output_file}")

    return {
        "success": True,
        "job_id": job_id,
        "job_state": job_state,
        "test_passed": test_passed,
        "output": job_output,
        "nodes": nodes,
        "cpus_per_node": cpus_per_node,
        "partition": partition
    }

def generate_slurm_script(
    config: HPLConfiguration,
    nodes: int,
    cpus_per_node: int,
    partition: str,
    sweep_id: int,
    config_id: int,
    time_limit: str = "01:00:00",
    xhpl_path: str = "xhpl"
) -> str:
    """
    Generate SLURM batch script for HPL job

    Args:
        config: HPL configuration
        nodes: Number of nodes
        cpus_per_node: CPUs per node
        partition: SLURM partition
        sweep_id: Sweep ID
        config_id: Configuration ID
        time_limit: Job time limit
        xhpl_path: Path to xhpl binary

    Returns:
        SLURM script content
    """
    total_processes = nodes * cpus_per_node
    job_name = f"hpl_sweep_{sweep_id}_{config_id}"
    output_file = f"hpl_output_{sweep_id}_{config_id}.out"

    script = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --nodes={nodes}
#SBATCH --ntasks-per-node={cpus_per_node}
#SBATCH --partition={partition}
#SBATCH --time={time_limit}
#SBATCH --output={output_file}

# HPL Parameter Sweep Job
# Sweep ID: {sweep_id}, Config ID: {config_id}
# N={config.n}, NB={config.nb}, P={config.p}, Q={config.q}

echo "=== HPL Benchmark Job ==="
echo "Job ID: $SLURM_JOB_ID"
echo "Hostname: $(hostname)"
echo "Date: $(date)"
echo "Nodes: {nodes}"
echo "Tasks per node: {cpus_per_node}"
echo "Total MPI processes: {total_processes}"
echo "Partition: {partition}"
echo ""
echo "HPL Configuration:"
echo "  N  = {config.n}"
echo "  NB = {config.nb}"
echo "  P  = {config.p}"
echo "  Q  = {config.q}"
echo ""

# Run HPL benchmark
echo "Starting HPL benchmark..."
mpirun -np {total_processes} {xhpl_path}

echo ""
echo "=== HPL Job Complete ==="
echo "Completed at: $(date)"
"""
    return script

def submit_hpl_sweep(
    configurations: List[HPLConfiguration],
    nodes: int,
    cpus_per_node: int,
    partition: str,
    sweep_id: int,
    xhpl_path: str = "xhpl",
    time_limit: str = "01:00:00"
) -> Dict[str, any]:
    """
    Submit HPL parameter sweep jobs to SLURM

    Args:
        configurations: List of HPL configurations
        nodes: Number of nodes
        cpus_per_node: CPUs per node
        partition: SLURM partition
        sweep_id: Sweep session ID
        xhpl_path: Path to xhpl binary on cluster
        time_limit: Job time limit

    Returns:
        Dictionary with submission results
    """
    if not ssh_manager.is_connected():
        return {"success": False, "error": "Not connected to cluster"}

    submitted_jobs = []
    failed_jobs = []

    for idx, config in enumerate(configurations):
        config_id = idx + 1

        # Generate HPL.dat content
        hpl_dat_content = generate_hpl_dat_content(config)

        # Create HPL.dat file on cluster
        hpl_dat_path = f"/tmp/HPL_{sweep_id}_{config_id}.dat"
        create_hpl_cmd = f"cat > {hpl_dat_path} << 'EOFHPL'\n{hpl_dat_content}\nEOFHPL"

        stdout, stderr, exit_code = ssh_manager.execute_command(create_hpl_cmd)
        if exit_code != 0:
            failed_jobs.append({
                "config_id": config_id,
                "error": f"Failed to create HPL.dat: {stderr}"
            })
            continue

        # Generate SLURM script
        slurm_script = generate_slurm_script(
            config=config,
            nodes=nodes,
            cpus_per_node=cpus_per_node,
            partition=partition,
            sweep_id=sweep_id,
            config_id=config_id,
            time_limit=time_limit,
            xhpl_path=xhpl_path
        )

        # Create SLURM script file on cluster
        script_path = f"/tmp/hpl_job_{sweep_id}_{config_id}.sh"
        create_script_cmd = f"cat > {script_path} << 'EOFSCRIPT'\n{slurm_script}\nEOFSCRIPT"

        stdout, stderr, exit_code = ssh_manager.execute_command(create_script_cmd)
        if exit_code != 0:
            failed_jobs.append({
                "config_id": config_id,
                "error": f"Failed to create SLURM script: {stderr}"
            })
            continue

        # Submit job to SLURM
        # Change to directory with HPL.dat before submitting
        submit_cmd = f"cd /tmp && ln -sf {hpl_dat_path} HPL.dat && sbatch {script_path}"
        stdout, stderr, exit_code = ssh_manager.execute_command(submit_cmd)

        if exit_code != 0:
            failed_jobs.append({
                "config_id": config_id,
                "error": f"Failed to submit job: {stderr}"
            })
            continue

        # Extract job ID
        match = re.search(r'Submitted batch job (\d+)', stdout)
        if not match:
            failed_jobs.append({
                "config_id": config_id,
                "error": f"Could not parse job ID from: {stdout}"
            })
            continue

        slurm_job_id = match.group(1)
        submitted_jobs.append({
            "config_id": config_id,
            "slurm_job_id": slurm_job_id,
            "config": config.dict()
        })

    return {
        "success": True,
        "submitted_count": len(submitted_jobs),
        "failed_count": len(failed_jobs),
        "submitted_jobs": submitted_jobs,
        "failed_jobs": failed_jobs
    }

def get_job_status(slurm_job_id: str) -> Dict[str, any]:
    """
    Get status of a SLURM job

    Args:
        slurm_job_id: SLURM job ID

    Returns:
        Dictionary with job status information
    """
    if not ssh_manager.is_connected():
        return {"success": False, "error": "Not connected to cluster"}

    # First try squeue (for running/pending jobs)
    stdout, stderr, exit_code = ssh_manager.execute_command(
        f"squeue -j {slurm_job_id} -h -o '%T|%r|%M|%L'"
    )

    if exit_code == 0 and stdout.strip():
        # Job is in queue
        parts = stdout.strip().split('|')
        status = parts[0] if len(parts) > 0 else "UNKNOWN"
        reason = parts[1] if len(parts) > 1 else ""
        time_used = parts[2] if len(parts) > 2 else "0:00"
        time_left = parts[3] if len(parts) > 3 else "0:00"

        return {
            "success": True,
            "job_id": slurm_job_id,
            "status": status,
            "reason": reason,
            "time_used": time_used,
            "time_left": time_left,
            "in_queue": True
        }

    # Job not in queue, check sacct (for completed/failed jobs)
    stdout, stderr, exit_code = ssh_manager.execute_command(
        f"sacct -j {slurm_job_id} -n -o State,ExitCode,Elapsed --parsable2"
    )

    if exit_code == 0 and stdout.strip():
        lines = stdout.strip().split('\n')
        # Get first line (job status, not job steps)
        if lines:
            parts = lines[0].split('|')
            status = parts[0] if len(parts) > 0 else "UNKNOWN"
            exit_code_str = parts[1] if len(parts) > 1 else "0:0"
            elapsed = parts[2] if len(parts) > 2 else "0:00:00"

            return {
                "success": True,
                "job_id": slurm_job_id,
                "status": status,
                "exit_code": exit_code_str,
                "elapsed": elapsed,
                "in_queue": False
            }

    # Job not found
    return {
        "success": True,
        "job_id": slurm_job_id,
        "status": "NOT_FOUND",
        "in_queue": False
    }

def get_multiple_job_statuses(slurm_job_ids: List[str]) -> Dict[str, any]:
    """
    Get status of multiple SLURM jobs efficiently

    Args:
        slurm_job_ids: List of SLURM job IDs

    Returns:
        Dictionary with job statuses
    """
    if not ssh_manager.is_connected():
        return {"success": False, "error": "Not connected to cluster"}

    if not slurm_job_ids:
        return {"success": True, "job_statuses": {}}

    job_statuses = {}

    # Query all jobs at once with squeue
    job_ids_str = ",".join(slurm_job_ids)
    stdout, stderr, exit_code = ssh_manager.execute_command(
        f"squeue -j {job_ids_str} -h -o '%A|%T|%r|%M|%L' 2>/dev/null"
    )

    # Parse squeue results
    in_queue_jobs = set()
    if exit_code == 0 and stdout.strip():
        for line in stdout.strip().split('\n'):
            parts = line.split('|')
            if len(parts) >= 2:
                job_id = parts[0]
                status = parts[1]
                reason = parts[2] if len(parts) > 2 else ""
                time_used = parts[3] if len(parts) > 3 else "0:00"
                time_left = parts[4] if len(parts) > 4 else "0:00"

                job_statuses[job_id] = {
                    "status": status,
                    "reason": reason,
                    "time_used": time_used,
                    "time_left": time_left,
                    "in_queue": True
                }
                in_queue_jobs.add(job_id)

    # Check completed jobs with sacct
    completed_jobs = [jid for jid in slurm_job_ids if jid not in in_queue_jobs]

    if completed_jobs:
        job_ids_str = ",".join(completed_jobs)
        stdout, stderr, exit_code = ssh_manager.execute_command(
            f"sacct -j {job_ids_str} -n -X -o JobID,State,ExitCode,Elapsed --parsable2 2>/dev/null"
        )

        if exit_code == 0 and stdout.strip():
            for line in stdout.strip().split('\n'):
                parts = line.split('|')
                if len(parts) >= 2:
                    job_id = parts[0]
                    status = parts[1]
                    exit_code_str = parts[2] if len(parts) > 2 else "0:0"
                    elapsed = parts[3] if len(parts) > 3 else "0:00:00"

                    job_statuses[job_id] = {
                        "status": status,
                        "exit_code": exit_code_str,
                        "elapsed": elapsed,
                        "in_queue": False
                    }

    # Mark jobs not found
    for job_id in slurm_job_ids:
        if job_id not in job_statuses:
            job_statuses[job_id] = {
                "status": "NOT_FOUND",
                "in_queue": False
            }

    return {
        "success": True,
        "job_statuses": job_statuses
    }
