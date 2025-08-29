#!/usr/bin/env python3
"""
Validation script for CI environment configuration.
This script checks if all required services and configurations are available.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a required file exists."""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NOT FOUND")
        return False

def check_env_var(var_name: str, description: str) -> bool:
    """Check if an environment variable is set."""
    value = os.getenv(var_name)
    if value:
        print(f"✅ {description}: {var_name}={value}")
        return True
    else:
        print(f"❌ {description}: {var_name} - NOT SET")
        return False

def check_docker_service(service_name: str) -> bool:
    """Check if a Docker service is running."""
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "--services", "--filter", "status=running"],
            capture_output=True,
            text=True,
            check=True
        )
        running_services = result.stdout.strip().split('\n')
        if service_name in running_services:
            print(f"✅ Docker service: {service_name} is running")
            return True
        else:
            print(f"❌ Docker service: {service_name} is not running")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Error checking Docker service {service_name}: {e}")
        return False

def main():
    """Run all validation checks."""
    print("🔍 Validating CI Environment Configuration...")
    print("=" * 50)
    
    checks_passed = 0
    total_checks = 0
    
    # Check required files
    file_checks = [
        (".env", "Environment file"),
        ("docker-compose.yml", "Docker Compose file"),
        ("pyproject.toml", "Python project file"),
        ("smart-maintenance-saas/.env", "App environment file"),
    ]
    
    for filepath, description in file_checks:
        total_checks += 1
        if check_file_exists(filepath, description):
            checks_passed += 1
    
    # Check environment variables
    env_checks = [
        ("POSTGRES_DB", "Database name"),
        ("POSTGRES_USER", "Database user"),
        ("POSTGRES_PASSWORD", "Database password"),
        ("MLFLOW_TRACKING_URI", "MLflow tracking URI"),
    ]
    
    for var_name, description in env_checks:
        total_checks += 1
        if check_env_var(var_name, description):
            checks_passed += 1
    
    # Check Docker services
    service_checks = ["db", "mlflow"]
    
    for service in service_checks:
        total_checks += 1
        if check_docker_service(service):
            checks_passed += 1
    
    print("=" * 50)
    print(f"📊 Validation Results: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("🎉 All validation checks passed! CI environment is ready.")
        sys.exit(0)
    else:
        print("⚠️  Some validation checks failed. Please review the configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()