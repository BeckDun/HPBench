# HPBench
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
Brief description of what the application does - automated HPL parameter sweeping through SLURM, result collection, analysis, and visualization through a local web interface.

### Key Benefits
- Automated parameter optimization for HPL benchmarks
- SSH-based remote cluster interaction
- Real-time job monitoring
- Performance visualization and analysis
- PDF report generation

## 2. Features
### Core Features
- **SSH Authentication**: Secure login to HPC clusters
- **SLURM Integration**: Automated job submission and monitoring
- **Parameter Sweep Engine**: Intelligent parameter space exploration
- **Result Collection**: Automated result gathering and parsing
- **Data Analysis**: Performance metrics calculation and optimization
- **Visualization**: Interactive graphs and charts
- **Report Generation**: PDF export with best parameters and graphs

### Workflow Features
- Module loading configuration
- Environment variable management
- Custom result directory selection
- CSV data export
- Real-time job status tracking
- Batch job management

## 3. Architecture
### System Architecture
```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   Web Frontend  │────▶│  Python      │────▶│  HPC        │
│   (HTML/JS)     │◀────│  Backend     │◀────│  Cluster    │
└─────────────────┘     │  (FastAPI)   │     │  (SLURM)    │
                        └──────────────┘     └─────────────┘
                               │
                        ┌──────▼──────┐
                        │  Database/  │
                        │  Storage     │
                        └─────────────┘
```

### Technology Stack
- **Backend**: Python 3.8+
  - FastAPI/Flask for API
  - Paramiko for SSH connections
  - Pandas for data processing
  - Matplotlib/Plotly for visualization
  - ReportLab for PDF generation
- **Frontend**: 
  - HTML5/CSS3
  - JavaScript (Vanilla or React/Vue optional)
  - Bootstrap or Tailwind CSS
- **Storage**: SQLite/JSON for local data

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
### Quick Start
```bash
# Clone the repository
git clone https://github.com/username/hpl-sweep.git
cd hpl-sweep

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

### Docker Installation (Optional)
```bash
docker build -t hpl-sweep .
docker run -p 8000:8000 hpl-sweep
```

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
```

### HPL Parameter Configuration
Description of configurable HPL parameters:
- N (Problem size)
- NB (Block size)
- P x Q (Process grid)
- Memory usage limits
- Algorithm variants

## 7. Usage
### Starting the Application
```bash
# Development mode
python app.py --debug

# Production mode
python app.py --host 0.0.0.0 --port 8000
```

### User Workflow
1. **Launch Application**
   - Navigate to `http://localhost:8000`
   
2. **SSH Login**
   - Enter cluster hostname
   - Provide username and password/key
   - Verify connection

3. **Configure HPL Environment**
   - Select/add required modules
   - Set environment variables
   - Specify XHPL binary path

4. **Set Job Parameters**
   - Number of nodes
   - CPUs per node
   - SLURM partition
   - Time limit
   - Result directory (optional)

5. **Launch Parameter Sweep**
   - Review parameter space
   - Submit jobs
   - Monitor progress

6. **Analyze Results**
   - Wait for job completion
   - Click "Generate Graphs"
   - View performance metrics
   - Identify optimal parameters

7. **Export Results**
   - Generate PDF report
   - Download CSV data
   - Save graphs

### Web Interface Screenshots
[Placeholder for UI screenshots]

## 8. API Documentation
### API Endpoints
- `POST /api/auth/login` - SSH authentication
- `POST /api/jobs/submit` - Submit parameter sweep
- `GET /api/jobs/status/{job_id}` - Check job status
- `GET /api/results/{job_id}` - Retrieve results
- `POST /api/analysis/graphs` - Generate visualizations
- `GET /api/export/pdf` - Generate PDF report

### WebSocket Endpoints
- `/ws/job-status` - Real-time job status updates

## 9. Project Structure
```
hpl-sweep/
├── app.py                 # Main application entry point
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── config/               # Configuration files
│   ├── app_config.yaml
│   ├── hpl_params.yaml
│   └── slurm_templates/
├── backend/              # Python backend code
│   ├── __init__.py
│   ├── api/             # API routes
│   │   ├── auth.py
│   │   ├── jobs.py
│   │   └── analysis.py
│   ├── core/            # Core functionality
│   │   ├── ssh_manager.py
│   │   ├── slurm_interface.py
│   │   ├── hpl_parser.py
│   │   └── parameter_generator.py
│   ├── models/          # Data models
│   │   ├── job.py
│   │   └── result.py
│   ├── services/        # Business logic
│   │   ├── sweep_service.py
│   │   ├── analysis_service.py
│   │   └── export_service.py
│   └── utils/           # Utility functions
│       ├── validators.py
│       └── helpers.py
├── frontend/            # Web frontend
│   ├── index.html
│   ├── css/
│   ├── js/
│   └── assets/
├── data/                # Local data storage
│   ├── jobs/
│   ├── results/
│   └── exports/
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

## 12. Troubleshooting
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

### Debug Mode
```bash
# Enable verbose logging
python app.py --debug --log-level DEBUG
```

### Log Files
- `logs/app.log` - Application logs
- `logs/ssh.log` - SSH connection logs
- `logs/slurm.log` - SLURM interaction logs

## 13. Contributing
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
