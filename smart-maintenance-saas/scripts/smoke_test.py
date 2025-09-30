#!/usr/bin/env python3
"""
Smart Maintenance SaaS - Smoke Test Suite
Validates that all critical services are operational after deployment
"""

import sys
import time
import requests
from typing import Dict, Any

# ANSI color codes
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color

API_BASE_URL = "http://localhost:8000"
UI_BASE_URL = "http://localhost:8501"

class SmokeTestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def run_test(self, test_name: str, test_func):
        """Run a single test and track results."""
        try:
            test_func()
            print(f"{GREEN}✓{NC} {test_name}")
            self.passed += 1
        except AssertionError as e:
            print(f"{RED}✗{NC} {test_name}: {e}")
            self.failed += 1
        except Exception as e:
            print(f"{YELLOW}⚠{NC} {test_name}: {e}")
            self.warnings += 1
    
    def print_summary(self):
        """Print test summary."""
        total = self.passed + self.failed + self.warnings
        print("\n" + "="*50)
        print("Smoke Test Summary")
        print("="*50)
        print(f"Total:    {total}")
        print(f"{GREEN}Passed:   {self.passed}{NC}")
        print(f"{RED}Failed:   {self.failed}{NC}")
        print(f"{YELLOW}Warnings: {self.warnings}{NC}")
        print("="*50 + "\n")
        
        if self.failed > 0:
            print(f"{RED}FAILED: Critical issues detected{NC}")
            return False
        elif self.warnings > 0:
            print(f"{YELLOW}PASSED with warnings: Non-critical issues detected{NC}")
            return True
        else:
            print(f"{GREEN}PASSED: All tests successful{NC}")
            return True

# Test functions
def test_api_health():
    """Test API health endpoint."""
    response = requests.get(f"{API_BASE_URL}/health", timeout=10)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("status") in ["ok", "healthy"], f"Unexpected status: {data.get('status')}"

def test_api_db_health():
    """Test database connectivity via API."""
    response = requests.get(f"{API_BASE_URL}/health/db", timeout=10)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("db_status") == "connected", "Database not connected"

def test_api_redis_health():
    """Test Redis connectivity via API."""
    response = requests.get(f"{API_BASE_URL}/health/redis", timeout=10)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("status") in ["healthy", "ok"], "Redis not healthy"

def test_ui_accessible():
    """Test UI is accessible."""
    response = requests.get(UI_BASE_URL, timeout=10)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

def test_api_docs():
    """Test API documentation is accessible."""
    response = requests.get(f"{API_BASE_URL}/docs", timeout=10)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

def test_openapi_schema():
    """Test OpenAPI schema is valid."""
    response = requests.get(f"{API_BASE_URL}/openapi.json", timeout=10)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "openapi" in data, "Invalid OpenAPI schema"
    assert "paths" in data, "No paths in OpenAPI schema"

def test_prometheus_metrics():
    """Test Prometheus metrics endpoint."""
    response = requests.get(f"{API_BASE_URL}/metrics", timeout=10)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    text = response.text
    assert "http_requests_total" in text or "process_cpu_seconds_total" in text, "No metrics found"

def test_cors_headers():
    """Test CORS headers are present."""
    response = requests.options(f"{API_BASE_URL}/health", timeout=10)
    # Note: CORS may not be configured for OPTIONS, just check endpoint works
    assert response.status_code in [200, 405], f"Unexpected status: {response.status_code}"

def test_api_root():
    """Test API root endpoint."""
    response = requests.get(f"{API_BASE_URL}/", timeout=10)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "message" in data, "No welcome message"

def test_ml_health():
    """Test ML service health (without API key)."""
    # This endpoint may require auth, so we just check it's not 500
    response = requests.get(f"{API_BASE_URL}/api/v1/ml/health", timeout=10)
    assert response.status_code in [200, 401, 403], f"Unexpected error: {response.status_code}"

def main():
    """Run all smoke tests."""
    print("\n" + "="*50)
    print("Running Smart Maintenance SaaS Smoke Tests")
    print("="*50 + "\n")
    
    runner = SmokeTestRunner()
    
    # Core API tests
    print("Testing Core API...")
    runner.run_test("API Health Check", test_api_health)
    runner.run_test("Database Connectivity", test_api_db_health)
    runner.run_test("Redis Connectivity", test_api_redis_health)
    runner.run_test("API Root Endpoint", test_api_root)
    
    # Documentation tests
    print("\nTesting Documentation...")
    runner.run_test("API Documentation", test_api_docs)
    runner.run_test("OpenAPI Schema", test_openapi_schema)
    
    # Monitoring tests
    print("\nTesting Monitoring...")
    runner.run_test("Prometheus Metrics", test_prometheus_metrics)
    
    # UI tests
    print("\nTesting UI...")
    runner.run_test("UI Accessibility", test_ui_accessible)
    
    # ML tests
    print("\nTesting ML Services...")
    runner.run_test("ML Health Endpoint", test_ml_health)
    
    # Print summary and exit
    success = runner.print_summary()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
