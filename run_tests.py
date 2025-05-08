#!/usr/bin/env python
"""
Test runner script.

This script runs tests and generates coverage reports for the application.
"""
import os
import subprocess
import sys

def run_tests():
    """Run pytest with coverage."""
    # Set testing environment
    os.environ["TESTING"] = "True"
    
    # Run tests with coverage
    cmd = [
        "pytest", 
        "backend/app/tests/", 
        "-v", 
        "--cov=backend", 
        "--cov-report=term", 
        "--cov-report=html"
    ]
    
    result = subprocess.run(cmd)
    return result.returncode

def run_flake8():
    """Run flake8 for PEP8 compliance."""
    cmd = ["flake8", "backend", "frontend"]
    result = subprocess.run(cmd)
    return result.returncode

def run_bandit():
    """Run bandit for security checks."""
    cmd = ["bandit", "-r", "backend"]
    result = subprocess.run(cmd)
    return result.returncode

if __name__ == "__main__":
    print("===== Running tests with coverage =====")
    test_result = run_tests()
    
    print("\n===== Running PEP8 compliance check =====")
    flake8_result = run_flake8()
    
    print("\n===== Running security check =====")
    bandit_result = run_bandit()
    
    # Print summary
    print("\n===== Summary =====")
    print(f"Tests: {'PASSED' if test_result == 0 else 'FAILED'}")
    print(f"PEP8: {'PASSED' if flake8_result == 0 else 'FAILED'}")
    print(f"Security: {'PASSED' if bandit_result == 0 else 'FAILED'}")
    
    # Exit with appropriate code
    sys.exit(max(test_result, flake8_result, bandit_result)) 