"""
HPL Parameter Models
"""
from pydantic import BaseModel
from typing import List, Optional

class HPLParameterRange(BaseModel):
    """HPL parameter sweep configuration"""
    # N: Problem size
    n_start: int
    n_end: int
    n_step: int

    # NB: Block size
    nb_values: List[int]  # Common values: 64, 128, 192, 256

    # P x Q: Process grid
    p_values: List[int]
    q_values: List[int]

    # Optional parameters
    pfact: str = "R"  # Panel factorization (L, R, C)
    nbmin: int = 4     # Recursion stopping criterion
    rfact: str = "R"   # Recursive panel factorization
    bcast: str = "1"   # Broadcast (0=1ring, 1=1ringM, 2=2ring, 3=2ringM)
    depth: int = 1     # Lookahead depth
    swap: str = "2"    # Swapping algorithm
    l1: int = 0        # L1 in (0=transposed, 1=no-transposed) form
    u: int = 0         # U in (0=transposed, 1=no-transposed) form
    equil: int = 1     # Equilibration (0=no, 1=yes)
    align: int = 8     # Data alignment

class HPLConfiguration(BaseModel):
    """Single HPL configuration"""
    n: int
    nb: int
    p: int
    q: int
    pfact: str = "R"
    nbmin: int = 4
    rfact: str = "R"
    bcast: str = "1"
    depth: int = 1
    swap: str = "2"
    l1: int = 0
    u: int = 0
    equil: int = 1
    align: int = 8

class ParameterSweepRequest(BaseModel):
    """Request to generate parameter sweep"""
    parameter_range: HPLParameterRange
    max_combinations: Optional[int] = 100  # Limit total combinations
