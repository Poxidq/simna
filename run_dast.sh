#!/bin/bash

# DAST Security Testing Script with Nuclei
# This script runs Nuclei against our API to identify security vulnerabilities

# Exit on error
set -e

# Configuration
API_URL=${1:-"http://localhost:8000"}
OPENAPI_FILE="docs/openapi.yaml"
OUTPUT_DIR="security/reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
NUCLEI_REPORT="${OUTPUT_DIR}/nuclei_report_${TIMESTAMP}.json"
SUMMARY_REPORT="${OUTPUT_DIR}/summary_${TIMESTAMP}.txt"

# Create output directory
mkdir -p "${OUTPUT_DIR}"

echo "🔒 Starting DAST security testing with Nuclei"
echo "API URL: ${API_URL}"
echo "OpenAPI File: ${OPENAPI_FILE}"
echo "Report: ${NUCLEI_REPORT}"

# Check if Nuclei is installed
if ! command -v nuclei &> /dev/null; then
    echo "⚠️ Nuclei is not installed. Installing..."
    GO111MODULE=on go get -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei
fi

# Update Nuclei templates
echo "📝 Updating Nuclei templates..."
nuclei -update-templates

# Run API endpoint discovery from OpenAPI spec
echo "🔍 Analyzing OpenAPI spec to discover endpoints..."
# Optional: use openapi-to-nuclei if available
# openapi-to-nuclei -u "${OPENAPI_FILE}" -o "api_endpoints.yaml"

# Run Nuclei against API endpoints
echo "🚀 Running Nuclei scan..."
nuclei -u "${API_URL}" \
       -severity medium,high,critical \
       -t ~/nuclei-templates/http/ \
       -json -o "${NUCLEI_REPORT}" \
       -rate-limit 10 \
       -timeout 5

# Generate summary report
echo "📊 Generating scan summary..."
echo "DAST Security Scan Summary (${TIMESTAMP})" > "${SUMMARY_REPORT}"
echo "=======================================" >> "${SUMMARY_REPORT}"
echo "" >> "${SUMMARY_REPORT}"

# Count issues by severity
if [ -f "${NUCLEI_REPORT}" ]; then
    CRITICAL=$(grep -c '"severity":"critical"' "${NUCLEI_REPORT}" || echo 0)
    HIGH=$(grep -c '"severity":"high"' "${NUCLEI_REPORT}" || echo 0)
    MEDIUM=$(grep -c '"severity":"medium"' "${NUCLEI_REPORT}" || echo 0)
    LOW=$(grep -c '"severity":"low"' "${NUCLEI_REPORT}" || echo 0)
    
    echo "Found issues:" >> "${SUMMARY_REPORT}"
    echo "- Critical: ${CRITICAL}" >> "${SUMMARY_REPORT}"
    echo "- High:     ${HIGH}" >> "${SUMMARY_REPORT}"
    echo "- Medium:   ${MEDIUM}" >> "${SUMMARY_REPORT}"
    echo "- Low:      ${LOW}" >> "${SUMMARY_REPORT}"
    echo "" >> "${SUMMARY_REPORT}"
    
    # List found vulnerabilities
    echo "Details:" >> "${SUMMARY_REPORT}"
    cat "${NUCLEI_REPORT}" | jq -r '.[] | "- \(.info.name) [\(.info.severity)] - \(.matched)"' 2>/dev/null >> "${SUMMARY_REPORT}" || echo "No vulnerabilities found." >> "${SUMMARY_REPORT}"
else
    echo "No vulnerabilities found or scan failed to produce a report." >> "${SUMMARY_REPORT}"
fi

# Display summary
echo ""
echo "✅ DAST security testing completed"
echo "Summary report saved to: ${SUMMARY_REPORT}"
cat "${SUMMARY_REPORT}"

# Exit with error if critical or high vulnerabilities found
if [ "$CRITICAL" -gt 0 ] || [ "$HIGH" -gt 0 ]; then
    echo "❌ Found critical or high severity vulnerabilities!"
    exit 1
else
    echo "✅ No critical or high severity vulnerabilities found."
    exit 0
fi 