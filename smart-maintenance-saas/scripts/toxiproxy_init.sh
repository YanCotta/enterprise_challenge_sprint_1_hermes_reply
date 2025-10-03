#!/bin/bash
# Toxiproxy Initialization Script for Docker Compose
#
# Configures Toxiproxy proxies on container startup so Redis and PostgreSQL
# requests can be routed through the proxy for chaos testing.

set -euo pipefail

echo "=== Toxiproxy Auto-Initialization ==="
echo "Waiting for Toxiproxy server to be ready..."

# Wait for Toxiproxy to be ready with timeout
TIMEOUT=60
ELAPSED=0
until curl -f http://toxiproxy:8474/version > /dev/null 2>&1; do
    if [ $ELAPSED -ge $TIMEOUT ]; then
        echo "❌ Timeout waiting for Toxiproxy server"
        exit 1
    fi
    echo "⏳ Waiting for Toxiproxy... (${ELAPSED}s/${TIMEOUT}s)"
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

echo "✅ Toxiproxy server is ready"

# Create Redis proxy (API -> toxiproxy:6380 -> redis:6379)
echo "🔧 Creating Redis proxy..."
curl -X POST http://toxiproxy:8474/proxies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "redis",
    "listen": "0.0.0.0:6380",
    "upstream": "redis:6379",
    "enabled": true
  }' || echo "ℹ️  Redis proxy might already exist"

# Create PostgreSQL proxy (API -> toxiproxy:5434 -> db:5432)
echo "🔧 Creating PostgreSQL proxy..."
curl -X POST http://toxiproxy:8474/proxies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "postgres", 
    "listen": "0.0.0.0:5434",
    "upstream": "db:5432",
    "enabled": true
  }' || echo "ℹ️  PostgreSQL proxy might already exist"

# Verify proxies are running
echo "📋 Current proxies:"
curl -s http://toxiproxy:8474/proxies | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for name, config in data.items():
        status = '✅ Enabled' if config['enabled'] else '❌ Disabled'
        print(f'  - {name}: {config[\"listen\"]} -> {config[\"upstream\"]} ({status})')
except:
    print('  Error parsing proxy list')
"

echo "✅ Toxiproxy initialization complete!"
echo ""
echo "🌐 Proxy endpoints available:"
echo "  - Redis: toxiproxy:6380 -> redis:6379"
echo "  - PostgreSQL: toxiproxy:5434 -> db:5432"
echo ""
echo "🧪 Ready for chaos engineering and network simulation tests."