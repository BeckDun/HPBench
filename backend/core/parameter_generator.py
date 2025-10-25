"""
HPL Parameter Generator
Generates parameter sweep combinations
"""
from typing import List
from backend.models.hpl_params import HPLParameterRange, HPLConfiguration
import itertools

def generate_parameter_sweep(param_range: HPLParameterRange, max_combinations: int = 100) -> List[HPLConfiguration]:
    """
    Generate all combinations of HPL parameters based on the range

    Args:
        param_range: Parameter range configuration
        max_combinations: Maximum number of combinations to generate

    Returns:
        List of HPL configurations
    """
    configurations = []

    # Generate N values
    n_values = list(range(param_range.n_start, param_range.n_end + 1, param_range.n_step))

    # Get NB values
    nb_values = param_range.nb_values

    # Get P and Q values
    p_values = param_range.p_values
    q_values = param_range.q_values

    # Generate all combinations
    total_combinations = len(n_values) * len(nb_values) * len(p_values) * len(q_values)

    if total_combinations > max_combinations:
        # Sample evenly if too many combinations
        step = total_combinations // max_combinations
        count = 0
    else:
        step = 1
        count = 0

    for n in n_values:
        for nb in nb_values:
            for p in p_values:
                for q in q_values:
                    if step > 1:
                        count += 1
                        if count % step != 0:
                            continue

                    config = HPLConfiguration(
                        n=n,
                        nb=nb,
                        p=p,
                        q=q,
                        pfact=param_range.pfact,
                        nbmin=param_range.nbmin,
                        rfact=param_range.rfact,
                        bcast=param_range.bcast,
                        depth=param_range.depth,
                        swap=param_range.swap,
                        l1=param_range.l1,
                        u=param_range.u,
                        equil=param_range.equil,
                        align=param_range.align
                    )
                    configurations.append(config)

                    if len(configurations) >= max_combinations:
                        return configurations

    return configurations

def validate_parameters(config: HPLConfiguration, total_nodes: int, cpus_per_node: int) -> tuple[bool, str]:
    """
    Validate HPL parameters

    Args:
        config: HPL configuration
        total_nodes: Total number of nodes
        cpus_per_node: CPUs per node

    Returns:
        Tuple of (valid: bool, message: str)
    """
    # Check P * Q matches total processes
    total_processes = total_nodes * cpus_per_node
    pq_product = config.p * config.q

    if pq_product != total_processes:
        return False, f"P*Q ({pq_product}) must equal total processes ({total_processes})"

    # Check N is divisible by NB
    if config.n % config.nb != 0:
        return False, f"N ({config.n}) must be divisible by NB ({config.nb})"

    # Check N is reasonable
    if config.n < 1000:
        return False, f"N ({config.n}) is too small (< 1000)"

    # Check NB is reasonable
    if config.nb < 32 or config.nb > 512:
        return False, f"NB ({config.nb}) should be between 32 and 512"

    return True, "Valid"

def generate_hpl_dat_content(config: HPLConfiguration) -> str:
    """
    Generate HPL.dat file content for a configuration

    Args:
        config: HPL configuration

    Returns:
        String content of HPL.dat file
    """
    return f"""HPLinpack benchmark input file
Innovative Computing Laboratory, University of Tennessee
HPL.out      output file name (if any)
6            device out (6=stdout,7=stderr,file)
1            # of problems sizes (N)
{config.n}         Ns
1            # of NBs
{config.nb}           NBs
0            PMAP process mapping (0=Row-,1=Column-major)
1            # of process grids (P x Q)
{config.p}            Ps
{config.q}            Qs
16.0         threshold
1            # of panel fact
{config.pfact}            PFACTs (0=left, 1=Crout, 2=Right)
1            # of recursive stopping criterium
{config.nbmin}            NBMINs (>= 1)
1            # of panels in recursion
1            NDIVs
1            # of recursive panel fact.
{config.rfact}            RFACTs (0=left, 1=Crout, 2=Right)
1            # of broadcast
{config.bcast}            BCASTs (0=1rg,1=1rM,2=2rg,3=2rM,4=Lng,5=LnM)
1            # of lookahead depth
{config.depth}            DEPTHs (>=0)
1            SWAP (0=bin-exch,1=long,2=mix)
{config.swap}            swapping threshold
1            L1 in (0=transposed,1=no-transposed) form
{config.l1}            L1 in (0=transposed,1=no-transposed) form
1            U  in (0=transposed,1=no-transposed) form
{config.u}            U  in (0=transposed,1=no-transposed) form
1            Equilibration (0=no,1=yes)
{config.equil}            Equilibration (0=no,1=yes)
{config.align}            memory alignment in double (> 0)
"""

def get_recommended_nb_values() -> List[int]:
    """Get commonly used NB values"""
    return [64, 96, 128, 160, 192, 224, 256]

def calculate_recommended_pq(total_processes: int) -> List[tuple[int, int]]:
    """
    Calculate recommended P and Q values for given total processes

    Args:
        total_processes: Total number of MPI processes

    Returns:
        List of (P, Q) tuples
    """
    pq_pairs = []

    # Find all factor pairs
    for p in range(1, int(total_processes ** 0.5) + 1):
        if total_processes % p == 0:
            q = total_processes // p
            # Prefer Q >= P for better performance
            if q >= p:
                pq_pairs.append((p, q))

    return pq_pairs
