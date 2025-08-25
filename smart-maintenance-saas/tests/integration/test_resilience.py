"""
Resilience integration tests using Toxiproxy for chaos engineering.

These tests simulate adverse network conditions to verify our system's
fault tolerance and graceful degradation capabilities.
"""

import asyncio
import pytest
import httpx


class TestResilience:
    """
    Integration tests for system resilience under adverse network conditions.
    
    Uses Toxiproxy to simulate:
    - Complete service unavailability (disable proxy)
    - Network latency (latency toxic)
    - Packet loss and connection issues
    """
    
    @pytest.fixture(scope="class")
    async def toxiproxy_client(self):
        """Initialize Toxiproxy client and set up proxies via HTTP API."""
        toxiproxy_url = "http://localhost:8474"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Wait for Toxiproxy to be ready
            for _ in range(30):  # 30 second timeout
                try:
                    response = await client.get(f"{toxiproxy_url}/version")
                    if response.status_code == 200:
                        break
                except Exception:
                    pass
                await asyncio.sleep(1)
            else:
                pytest.skip("Toxiproxy not available")
            
            # Create proxies for our services if they don't exist
            proxies = {}
            
            # Create Redis proxy (api -> toxiproxy:6380 -> redis:6379)
            try:
                redis_proxy_data = {
                    "name": "redis",
                    "listen": "0.0.0.0:6380",
                    "upstream": "redis:6379",
                    "enabled": True
                }
                response = await client.post(f"{toxiproxy_url}/proxies", json=redis_proxy_data)
                if response.status_code in [200, 201, 409]:  # 409 = already exists
                    proxies["redis"] = "redis"
            except Exception:
                pass
            
            # Create PostgreSQL proxy (api -> toxiproxy:5433 -> db:5432)
            try:
                db_proxy_data = {
                    "name": "postgres",
                    "listen": "0.0.0.0:5433",
                    "upstream": "db:5432",
                    "enabled": True
                }
                response = await client.post(f"{toxiproxy_url}/proxies", json=db_proxy_data)
                if response.status_code in [200, 201, 409]:  # 409 = already exists
                    proxies["postgres"] = "postgres"
            except Exception:
                pass
            
            # Ensure proxies are enabled
            for proxy_name in proxies.keys():
                try:
                    await client.post(f"{toxiproxy_url}/proxies/{proxy_name}/enable")
                except Exception:
                    pass
            
            yield {
                "url": toxiproxy_url,
                "client": client,
                "proxies": proxies
            }
            
            # Cleanup: Remove all toxics and ensure proxies are enabled
            for proxy_name in proxies.keys():
                try:
                    # Remove all toxics
                    await client.delete(f"{toxiproxy_url}/proxies/{proxy_name}/toxics")
                    # Enable proxy
                    await client.post(f"{toxiproxy_url}/proxies/{proxy_name}/enable")
                except Exception:
                    pass
    
    async def test_redis_unavailability_graceful_degradation(self, toxiproxy_client):
        """
        Test system graceful degradation when Redis is unavailable.
        
        Verifies:
        - API continues to function without Redis
        - Data ingestion works with degraded performance
        - System recovers when Redis comes back online
        """
        toxiproxy_url = toxiproxy_client["url"]
        client = toxiproxy_client["client"]
        
        if "redis" not in toxiproxy_client["proxies"]:
            pytest.skip("Redis proxy not available")
        
        # Simulate Redis unavailability by disabling the proxy
        try:
            await client.post(f"{toxiproxy_url}/proxies/redis/disable")
            
            # Test API health check still works
            async with httpx.AsyncClient(timeout=30.0) as api_client:
                response = await api_client.get("http://localhost:8000/health")
                assert response.status_code == 200
            
            # Test data ingestion works (should degrade gracefully)
            sensor_data = {
                "sensor_id": "TEST_RESILIENCE_REDIS_001",
                "timestamp": "2024-01-15T12:00:00Z",
                "values": {"temperature": 25.5, "vibration": 0.02}
            }
            
            async with httpx.AsyncClient(timeout=30.0) as api_client:
                response = await api_client.post(
                    "http://localhost:8000/api/v1/data/sensors",
                    json=sensor_data
                )
                # Should succeed despite Redis being down
                assert response.status_code in [200, 201]
            
            # Re-enable Redis
            await client.post(f"{toxiproxy_url}/proxies/redis/enable")
            
            # Allow time for reconnection
            await asyncio.sleep(2)
            
            # Verify system recovers
            async with httpx.AsyncClient(timeout=30.0) as api_client:
                response = await api_client.get("http://localhost:8000/health")
                assert response.status_code == 200
                
        except Exception as e:
            # Always try to re-enable proxy
            try:
                await client.post(f"{toxiproxy_url}/proxies/redis/enable")
            except Exception:
                pass
            raise e
    
    async def test_database_latency_tolerance(self, toxiproxy_client):
        """
        Test system tolerance to database latency.
        
        Verifies:
        - API handles high database latency gracefully
        - Requests don't timeout immediately
        - Performance degrades gracefully under load
        """
        toxiproxy_url = toxiproxy_client["url"]
        client = toxiproxy_client["client"]
        
        if "postgres" not in toxiproxy_client["proxies"]:
            pytest.skip("PostgreSQL proxy not available")
        
        try:
            # Add latency toxic to database proxy (2 second delay)
            latency_toxic = {
                "type": "latency",
                "attributes": {
                    "latency": 2000,  # 2 seconds
                    "jitter": 500     # +/- 500ms jitter
                }
            }
            
            await client.post(
                f"{toxiproxy_url}/proxies/postgres/toxics",
                json=latency_toxic
            )
            
            # Test that health check still works (may be slower)
            async with httpx.AsyncClient(timeout=30.0) as api_client:
                response = await api_client.get("http://localhost:8000/health")
                assert response.status_code == 200
            
            # Test data ingestion with high latency
            sensor_data = {
                "sensor_id": "TEST_RESILIENCE_LATENCY_001", 
                "timestamp": "2024-01-15T12:05:00Z",
                "values": {"temperature": 26.0, "vibration": 0.03}
            }
            
            async with httpx.AsyncClient(timeout=30.0) as api_client:
                response = await api_client.post(
                    "http://localhost:8000/api/v1/data/sensors",
                    json=sensor_data
                )
                # Should still succeed despite latency
                assert response.status_code in [200, 201]
            
        finally:
            # Remove latency toxic
            try:
                await client.delete(f"{toxiproxy_url}/proxies/postgres/toxics")
            except Exception:
                pass
    
    async def test_combined_service_degradation(self, toxiproxy_client):
        """
        Test system behavior under combined service degradations.
        
        Verifies:
        - System handles multiple simultaneous failures
        - Critical functions remain available
        - Recovery works when services are restored
        """
        toxiproxy_url = toxiproxy_client["url"]
        client = toxiproxy_client["client"]
        
        # Apply multiple degradations
        try:
            # Add bandwidth limitation to Redis (simulates slow connection)
            if "redis" in toxiproxy_client["proxies"]:
                bandwidth_toxic = {
                    "type": "bandwidth",
                    "attributes": {
                        "rate": 1000  # 1KB/s - very slow
                    }
                }
                await client.post(
                    f"{toxiproxy_url}/proxies/redis/toxics",
                    json=bandwidth_toxic
                )
            
            # Add timeout toxic to database
            if "postgres" in toxiproxy_client["proxies"]:
                timeout_toxic = {
                    "type": "timeout",
                    "attributes": {
                        "timeout": 5000  # 5 second timeout
                    }
                }
                await client.post(
                    f"{toxiproxy_url}/proxies/postgres/toxics",
                    json=timeout_toxic
                )
            
            # Test system resilience under combined stress
            async with httpx.AsyncClient(timeout=30.0) as api_client:
                # Health check should still work
                response = await api_client.get("http://localhost:8000/health")
                assert response.status_code == 200
                
                # Data ingestion should work but may be slower
                sensor_data = {
                    "sensor_id": "TEST_RESILIENCE_COMBINED_001",
                    "timestamp": "2024-01-15T12:10:00Z", 
                    "values": {"temperature": 27.0, "vibration": 0.04}
                }
                
                response = await api_client.post(
                    "http://localhost:8000/api/v1/data/sensors",
                    json=sensor_data
                )
                # Should succeed despite degraded performance
                assert response.status_code in [200, 201]
        
        finally:
            # Remove all toxics to restore normal operation
            try:
                if "redis" in toxiproxy_client["proxies"]:
                    await client.delete(f"{toxiproxy_url}/proxies/redis/toxics")
                if "postgres" in toxiproxy_client["proxies"]:
                    await client.delete(f"{toxiproxy_url}/proxies/postgres/toxics")
            except Exception:
                pass