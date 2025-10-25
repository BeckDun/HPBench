"""
HPL-Sweep: HPL Parameter Sweep Web Application
Main application entry point
"""
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Import API routers
from backend.api import auth, cluster, jobs

# Create FastAPI app
app = FastAPI(title="HPL-Sweep", description="HPL Parameter Sweep Application", version="0.1.0")

# Include API routers
app.include_router(auth.router)
app.include_router(cluster.router)
app.include_router(jobs.router)

# Mount frontend static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def root():
    """Serve the main frontend page"""
    return FileResponse("frontend/index.html")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "HPL-Sweep is running"}

if __name__ == "__main__":
    print("Starting HPL-Sweep application...")
    print("Open your browser to http://localhost:8000")
    uvicorn.run("app:app", host="localhost", port=8000, reload=True)
