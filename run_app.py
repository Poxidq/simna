#!/usr/bin/env python
"""
Application runner script.

This script runs the backend and frontend applications.
"""
import os
import subprocess
import sys
import time
from multiprocessing import Process

def run_backend():
    """Run the backend FastAPI application."""
    print("Starting backend server...")
    os.environ["PYTHONPATH"] = os.getcwd()
    cmd = ["uvicorn", "backend.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    subprocess.run(cmd)

def run_frontend():
    """Run the frontend Streamlit application."""
    print("Starting frontend application...")
    os.environ["PYTHONPATH"] = os.getcwd()
    cmd = ["streamlit", "run", "frontend/app.py"]
    subprocess.run(cmd)

if __name__ == "__main__":
    # Start backend in a separate process
    backend_process = Process(target=run_backend)
    backend_process.start()
    
    # Wait a moment for backend to start
    time.sleep(2)
    
    try:
        # Start frontend
        frontend_process = Process(target=run_frontend)
        frontend_process.start()
        
        # Wait for frontend to complete
        frontend_process.join()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Terminate backend process
        backend_process.terminate()
        backend_process.join()
        print("Application stopped") 