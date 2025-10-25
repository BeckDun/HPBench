"""
HPL Output Parser
Parses HPL benchmark output to extract performance metrics
"""
import re
from typing import Dict, Optional, List
from datetime import datetime


class HPLResult:
    """Represents parsed HPL benchmark result"""

    def __init__(self):
        self.n: Optional[int] = None
        self.nb: Optional[int] = None
        self.p: Optional[int] = None
        self.q: Optional[int] = None
        self.time: Optional[float] = None
        self.gflops: Optional[float] = None
        self.residual_check: Optional[str] = None
        self.passed: bool = False
        self.error_message: Optional[str] = None
        self.job_info: Dict = {}

    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return {
            "n": self.n,
            "nb": self.nb,
            "p": self.p,
            "q": self.q,
            "time": self.time,
            "gflops": self.gflops,
            "residual_check": self.residual_check,
            "passed": self.passed,
            "error_message": self.error_message,
            "job_info": self.job_info
        }


def parse_hpl_output(output_content: str) -> HPLResult:
    """
    Parse HPL benchmark output file

    HPL output typically contains a results table like:
    ================================================================================
    T/V                N    NB     P     Q               Time                 Gflops
    --------------------------------------------------------------------------------
    WR00L2L2       10000   128     2     2              52.51              1.283e+01
    --------------------------------------------------------------------------------

    Args:
        output_content: Content of HPL output file

    Returns:
        HPLResult object with parsed data
    """
    result = HPLResult()

    try:
        lines = output_content.split('\n')

        # Extract job information
        for line in lines:
            if "Job ID:" in line:
                match = re.search(r'Job ID:\s*(\S+)', line)
                if match:
                    result.job_info['job_id'] = match.group(1)

            if "Hostname:" in line:
                match = re.search(r'Hostname:\s*(.+)', line)
                if match:
                    result.job_info['hostname'] = match.group(1).strip()

            if "Date:" in line and 'start_date' not in result.job_info:
                match = re.search(r'Date:\s*(.+)', line)
                if match:
                    result.job_info['start_date'] = match.group(1).strip()

            if "Completed at:" in line:
                match = re.search(r'Completed at:\s*(.+)', line)
                if match:
                    result.job_info['end_date'] = match.group(1).strip()

            if "HPL exit code:" in line:
                match = re.search(r'HPL exit code:\s*(\d+)', line)
                if match:
                    result.job_info['exit_code'] = int(match.group(1))

        # Find HPL results table
        # Look for lines that match the result pattern
        # Format: WR00L2L2       10000   128     2     2              52.51              1.283e+01
        result_pattern = re.compile(
            r'WR\w+\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)\s+([\d.e+\-]+)'
        )

        for line in lines:
            match = result_pattern.search(line)
            if match:
                result.n = int(match.group(1))
                result.nb = int(match.group(2))
                result.p = int(match.group(3))
                result.q = int(match.group(4))
                result.time = float(match.group(5))
                result.gflops = float(match.group(6))

        # Check for residual validation
        if re.search(r'PASSED', output_content, re.IGNORECASE):
            result.passed = True
            result.residual_check = "PASSED"
        elif re.search(r'FAILED', output_content, re.IGNORECASE):
            result.passed = False
            result.residual_check = "FAILED"

        # Check for errors
        if "error" in output_content.lower() or "fail" in output_content.lower():
            # Try to extract error message
            for line in lines:
                if "error" in line.lower():
                    result.error_message = line.strip()
                    break

        # If we found performance data, consider it successful
        if result.gflops is not None:
            result.passed = True

    except Exception as e:
        result.error_message = f"Failed to parse HPL output: {str(e)}"

    return result


def parse_multiple_results(output_content: str) -> List[HPLResult]:
    """
    Parse HPL output that may contain multiple benchmark results

    Args:
        output_content: Content of HPL output file

    Returns:
        List of HPLResult objects
    """
    results = []

    # Split by the results separator line
    sections = re.split(r'={70,}', output_content)

    for section in sections:
        if 'WR' in section and 'Gflops' in section:
            result = parse_hpl_output(section)
            if result.gflops is not None:
                results.append(result)

    # If no results found in sections, try parsing the whole content
    if not results:
        result = parse_hpl_output(output_content)
        if result.gflops is not None or result.error_message:
            results.append(result)

    return results


def extract_best_result(results: List[HPLResult]) -> Optional[HPLResult]:
    """
    Extract the best (highest GFLOPS) result from a list

    Args:
        results: List of HPLResult objects

    Returns:
        Best HPLResult or None
    """
    if not results:
        return None

    valid_results = [r for r in results if r.gflops is not None]

    if not valid_results:
        return results[0] if results else None

    return max(valid_results, key=lambda r: r.gflops)
