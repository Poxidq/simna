#!/bin/bash

# Exit on any error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}===== Running Quality Checks for Notes App =====${NC}"

# 1. Code Style Checks
echo -e "\n${YELLOW}===== Running PEP8 Style Checks =====${NC}"
poetry run flake8 frontend backend --count --select=E9,F63,F7,F82 --show-source --statistics
poetry run flake8 frontend backend --count --max-complexity=10 --max-line-length=100 --statistics

# 2. Code Formatting
echo -e "\n${YELLOW}===== Running Code Formatting Checks =====${NC}"
poetry run black --check frontend backend
poetry run isort --check-only frontend backend

# 3. Documentation Coverage - use our custom script instead of interrogate
echo -e "\n${YELLOW}===== Checking Documentation Coverage =====${NC}"
poetry run pydocstyle frontend backend || echo -e "${RED}Some docstring issues found${NC}"
python check_docstrings.py frontend backend --min-percentage=90

# 4. Maintainability Index Check - use our custom script instead of radon
echo -e "\n${YELLOW}===== Checking Code Maintainability =====${NC}"
python check_maintainability.py frontend backend --min-mi=70

# 5. Run Tests with Coverage
echo -e "\n${YELLOW}===== Running Tests with Coverage =====${NC}"
poetry run pytest backend/tests -v --cov=frontend --cov=backend --cov-report=term-missing

# 6. Security Checks
echo -e "\n${YELLOW}===== Running Security Checks =====${NC}"
# Install bandit if missing
pip show bandit > /dev/null 2>&1 || pip install bandit
python -m bandit -r frontend backend || echo -e "${RED}Security issues found${NC}"

echo -e "\n${GREEN}===== Quality checks completed! =====${NC}" 
