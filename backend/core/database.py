"""
Database management for HPL-Sweep
Handles SQLite database initialization and connections
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = "data/hpl_sweep.db"

def get_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allow dict-like access to rows
    return conn

def init_database():
    """Initialize the database with required tables"""

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    conn = get_connection()
    cursor = conn.cursor()

    # Sessions table - stores SSH connection info
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hostname TEXT NOT NULL,
            username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)

    # Jobs table - stores SLURM job information
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            job_id TEXT NOT NULL,
            nodes INTEGER,
            cpus_per_node INTEGER,
            partition TEXT,
            status TEXT DEFAULT 'PENDING',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    # Sweeps table - stores parameter sweep sessions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sweeps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            name TEXT,
            total_jobs INTEGER DEFAULT 0,
            completed_jobs INTEGER DEFAULT 0,
            nodes INTEGER,
            cpus_per_node INTEGER,
            partition TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    # HPL configurations table - stores HPL parameters for each job
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hpl_configurations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sweep_id INTEGER NOT NULL,
            slurm_job_id TEXT,
            n INTEGER NOT NULL,
            nb INTEGER NOT NULL,
            p INTEGER NOT NULL,
            q INTEGER NOT NULL,
            pfact TEXT DEFAULT 'R',
            nbmin INTEGER DEFAULT 4,
            rfact TEXT DEFAULT 'R',
            bcast TEXT DEFAULT '1',
            depth INTEGER DEFAULT 1,
            swap TEXT DEFAULT '2',
            l1 INTEGER DEFAULT 0,
            u INTEGER DEFAULT 0,
            equil INTEGER DEFAULT 1,
            align INTEGER DEFAULT 8,
            status TEXT DEFAULT 'PENDING',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (sweep_id) REFERENCES sweeps(id)
        )
    """)

    # Results table - stores HPL benchmark results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_id INTEGER NOT NULL,
            gflops REAL,
            time REAL,
            residual TEXT,
            passed BOOLEAN DEFAULT 0,
            error_message TEXT,
            job_info TEXT,
            error_content TEXT,
            retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (config_id) REFERENCES hpl_configurations(id)
        )
    """)

    conn.commit()
    conn.close()

    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_database()
