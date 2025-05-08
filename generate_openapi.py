#!/usr/bin/env python
"""
OpenAPI Schema Generator.

This script generates an OpenAPI schema from the FastAPI application
and writes it to a YAML file for use in documentation and security testing.
"""
import json
import os
import yaml
from pathlib import Path

from backend.main import app

def generate_openapi_yaml():
    """Generate OpenAPI schema in YAML format."""
    print("Generating OpenAPI schema...")
    
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    openapi_json = app.openapi()
    
    with open(docs_dir / "openapi.json", "w") as f:
        json.dump(openapi_json, f, indent=2)
    
    with open(docs_dir / "openapi.yaml", "w") as f:
        yaml.dump(openapi_json, f, default_flow_style=False)
    
    print(f"OpenAPI schema generated in {docs_dir}")
    print(f"- JSON: {docs_dir / 'openapi.json'}")
    print(f"- YAML: {docs_dir / 'openapi.yaml'}")

if __name__ == "__main__":
    generate_openapi_yaml() 