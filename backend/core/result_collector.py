"""
Result Collector
Handles retrieval of HPL result files from the cluster via SFTP
"""
from typing import Dict, Tuple, Optional, List
from backend.core.ssh_manager import ssh_manager
from backend.core.hpl_parser import parse_hpl_output, HPLResult
import io


def get_result_file_path(sweep_id: int, config_id: int, file_type: str = "out") -> str:
    """
    Get the path to a result file on the cluster

    Args:
        sweep_id: Sweep ID
        config_id: Configuration ID
        file_type: File type ("out" or "err")

    Returns:
        Path to the result file
    """
    return f"hpl_results/sweep_{sweep_id}/config_{config_id}.{file_type}"


def check_result_file_exists(sweep_id: int, config_id: int) -> Tuple[bool, bool, str]:
    """
    Check if result files exist on the cluster

    Args:
        sweep_id: Sweep ID
        config_id: Configuration ID

    Returns:
        Tuple of (out_exists: bool, err_exists: bool, error_message: str)
    """
    if not ssh_manager.is_connected():
        return False, False, "Not connected to cluster"

    out_path = get_result_file_path(sweep_id, config_id, "out")
    err_path = get_result_file_path(sweep_id, config_id, "err")

    # Check if output file exists
    stdout, stderr, exit_code = ssh_manager.execute_command(f"test -f ~/{out_path} && echo 'EXISTS'")
    out_exists = "EXISTS" in stdout

    # Check if error file exists
    stdout, stderr, exit_code = ssh_manager.execute_command(f"test -f ~/{err_path} && echo 'EXISTS'")
    err_exists = "EXISTS" in stdout

    return out_exists, err_exists, ""


def retrieve_result_file(sweep_id: int, config_id: int, file_type: str = "out") -> Tuple[bool, Optional[str], str]:
    """
    Retrieve a result file from the cluster via SFTP

    Args:
        sweep_id: Sweep ID
        config_id: Configuration ID
        file_type: File type ("out" or "err")

    Returns:
        Tuple of (success: bool, content: Optional[str], error_message: str)
    """
    if not ssh_manager.is_connected():
        return False, None, "Not connected to cluster"

    try:
        remote_path = get_result_file_path(sweep_id, config_id, file_type)

        # Use SFTP to retrieve the file
        sftp = ssh_manager.client.open_sftp()

        try:
            # Read the file content
            with sftp.file(remote_path, 'r') as remote_file:
                content = remote_file.read().decode('utf-8')

            sftp.close()
            return True, content, ""

        except FileNotFoundError:
            sftp.close()
            return False, None, f"File not found: {remote_path}"

        except Exception as e:
            sftp.close()
            return False, None, f"Failed to read file: {str(e)}"

    except Exception as e:
        return False, None, f"SFTP error: {str(e)}"


def retrieve_and_parse_result(sweep_id: int, config_id: int) -> Tuple[bool, Optional[HPLResult], str, Optional[str]]:
    """
    Retrieve and parse HPL result for a specific configuration

    Args:
        sweep_id: Sweep ID
        config_id: Configuration ID

    Returns:
        Tuple of (success: bool, result: Optional[HPLResult], error_content: str, error_message: str)
    """
    # Check if files exist
    out_exists, err_exists, check_error = check_result_file_exists(sweep_id, config_id)

    if check_error:
        return False, None, "", check_error

    if not out_exists:
        return False, None, "", "Output file not found (job may not have completed yet)"

    # Retrieve output file
    success, out_content, out_error = retrieve_result_file(sweep_id, config_id, "out")

    if not success:
        return False, None, "", out_error

    # Parse the output
    result = parse_hpl_output(out_content)

    # Retrieve error file if it exists
    error_content = ""
    if err_exists:
        success, err_content, _ = retrieve_result_file(sweep_id, config_id, "err")
        if success and err_content:
            error_content = err_content

    return True, result, error_content, ""


def retrieve_sweep_results(sweep_id: int, config_ids: List[int]) -> Dict[int, Dict]:
    """
    Retrieve and parse results for all configurations in a sweep

    Args:
        sweep_id: Sweep ID
        config_ids: List of configuration IDs

    Returns:
        Dictionary mapping config_id to result data
    """
    results = {}

    for config_id in config_ids:
        success, result, error_content, error_message = retrieve_and_parse_result(sweep_id, config_id)

        if success and result:
            results[config_id] = {
                "success": True,
                "result": result.to_dict(),
                "error_content": error_content,
                "has_error": bool(error_content)
            }
        else:
            results[config_id] = {
                "success": False,
                "error_message": error_message,
                "result": None
            }

    return results


def list_result_files(sweep_id: int) -> Tuple[bool, List[str], str]:
    """
    List all result files for a sweep

    Args:
        sweep_id: Sweep ID

    Returns:
        Tuple of (success: bool, files: List[str], error_message: str)
    """
    if not ssh_manager.is_connected():
        return False, [], "Not connected to cluster"

    results_dir = f"hpl_results/sweep_{sweep_id}"

    # List files in the results directory
    stdout, stderr, exit_code = ssh_manager.execute_command(f"ls -1 ~/{results_dir} 2>/dev/null || echo 'NO_FILES'")

    if "NO_FILES" in stdout or exit_code != 0:
        return True, [], ""

    files = [f.strip() for f in stdout.strip().split('\n') if f.strip()]

    return True, files, ""
