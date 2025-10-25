"""
SLURM Interface for HPL-Sweep
Handles SLURM commands and job management
"""
from typing import List, Tuple, Dict, Optional
from backend.core.ssh_manager import ssh_manager
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
