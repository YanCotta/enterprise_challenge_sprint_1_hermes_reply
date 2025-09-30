"""
Tests for API rate limiting functionality.

This module tests the rate limiting implementation for our ML endpoints,
specifically focusing on the /check_drift endpoint which has a 10 requests
per minute limit per API key.
"""

import asyncio
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import time

from apps.api.main import app
from core.config.settings import settings


@pytest.fixture(autouse=True)
def allow_test_api_keys(monkeypatch):
    """Ensure the test API keys are accepted by the application."""
    keys = [
        getattr(settings, "API_KEY", ""),
        "test-api-key-rate-limit",
        "test-key-1",
        "test-key-2",
        "unique-test-key",
    ]
    deduped = [key for key in dict.fromkeys(keys) if key]
    monkeypatch.setenv("API_KEYS", ",".join(deduped))
    yield


class TestRateLimiting:
    """Test suite for API rate limiting functionality."""

    @pytest.fixture
    def client(self):
        """Create a test client for rate limiting tests."""
        return TestClient(app)

    @pytest.fixture
    def async_client(self):
        """Create an async test client for rate limiting tests."""
        return AsyncClient(app=app, base_url="http://test")

    @pytest.fixture
    def sample_drift_payload(self):
        """Sample payload for drift check requests."""
        return {
            "sensor_id": "test_sensor_rate_limit",
            "window_minutes": 30,
            "p_value_threshold": 0.05,
            "min_samples": 10
        }

    @pytest.fixture
    def test_api_key(self):
        """Test API key for rate limiting tests."""
        return getattr(settings, "API_KEY", "test-api-key-rate-limit") or "test-api-key-rate-limit"

    def test_rate_limit_enforcement_with_api_key(self, client, sample_drift_payload, test_api_key):
        """
        Test that rate limits are enforced correctly for API key-based requests.
        
        This test:
        1. Makes 10 successful requests to /check_drift with the same API key
        2. Asserts that the 11th request is rejected with 429 Too Many Requests
        """
        headers = {"X-API-Key": test_api_key}
        endpoint = "/api/v1/ml/check_drift"
        
        successful_requests = 0
        rate_limited = False
        
        # Make 11 requests rapidly
        for i in range(11):
            response = client.post(endpoint, json=sample_drift_payload, headers=headers)
            
            if response.status_code == 429:
                rate_limited = True
                break
            elif response.status_code in [200, 400, 404, 500]:
                # Accept various status codes as "successful" from a rate limiting perspective
                # The endpoint might return errors due to missing data, but that's not a rate limit issue
                successful_requests += 1
            else:
                pytest.fail(f"Unexpected status code: {response.status_code}")
        
        # Verify that we made exactly 10 successful requests before being rate limited
        assert successful_requests == 10, f"Expected 10 successful requests, got {successful_requests}"
        assert rate_limited, "Expected to be rate limited after 10 requests, but wasn't"

    def test_rate_limit_per_api_key_isolation(self, client, sample_drift_payload):
        """
        Test that rate limits are isolated per API key.
        
        This test verifies that different API keys have separate rate limit counters.
        """
        endpoint = "/api/v1/ml/check_drift"
        
        # Test with first API key
        headers_key1 = {"X-API-Key": "test-key-1"}
        headers_key2 = {"X-API-Key": "test-key-2"}
        
        # Make 10 requests with key1
        for i in range(10):
            response = client.post(endpoint, json=sample_drift_payload, headers=headers_key1)
            # Accept any non-429 status as successful from rate limiting perspective
            assert response.status_code != 429, f"Key1 was rate limited at request {i+1}"
        
        # 11th request with key1 should be rate limited
        response_key1_limit = client.post(endpoint, json=sample_drift_payload, headers=headers_key1)
        assert response_key1_limit.status_code == 429, "Key1 should be rate limited on 11th request"
        
        # But key2 should still work (first request)
        response_key2_first = client.post(endpoint, json=sample_drift_payload, headers=headers_key2)
        assert response_key2_first.status_code != 429, "Key2 should not be rate limited on first request"

    def test_rate_limit_without_api_key_fallback_to_ip(self, client, sample_drift_payload):
        """
        Test that rate limiting falls back to IP address when no API key is provided.
        
        This test verifies that requests without API keys are still rate limited
        based on the client IP address.
        """
        endpoint = "/api/v1/ml/check_drift"
        
        successful_requests = 0
        rate_limited = False
        
        # Make requests without API key (should fallback to IP-based rate limiting)
        for i in range(11):
            response = client.post(endpoint, json=sample_drift_payload)
            
            if response.status_code == 429:
                rate_limited = True
                break
            elif response.status_code in [200, 400, 404, 500]:
                successful_requests += 1
            else:
                pytest.fail(f"Unexpected status code: {response.status_code}")
        
        assert successful_requests == 10, f"Expected 10 successful requests, got {successful_requests}"
        assert rate_limited, "Expected to be rate limited after 10 requests without API key"

    def test_rate_limit_response_format(self, client, sample_drift_payload, test_api_key):
        """
        Test that rate limit exceeded responses have the correct format.
        
        This test verifies that 429 responses include appropriate headers and error details.
        """
        headers = {"X-API-Key": test_api_key}
        endpoint = "/api/v1/ml/check_drift"
        
        # Exhaust the rate limit
        for i in range(10):
            client.post(endpoint, json=sample_drift_payload, headers=headers)
        
        # Make the rate-limited request
        response = client.post(endpoint, json=sample_drift_payload, headers=headers)
        
        # Verify rate limit response
        assert response.status_code == 429
        
        # Check for rate limit headers (slowapi typically adds these)
        response_data = response.json()
        assert "detail" in response_data
        
        # The error message should indicate rate limiting
        detail = response_data["detail"].lower()
        assert any(keyword in detail for keyword in ["rate", "limit", "exceeded", "too many"]), \
            f"Rate limit error message should mention rate limiting: {response_data['detail']}"

    @pytest.mark.asyncio
    async def test_rate_limit_time_window_reset(self, async_client, sample_drift_payload, test_api_key):
        """
        Test that rate limits reset after the time window expires.
        
        Note: This test is marked as slow and might be skipped in CI due to the time requirement.
        It verifies that after waiting for the rate limit window to expire, requests work again.
        """
        headers = {"X-API-Key": test_api_key}
        endpoint = "/api/v1/ml/check_drift"
        
        # Exhaust the rate limit
        for i in range(10):
            response = await async_client.post(endpoint, json=sample_drift_payload, headers=headers)
            if response.status_code == 429:
                break
        
        # Verify we're rate limited
        response = await async_client.post(endpoint, json=sample_drift_payload, headers=headers)
        assert response.status_code == 429, "Should be rate limited after 10 requests"
        
        # Wait for rate limit window to reset (61 seconds to be safe)
        # Note: In real tests, you might want to mock the time or use a shorter window
        print("Waiting 61 seconds for rate limit window to reset...")
        await asyncio.sleep(61)
        
        # Should be able to make requests again
        response = await async_client.post(endpoint, json=sample_drift_payload, headers=headers)
        assert response.status_code != 429, "Rate limit should have reset after waiting"

    def test_other_endpoints_not_rate_limited(self, client):
        """
        Test that endpoints without rate limiting are not affected.
        
        This test verifies that the rate limiting only applies to specific endpoints
        and doesn't affect other API endpoints.
        """
        # Test health endpoint (should not be rate limited)
        for i in range(15):  # More than the drift endpoint limit
            response = client.get("/health")
            assert response.status_code == 200, f"Health endpoint should not be rate limited, request {i+1}"
        
        # Test ML health endpoint (should not be rate limited)
        for i in range(15):
            response = client.get("/api/v1/ml/health")
            # Accept 200 or other valid responses, but not 429
            assert response.status_code != 429, f"ML health endpoint should not be rate limited, request {i+1}"


