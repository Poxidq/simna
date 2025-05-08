#!/usr/bin/env python3
"""
Type checking script.

This script runs the mypy type checker on selected modules to ensure
that the type annotations are correct and consistent.
"""
import os
import subprocess
import sys
from typing import List, Tuple


def run_mypy(targets: List[str], options: List[str]) -> Tuple[int, str]:
    """
    Run mypy on the specified targets with the given options.
    
    Args:
        targets: List of modules or files to check
        options: List of mypy options
        
    Returns:
        Tuple[int, str]: Return code and output
    """
    cmd = [sys.executable, "-m", "mypy"] + options + targets
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(
        cmd, 
        capture_output=True, 
        text=True,
        encoding="utf-8"
    )
    
    return result.returncode, result.stdout + result.stderr


def get_strict_options() -> List[str]:
    """
    Get options for strict type checking.
    
    Returns:
        List[str]: List of strict type checking options
    """
    return [
        "--ignore-missing-imports",
        "--disallow-untyped-defs",
        "--disallow-incomplete-defs",
        "--check-untyped-defs",
        "--disallow-untyped-decorators",
        "--no-implicit-optional",
        "--warn-redundant-casts",
        "--warn-unused-ignores",
        "--warn-return-any",
        "--no-implicit-reexport",
    ]


def check_backend_core() -> None:
    """Check backend core modules."""
    print("\n=== Checking Backend Core ===")
    
    targets = [
        "backend/app/core/security.py",
        "backend/app/services/translation.py",
        "backend/app/core/config.py",
    ]
    
    options = get_strict_options()
    
    code, output = run_mypy(targets, options)
    print(output)
    
    if code == 0:
        print("Backend core check: SUCCESS")
    else:
        print(f"Backend core check: FAILED with code {code}")


def check_backend_api() -> None:
    """Check backend API modules."""
    print("\n=== Checking Backend API ===")
    
    targets = [
        "backend/app/api/endpoints/auth.py",
        "backend/app/api/endpoints/notes.py",
        "backend/app/api/schemas.py",
        "backend/app/api/api.py",
    ]
    
    options = get_strict_options()
    
    code, output = run_mypy(targets, options)
    print(output)
    
    if code == 0:
        print("Backend API check: SUCCESS")
    else:
        print(f"Backend API check: FAILED with code {code}")


def check_backend_db() -> None:
    """Check backend database modules."""
    print("\n=== Checking Backend Database ===")
    
    targets = [
        "backend/app/db/models.py",
        "backend/app/db/database.py",
    ]
    
    options = get_strict_options()
    
    code, output = run_mypy(targets, options)
    print(output)
    
    if code == 0:
        print("Backend database check: SUCCESS")
    else:
        print(f"Backend database check: FAILED with code {code}")


def check_frontend_services() -> None:
    """Check frontend service modules."""
    print("\n=== Checking Frontend Services ===")
    
    targets = [
        "frontend/services/notes_service.py",
        "frontend/services/auth_service.py",
        "frontend/services/api.py",
    ]
    
    options = get_strict_options()
    
    code, output = run_mypy(targets, options)
    print(output)
    
    if code == 0:
        print("Frontend services check: SUCCESS")
    else:
        print(f"Frontend services check: FAILED with code {code}")


def check_frontend_components() -> None:
    """Check frontend component modules."""
    print("\n=== Checking Frontend Components ===")
    
    targets = [
        "frontend/components/auth.py",
        "frontend/components/notes.py",
    ]
    
    options = get_strict_options()
    
    code, output = run_mypy(targets, options)
    print(output)
    
    if code == 0:
        print("Frontend components check: SUCCESS")
    else:
        print(f"Frontend components check: FAILED with code {code}")


def check_frontend_app() -> None:
    """Check frontend app module."""
    print("\n=== Checking Frontend App ===")
    
    targets = [
        "frontend/app.py",
        "frontend/state/app_state.py",
        "frontend/utils/theme.py",
    ]
    
    options = get_strict_options()
    
    code, output = run_mypy(targets, options)
    print(output)
    
    if code == 0:
        print("Frontend app check: SUCCESS")
    else:
        print(f"Frontend app check: FAILED with code {code}")


def check_backend_main() -> None:
    """Check backend main module."""
    print("\n=== Checking Backend Main ===")
    
    targets = [
        "backend/main.py",
    ]
    
    options = get_strict_options()
    
    code, output = run_mypy(targets, options)
    print(output)
    
    if code == 0:
        print("Backend main check: SUCCESS")
    else:
        print(f"Backend main check: FAILED with code {code}")


def main() -> None:
    """Run type checking on selected modules."""
    # Check if mypy is installed
    try:
        subprocess.run(
            [sys.executable, "-m", "mypy", "--version"],
            capture_output=True,
            check=True
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Error: mypy is not installed. Please install it with:")
        print("  pip install mypy")
        return

    # Change to workspace root
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run checks
    check_backend_core()
    check_backend_api()
    check_backend_db()
    check_backend_main()
    check_frontend_services()
    check_frontend_components()
    check_frontend_app()


if __name__ == "__main__":
    main() 