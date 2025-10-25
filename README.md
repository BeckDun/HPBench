# HPBench
# HPL Parameter Sweep Web Application - README Plan
**HPL-Sweep: Automated HPL Parameter Optimization Tool**
*A Python-based web application for automated HPL benchmark parameter sweeping and performance analysis on HPC clusters*

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Prerequisites](#prerequisites)
5. [Installation](#installation)
6. [Configuration](#configuration)
7. [Usage](#usage)
8. [API Documentation](#api-documentation)
9. [Project Structure](#project-structure)
10. [Development](#development)
11. [Testing](#testing)
12. [Troubleshooting](#troubleshooting)
13. [Contributing](#contributing)
14. [License](#license)

## 1. Overview
### Description
A fully local Python web application that manages HPL benchmark parameter sweeping on remote HPC clusters. The application runs entirely on your local machine, maintains persistent state across sessions, and allows you to submit jobs to remote clusters via SSH, leave while they run, and return later to analyze results.

### Key Benefits
- **100% Local**: No server deployment needed - runs entirely on your machine
- **Persistent State**: Close the app anytime and resume where you left off
- **Remote Execution**: Jobs run on HPC cluster while app can be closed
- **Automated parameter optimization for HPL benchmarks**
- **SSH-based remote cluster interaction**
- **Asynchronous job monitoring with state preservation**
- **Local performance visualization and analysis**
- **PDF report generation with optimal parameters**

## 2. Features
### Core Features
- **100% Local Execution**: Entire application runs on your local machine
- **State Persistence**: All job states, results, and configurations saved locally
- **Session Resumption**: Exit and return anytime - jobs continue running on cluster
- **SSH Authentication**: Secure connection to remote HPC clusters
- **SLURM Integration**: Automated job submission and monitoring
- **Parameter Sweep Engine**: Intelligent parameter space exploration
- **Result Collection**: Automated result gathering and parsing from remote cluster
- **Local Data Analysis**: Performance metrics calculation and optimization
- **Offline Visualization**: Interactive graphs generated locally
- **Report Generation**: PDF export with best parameters and graphs

### Workflow Features
- Module loading configuration
- Environment variable management
- Custom result directory selection (on remote cluster)
- Local CSV data storage
- Asynchronous job status tracking
- Batch job management
- **Persistent job tracking across sessions**
- **Automatic result synchronization**

## 3. Architecture
### System Architecture
```
        LOCAL MACHINE                           REMOTE HPC CLUSTER
┌──────────────────────────────┐              ┌─────────────────┐
│                              │              │                 │
│  ┌────────────────────┐      │     SSH      │   ┌─────────┐   │
│  │   Web Browser      │      │◀────────────▶│   │  SLURM  │   │
│  │  (localhost:8000)  │      │              │   │  Jobs   │   │
│  └──────────┬─────────┘      │              │   └─────────┘   │
│             │                │              │                 │
│  ┌──────────▼─────────┐      │              │   ┌─────────┐   │
│  │   Python Backend   │      │   Paramiko   │   │   HPL   │   │
│  │    (FastAPI)       │──────┼─────────────▶│   │  Runs   │   │
│  └──────────┬─────────┘      │              │   └─────────┘   │
│             │                │              │                 │
│  ┌──────────▼─────────┐      │              │   ┌─────────┐   │
│  │  Local SQLite DB   │      │    Results   │   │ Results │   │
│  │  (State Storage)   │◀─────┼──────────────│   │  Files  │   │
│  └────────────────────┘      │              │   └─────────┘   │
│                              │              │                 │
│  📁 Local Files:             │              └─────────────────┘
│   • Job states               │
│   • Cached results           │
│   • Generated graphs         │
│   • Configuration            │
└──────────────────────────────┘
```

### Technology Stack
- **Backend**: Python 3.8+ (All running locally)
  - FastAPI for local web server
  - Paramiko for SSH connections to remote cluster
  - Pandas for data processing
  - Matplotlib/Plotly for visualization
  - ReportLab for PDF generation
- **Frontend**: 
  - HTML5/CSS3 (served locally)
  - JavaScript (Vanilla or lightweight framework)
  - Bootstrap or Tailwind CSS
- **Storage**: SQLite for persistent local state storage
  - Job history and status
  - SSH session information
  - Cached results
  - User preferences

## 4. Prerequisites
### System Requirements
- Python 3.8 or higher
- Modern web browser
- Network access to HPC cluster
- SSH access credentials

### Python Dependencies
```
fastapi>=0.100.0
uvicorn>=0.23.0
paramiko>=3.0.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
plotly>=5.14.0
reportlab>=4.0.0
pydantic>=2.0.0
python-multipart>=0.0.6
aiofiles>=23.0.0
```

### HPC Cluster Requirements
- SLURM workload manager
- HPL (High Performance Linpack) installed
- Appropriate compute node access
- Module system (Lmod/Environment Modules)

## 5. Installation
### Quick Start (Local Installation)
```bash
# Clone the repository to your local machine
git clone https://github.com/username/hpl-sweep.git
cd hpl-sweep

# Create virtual environment (keeps everything local)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies locally
pip install -r requirements.txt

# Initialize local database
python scripts/init_db.py

# Run the application locally
python app.py

# Open browser to http://localhost:8000
# Application is now running entirely on your machine
```

### First Time Setup
```bash
# Create necessary local directories
mkdir -p data/{sessions,cached_results,generated_graphs,exports,backups}

# Set up configuration
cp config/app_config.yaml.example config/app_config.yaml
# Edit config/app_config.yaml with your preferences

# Test local server
python app.py --test
```

### No External Dependencies
- No cloud services required
- No external database needed
- No deployment necessary
- Everything runs on localhost

## 6. Configuration
### Configuration Files
- `config/app_config.yaml` - Application settings
- `config/hpl_params.yaml` - HPL parameter ranges
- `config/slurm_templates/` - SLURM script templates

### Environment Variables
```bash
HPL_SWEEP_PORT=8000
HPL_SWEEP_HOST=localhost
HPL_SWEEP_DEBUG=False
HPL_SWEEP_SECRET_KEY=your-secret-key
HPL_SWEEP_DB_PATH=./data/hpl_sweep.db
```

### HPL Parameter Configuration
Description of configurable HPL parameters:
- N (Problem size)
- NB (Block size)
- P x Q (Process grid)
- Memory usage limits
- Algorithm variants

### State Persistence Configuration
The application maintains state in a local SQLite database:
```yaml
# config/persistence.yaml
database:
  path: ./data/hpl_sweep.db
  backup_interval: 300  # seconds
  
cache:
  results_dir: ./data/cached_results/
  graphs_dir: ./data/generated_graphs/
  max_age_days: 30
  
session:
  auto_restore: true
  save_credentials: false  # for security
  ssh_timeout: 30
```

## 7. Usage
### Starting the Application
```bash
# Start local server (development mode)
python app.py --debug

# Start local server (normal mode)
python app.py

# The app automatically runs at http://localhost:8000
# All data is stored locally in ./data/ directory
```

### User Workflow
1. **Launch Application Locally**
   - Run `python app.py`
   - Open browser to `http://localhost:8000`
   - All previous sessions automatically restored
   
2. **SSH Login**
   - Enter cluster hostname
   - Provide username and password/key
   - Connection info saved locally for session resumption

3. **Configure HPL Environment**
   - Select/add required modules
   - Set environment variables
   - Specify XHPL binary path
   - **Configuration saved to local database**

4. **Set Job Parameters**
   - Number of nodes
   - CPUs per node
   - SLURM partition
   - Time limit
   - Result directory on cluster (optional)
   - **All parameters stored locally**

5. **Launch Parameter Sweep**
   - Review parameter space
   - Submit jobs to remote cluster
   - Job IDs saved to local database
   - **Can safely close application - jobs continue on cluster**

6. **Monitor Progress (Can Resume Later)**
   - Check job status anytime by reopening app
   - Application queries cluster for job updates
   - Progress automatically saved locally
   - **Exit and return days later if needed**

7. **Analyze Results (After Jobs Complete)**
   - Reopen application at any time
   - Click "Sync Results" to pull from cluster
   - Click "Generate Graphs" - processed locally
   - View performance metrics
   - Identify optimal parameters
   - **All results cached locally**

8. **Export Results**
   - Generate PDF report locally
   - Export CSV data from local storage
   - Save graphs as image files

### Session Persistence Features
- **Automatic State Recovery**: Reopening the app restores all previous job information
- **Job Status Synchronization**: Checks remote cluster for updates on reopening
- **Result Caching**: Downloaded results stored locally, no need to re-fetch
- **Configuration Memory**: All settings preserved between sessions
- **Multi-Session Support**: Track multiple parameter sweep sessions simultaneously

### Web Interface Screenshots
[Placeholder for UI screenshots showing session resumption]

## 8. API Documentation
### Local API Endpoints (All served from localhost:8000)
- `POST /api/auth/login` - SSH authentication to remote cluster
- `POST /api/auth/logout` - Clear SSH session (local)
- `GET /api/session/restore` - Restore previous session state
- `POST /api/jobs/submit` - Submit parameter sweep to cluster
- `GET /api/jobs/status/{job_id}` - Check job status on cluster
- `GET /api/jobs/sync` - Sync all job statuses from cluster
- `GET /api/results/{job_id}` - Retrieve results (from cache or cluster)
- `POST /api/results/sync-all` - Pull all completed results from cluster
- `POST /api/analysis/graphs` - Generate visualizations locally
- `GET /api/export/pdf` - Generate PDF report locally
- `GET /api/state/save` - Manual state save
- `GET /api/state/sessions` - List all saved sessions

### WebSocket Endpoints (Local)
- `/ws/job-status` - Real-time job status updates when app is open

### State Management
All API calls automatically persist state to local SQLite database:
- Job submissions and IDs
- SSH connection parameters (encrypted)
- HPL configurations
- Result cache references
- Graph generation history

## 9. Project Structure
```
hpl-sweep/
├── app.py                 # Main application entry point (local server)
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── config/               # Configuration files
│   ├── app_config.yaml
│   ├── hpl_params.yaml
│   ├── persistence.yaml  # State persistence settings
│   └── slurm_templates/
├── backend/              # Python backend code (runs locally)
│   ├── __init__.py
│   ├── api/             # Local API routes
│   │   ├── auth.py
│   │   ├── jobs.py
│   │   └── analysis.py
│   ├── core/            # Core functionality
│   │   ├── ssh_manager.py
│   │   ├── slurm_interface.py
│   │   ├── hpl_parser.py
│   │   ├── state_manager.py      # Session persistence
│   │   └── parameter_generator.py
│   ├── models/          # Data models
│   │   ├── job.py
│   │   ├── session.py   # Session state model
│   │   └── result.py
│   ├── services/        # Business logic
│   │   ├── sweep_service.py
│   │   ├── analysis_service.py
│   │   ├── sync_service.py       # Result synchronization
│   │   └── export_service.py
│   └── utils/           # Utility functions
│       ├── validators.py
│       └── helpers.py
├── frontend/            # Web frontend (served locally)
│   ├── index.html
│   ├── css/
│   ├── js/
│   └── assets/
├── data/                # LOCAL PERSISTENT STORAGE
│   ├── hpl_sweep.db    # SQLite database (job states, configs)
│   ├── sessions/        # Active session data
│   ├── cached_results/  # Downloaded HPL results
│   ├── generated_graphs/# Locally generated visualizations
│   ├── exports/         # PDF reports and CSV exports
│   └── backups/         # Database backups
├── tests/               # Test suite
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── docs/                # Additional documentation
    ├── user_guide.md
    ├── developer_guide.md
    └── api_reference.md
```

## 10. Development
### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run with hot reload
uvicorn app:app --reload --host localhost --port 8000

# Run tests
pytest tests/

# Code formatting
black backend/
flake8 backend/
```

### Adding New Features
- Guidelines for extending parameter sweep algorithms
- Adding new visualization types
- Implementing additional export formats

## 11. Testing
### Running Tests
```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Coverage report
pytest --cov=backend tests/
```

### Test Categories
- Unit tests for core functions
- Integration tests for SLURM interaction
- API endpoint tests
- Frontend UI tests (optional)

## 12. Local Execution & State Persistence Details
### How State Persistence Works
1. **SQLite Database**: All job information stored in `./data/hpl_sweep.db`
   - Job IDs and parameters
   - Submission timestamps
   - Last known status
   - Result file locations

2. **Session Management**:
   - Each parameter sweep creates a session ID
   - Sessions can be resumed even after system restart
   - Multiple concurrent sessions supported

3. **Result Caching**:
   - Results downloaded once and stored locally
   - Subsequent views use cached data
   - Cache invalidation configurable

4. **Automatic Recovery**:
   ```python
   # On application start:
   1. Load all active sessions from database
   2. Check remote cluster for job updates
   3. Sync any completed results
   4. Restore UI to last state
   ```

### Data Flow
```
1. Submit Jobs (Local → Remote):
   Local App → SSH → SLURM → Job Queue

2. Monitor Status (Periodic or On-Demand):
   Local App → SSH → squeue/sacct → Update Local DB

3. Retrieve Results (Remote → Local):
   Remote Results → SSH/SCP → Local Cache → Analysis

4. Generate Visualizations (All Local):
   Local Cache → Pandas → Matplotlib → Browser
```

### Benefits of Local Architecture
- **Privacy**: All data stays on your machine
- **Performance**: No network latency for analysis
- **Reliability**: No dependency on external services
- **Flexibility**: Run multiple instances for different clusters
- **Cost**: Zero hosting or cloud costs

## 13. Troubleshooting
### Common Issues
1. **SSH Connection Failures**
   - Verify credentials
   - Check network connectivity
   - Ensure SSH key permissions

2. **SLURM Job Submission Errors**
   - Validate SLURM configuration
   - Check partition availability
   - Verify resource limits

3. **HPL Execution Problems**
   - Confirm HPL installation
   - Check module availability
   - Verify MPI configuration

4. **Result Parsing Issues**
   - Validate HPL output format
   - Check file permissions
   - Ensure complete job execution

5. **Local State Issues**
   - Check database integrity: `python scripts/check_db.py`
   - Clear cache if corrupted: `rm -rf data/cached_results/*`
   - Restore from backup: `cp data/backups/latest.db data/hpl_sweep.db`

### Debug Mode
```bash
# Enable verbose logging
python app.py --debug --log-level DEBUG
```

### Log Files
- `logs/app.log` - Application logs
- `logs/ssh.log` - SSH connection logs
- `logs/slurm.log` - SLURM interaction logs
- `logs/state.log` - State persistence logs

## 14. Contributing
### Development Workflow
1. Fork the repository
2. Create feature branch
3. Make changes
4. Write tests
5. Submit pull request

### Code Style
- Follow PEP 8
- Use type hints
- Write docstrings
- Add unit tests

### Commit Message Format
```
type: brief description

Longer explanation if needed
```

## 14. License
MIT License (or your chosen license)

---

## Appendices

### A. HPL Parameter Descriptions
Detailed explanation of each HPL parameter and its impact on performance.

### B. SLURM Script Examples
Sample SLURM scripts for different cluster configurations.

### C. Performance Tuning Guide
Best practices for optimizing HPL performance.

### D. Security Considerations
- SSH key management
- Credential storage
- Data encryption

### E. Roadmap
- [ ] Phase 1: Core functionality
- [ ] Phase 2: Advanced visualizations
- [ ] Phase 3: Machine learning optimization
- [ ] Phase 4: Multi-cluster support

### F. Changelog
Version history and release notes.

### G. Acknowledgments
Credits and references.
