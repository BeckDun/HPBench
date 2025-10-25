"""
SSH Manager for HPL-Sweep
Handles SSH connections to remote HPC clusters
"""
import paramiko
from typing import Optional, Tuple

class SSHManager:
    """Manages SSH connections to remote clusters"""

    def __init__(self):
        self.client: Optional[paramiko.SSHClient] = None
        self.hostname: Optional[str] = None
        self.username: Optional[str] = None

    def connect(self, hostname: str, username: str, password: str) -> Tuple[bool, str]:
        """
        Connect to remote cluster via SSH

        Args:
            hostname: Cluster hostname or IP
            username: SSH username
            password: SSH password

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.client.connect(
                hostname=hostname,
                username=username,
                password=password,
                timeout=10
            )

            self.hostname = hostname
            self.username = username

            return True, f"Connected to {hostname}"

        except paramiko.AuthenticationException:
            return False, "Authentication failed. Please check your username and password."
        except paramiko.SSHException as e:
            return False, f"SSH connection failed: {str(e)}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def execute_command(self, command: str) -> Tuple[str, str, int]:
        """
        Execute a command on the remote cluster

        Args:
            command: Command to execute

        Returns:
            Tuple of (stdout: str, stderr: str, exit_code: int)
        """
        if not self.client:
            return "", "Not connected to any cluster", 1

        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()

            stdout_str = stdout.read().decode('utf-8')
            stderr_str = stderr.read().decode('utf-8')

            return stdout_str, stderr_str, exit_code

        except Exception as e:
            return "", f"Command execution failed: {str(e)}", 1

    def is_connected(self) -> bool:
        """Check if SSH connection is active"""
        if not self.client:
            return False

        try:
            transport = self.client.get_transport()
            return transport is not None and transport.is_active()
        except:
            return False

    def disconnect(self):
        """Close SSH connection"""
        if self.client:
            self.client.close()
            self.client = None
            self.hostname = None
            self.username = None

# Global SSH manager instance
ssh_manager = SSHManager()
