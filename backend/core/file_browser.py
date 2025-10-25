"""
File Browser for Cluster Filesystem
Allows browsing and verification of files on the remote cluster
"""
from typing import List, Dict, Tuple, Optional
from backend.core.ssh_manager import ssh_manager
import os


def list_directory(path: str = "~") -> Tuple[bool, List[Dict], str]:
    """
    List contents of a directory on the cluster

    Args:
        path: Directory path to list (default: home directory)

    Returns:
        Tuple of (success: bool, entries: List[Dict], error_message: str)
    """
    if not ssh_manager.is_connected():
        return False, [], "Not connected to cluster"

    try:
        # Expand path and list directory contents with details
        cmd = f"""
        cd {path} 2>/dev/null && pwd && ls -lAh --group-directories-first 2>/dev/null || {{
            echo "ERROR: Cannot access directory"
            exit 1
        }}
        """

        stdout, stderr, exit_code = ssh_manager.execute_command(cmd)

        if exit_code != 0 or "ERROR:" in stdout:
            return False, [], f"Cannot access directory: {path}"

        lines = stdout.strip().split('\n')
        if len(lines) < 1:
            return False, [], "Invalid directory output"

        # First line is the actual path (after expansion)
        actual_path = lines[0].strip()
        entries = []

        # Parse ls -lAh output (skip first line which is the pwd output, and total line if present)
        for line in lines[1:]:
            if line.startswith('total ') or not line.strip():
                continue

            parts = line.split(maxsplit=8)
            if len(parts) < 9:
                continue

            permissions = parts[0]
            size = parts[4]
            name = parts[8]

            # Skip . and ..
            if name in ['.', '..']:
                continue

            is_directory = permissions.startswith('d')
            is_executable = 'x' in permissions[3:6]  # Check user execute permission
            is_symlink = permissions.startswith('l')

            entry = {
                "name": name,
                "type": "directory" if is_directory else ("symlink" if is_symlink else "file"),
                "size": size,
                "permissions": permissions,
                "executable": is_executable,
                "path": f"{actual_path}/{name}".replace('//', '/')
            }

            entries.append(entry)

        return True, entries, actual_path

    except Exception as e:
        return False, [], f"Error listing directory: {str(e)}"


def verify_file(path: str) -> Tuple[bool, Dict, str]:
    """
    Verify a file exists and get its details

    Args:
        path: File path to verify

    Returns:
        Tuple of (success: bool, file_info: Dict, error_message: str)
    """
    if not ssh_manager.is_connected():
        return False, {}, "Not connected to cluster"

    try:
        # Check if file exists and get details
        cmd = f"""
        if [ -e {path} ]; then
            ls -lh {path}
            echo "---"
            file {path} 2>/dev/null || echo "Unknown file type"
            echo "---"
            if [ -x {path} ]; then
                echo "EXECUTABLE"
            else
                echo "NOT_EXECUTABLE"
            fi
        else
            echo "FILE_NOT_FOUND"
        fi
        """

        stdout, stderr, exit_code = ssh_manager.execute_command(cmd)

        if "FILE_NOT_FOUND" in stdout:
            return False, {}, f"File not found: {path}"

        lines = stdout.strip().split('\n')

        # Parse ls output
        ls_line = lines[0] if lines else ""
        parts = ls_line.split(maxsplit=8)

        if len(parts) < 9:
            return False, {}, "Could not parse file information"

        permissions = parts[0]
        size = parts[4]
        name = parts[8]

        # Get file type
        file_type_line = ""
        for i, line in enumerate(lines):
            if line == "---" and i + 1 < len(lines):
                file_type_line = lines[i + 1]
                break

        # Check executable
        is_executable = "EXECUTABLE" in stdout

        file_info = {
            "path": path,
            "name": os.path.basename(path),
            "size": size,
            "permissions": permissions,
            "executable": is_executable,
            "file_type": file_type_line,
            "is_file": permissions.startswith('-'),
            "is_directory": permissions.startswith('d'),
            "exists": True
        }

        return True, file_info, ""

    except Exception as e:
        return False, {}, f"Error verifying file: {str(e)}"


def find_hpl_binaries(search_paths: Optional[List[str]] = None) -> Tuple[bool, List[str], str]:
    """
    Search for HPL binaries (xhpl) in common locations

    Args:
        search_paths: Optional list of paths to search

    Returns:
        Tuple of (success: bool, found_paths: List[str], error_message: str)
    """
    if not ssh_manager.is_connected():
        return False, [], "Not connected to cluster"

    if search_paths is None:
        search_paths = [
            "~",
            "~/hpl",
            "~/HPL",
            "~/bin",
            "/usr/local/bin",
            "/opt/hpl",
            "/opt/HPL",
            "$HOME/hpl*/bin",
            "$HOME/HPL*/bin"
        ]

    try:
        # Build find command to search for xhpl
        paths_str = " ".join(search_paths)
        cmd = f"""
        for dir in {paths_str}; do
            find $dir -name "xhpl" -type f -executable 2>/dev/null
        done | head -20
        """

        stdout, stderr, exit_code = ssh_manager.execute_command(cmd)

        found_paths = []
        if stdout.strip():
            found_paths = [line.strip() for line in stdout.strip().split('\n') if line.strip()]

        return True, found_paths, ""

    except Exception as e:
        return False, [], f"Error searching for HPL binaries: {str(e)}"


def get_parent_directory(path: str) -> str:
    """
    Get parent directory of a path

    Args:
        path: Current path

    Returns:
        Parent directory path
    """
    if path in ['/', '~']:
        return path

    # Remove trailing slash
    path = path.rstrip('/')

    # Get parent
    parent = os.path.dirname(path)

    return parent if parent else '/'
