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

    # Results table - stores HPL benchmark results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            n INTEGER,
            nb INTEGER,
            p INTEGER,
            q INTEGER,
            gflops REAL,
            time REAL,
            retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)

    conn.commit()
    conn.close()

    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_database()
