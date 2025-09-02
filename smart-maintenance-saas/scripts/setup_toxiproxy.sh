#!/bin/bash
"""
Toxiproxy Setup Script

This script initializes Toxiproxy proxies for chaos engineering tests.
It creates proxies for Redis and PostgreSQL services to enable
network failure simulation.
"""

set -e

echo "=== Toxiproxy Setup Script ==="
echo "Setting up proxies for Redis and PostgreSQL..."

# Wait for Toxiproxy to be ready
echo "Waiting for Toxiproxy server to be ready..."
until curl -f http://localhost:8474/version > /dev/null 2>&1; do
    echo "Waiting for Toxiproxy..."
    sleep 2
done

echo "✅ Toxiproxy server is ready"

# Create Redis proxy (API -> toxiproxy:6380 -> redis:6379)
echo "Creating Redis proxy..."
curl -X POST http://localhost:8474/proxies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "redis",
    "listen": "0.0.0.0:6380",
    "upstream": "redis:6379",
    "enabled": true
  }' || echo "Redis proxy might already exist"

# Create PostgreSQL proxy (API -> toxiproxy:5434 -> db:5432)
echo "Creating PostgreSQL proxy..."
curl -X POST http://localhost:8474/proxies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "postgres", 
    "listen": "0.0.0.0:5434",
    "upstream": "db:5432",
    "enabled": true
  }' || echo "PostgreSQL proxy might already exist"

# List all proxies
echo "Current proxies:"
curl -s http://localhost:8474/proxies | python3 -m json.tool

echo "✅ Toxiproxy setup complete!"
echo ""
echo "Proxy endpoints:"
echo "  - Redis: localhost:6380 -> redis:6379"
echo "  - PostgreSQL: localhost:5434 -> db:5432"
echo ""
echo "Use these in chaos tests to simulate network failures."