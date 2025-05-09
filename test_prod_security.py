#!/usr/bin/env python
"""
Production Security Test Script.

This script tests the application's behavior in production mode,
especially the cookie key security features.
"""
import os
import subprocess
import sys
import time


def run_with_env(env_vars):
    """Run the app with specific environment variables to test security features."""
    env = os.environ.copy()
    env.update(env_vars)
    
    print(f"\n🔒 Testing with environment: {env_vars}")
    
    try:
        # Run the app with a timeout to catch any exit code
        result = subprocess.run(
            ["poetry", "run", "streamlit", "run", "frontend/app.py"],
            env=env,
            capture_output=True,
            text=True,
            timeout=10  # Time out after 10 seconds
        )
        
        # Print the output
        print(f"Exit code: {result.returncode}")
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        # If the app runs without exiting, it means it didn't trigger our security exit
        print("App ran without security errors (timeout)")
        return True


def main():
    """Run security tests in different environments."""
    print("🔐 Testing Notes App Cookie Key Security in Production Mode")
    print("=" * 70)
    
    # Test 1: Development mode with default key (should run)
    print("\n\n🧪 TEST 1: Development mode with default key")
    dev_success = run_with_env({
        "ENVIRONMENT": "development",
        "COOKIE_KEY": ""  # Empty to use default
    })
    
    # Test 2: Production mode with default key, no auto-generation (should exit)
    print("\n\n🧪 TEST 2: Production mode with default key, no auto-generation")
    prod_no_gen_success = run_with_env({
        "ENVIRONMENT": "production",
        "COOKIE_KEY": "",  # Empty to use default
        "ALLOW_GENERATE_COOKIE_KEY": "false"
    })
    
    # Test 3: Production mode with default key but allow generation (should run)
    print("\n\n🧪 TEST 3: Production mode with default key but allow generation")
    prod_with_gen_success = run_with_env({
        "ENVIRONMENT": "production",
        "COOKIE_KEY": "",  # Empty to use default
        "ALLOW_GENERATE_COOKIE_KEY": "true"
    })
    
    # Test 4: Production mode with custom key (should run)
    print("\n\n🧪 TEST 4: Production mode with custom key")
    prod_with_key_success = run_with_env({
        "ENVIRONMENT": "production",
        "COOKIE_KEY": "my_secure_production_key_for_testing"
    })
    
    # Summarize results
    print("\n\n📊 SUMMARY OF RESULTS")
    print("=" * 70)
    print(f"Development mode with default key: {'✅ PASS' if dev_success else '❌ FAIL'}")
    print(f"Production mode with default key: {'❌ PASS' if not prod_no_gen_success else '✅ FAIL'}")
    print(f"Production with auto-generation: {'✅ PASS' if prod_with_gen_success else '❌ FAIL'}")
    print(f"Production with custom key: {'✅ PASS' if prod_with_key_success else '❌ FAIL'}")
    
    
if __name__ == "__main__":
    main() 