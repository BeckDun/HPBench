# HPBench

A web application for automated [HPL (High Performance Linpack)](https://www.netlib.org/benchmark/hpl/) benchmark parameter sweeping and performance analysis on HPC clusters.

## Overview

HPBench helps you optimize HPL performance by automating parameter sweeps across your HPC cluster. The application runs locally on your machine and connects to remote clusters via SSH to submit jobs, monitor progress, and collect results.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/BeckDun/HPBench.git
cd HPBench

# Create and activate virtual environment (using uv)
uv venv
source .venv/bin/activate

# Or with standard Python venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Open your browser to http://localhost:8000

## Features

### Current Features
- **SSH Authentication**: Secure connection to remote HPC clusters
- **Cluster Integration**: SLURM partition detection and job submission
- **Parameter Generation**: Automated HPL parameter sweep generation
- **File Browser**: Browse remote cluster filesystem to locate HPL binaries
- **Job Management**: Submit and monitor HPL benchmark jobs
- **Result Collection**: Retrieve and parse HPL results from completed jobs
- **Local Database**: SQLite database for persistent job tracking

### In Progress
- [ ] Job status monitoring and real-time updates
- [ ] Performance visualization and graphs
- [ ] Result analysis and comparison tools
- [ ] PDF report generation
- [ ] Best configuration recommendations
- [ ] Multi-cluster support

## Prerequisites

- Python 3.8 or higher
- SSH access to HPC cluster with SLURM
- HPL installed on the cluster
- Modern web browser

## Project Structure

```
HPBench/
├── app.py                    # Main application entry point
├── requirements.txt          # Python dependencies
├── backend/                  # Backend API and core logic
│   ├── api/                 # FastAPI routes
│   ├── core/                # Core functionality
│   └── models/              # Data models
├── frontend/                # Web interface
│   ├── index.html
│   ├── css/
│   └── js/
├── data/                    # Local data storage
│   └── hpl_sweep.db        # SQLite database
├── config/                  # Configuration files
└── logs/                    # Application logs
```

## Usage

1. **Start the application**
   ```bash
   python app.py
   ```

2. **Login to your cluster**
   - Enter hostname, username, and password
   - Connection is maintained for the session

3. **Configure your sweep**
   - Browse for HPL binary (xhpl)
   - Set parameter ranges (N, NB, P, Q)
   - Select SLURM partition and resources

4. **Submit jobs**
   - Generate parameter combinations
   - Submit sweep to cluster
   - Monitor job progress

5. **View results**
   - Collect completed job results
   - Analyze performance data

## Configuration

The application automatically creates necessary directories on first run. Configuration can be customized through environment variables or configuration files in the `config/` directory.

## Troubleshooting

- **Connection issues**: Verify SSH credentials and network access
- **Job submission fails**: Check SLURM partition availability and resource limits
- **Missing results**: Ensure jobs completed successfully and output files exist

For more help, check the logs in `logs/` directory.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

MIT License

---

**Note**: This application was developed with assistance from [Claude Code](https://claude.com/claude-code), Anthropic's AI-powered coding assistant.