class TestRateLimitConfiguration:
    """Test suite for rate limiting configuration and edge cases."""

    def test_rate_limit_applies_only_to_check_drift(self, client):
        """
        Verify that rate limiting is applied only to the /check_drift endpoint.
        
        This test ensures that other ML endpoints are not accidentally rate limited.
        """
        # Test that other ML endpoints don't have the same rate limit
        sample_predict_payload = {
            "model_name": "test_model",
            "model_version": "1",
            "features": {"test_feature": 1.0}
        }
        
        headers = {"X-API-Key": "test-api-key"}
        
        # Make multiple requests to predict endpoint
        for i in range(15):  # More than drift limit
            response = client.post("/api/v1/ml/predict", json=sample_predict_payload, headers=headers)
            # Should not be rate limited (might get other errors, but not 429)
            assert response.status_code != 429, f"Predict endpoint should not be rate limited, request {i+1}"

    def test_rate_limit_identifier_function(self, client, sample_drift_payload):
        """
        Test the rate limit identifier function behavior.
        
        This test verifies that the identifier function correctly uses API keys
        when available and falls back to IP addresses appropriately.
        """
        endpoint = "/api/v1/ml/check_drift"
        
        # Test with API key - should use key-based identification
        headers_with_key = {"X-API-Key": "unique-test-key"}
        
        # Make 10 requests with API key
        for i in range(10):
            response = client.post(endpoint, json=sample_drift_payload, headers=headers_with_key)
            assert response.status_code != 429
        
        # 11th request should be rate limited
        response = client.post(endpoint, json=sample_drift_payload, headers=headers_with_key)
        assert response.status_code == 429
        
        # But a request without API key should still work (different identifier)
        response_no_key = client.post(endpoint, json=sample_drift_payload)
        # This might succeed or fail for other reasons, but shouldn't be rate limited initially
        # (since it's using IP-based identification which should have a fresh counter)
        if response_no_key.status_code == 429:
            pytest.fail("Request without API key was rate limited when it should use different identifier")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])