#!/bin/bash
# Smart Maintenance SaaS - VM Deployment Script
# This script automates the deployment process with validation and health checks

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================================="
echo "  Smart Maintenance SaaS - VM Deployment"
echo "=================================================="
echo ""

# Check if running from project root
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}ERROR: docker-compose.yml not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Step 1: Validate .env file exists
echo "Step 1: Validating environment configuration..."
if [ ! -f .env ]; then
    echo -e "${RED}ERROR: .env file not found${NC}"
    echo "Please create .env file from .env_example.txt:"
    echo "  cp .env_example.txt .env"
    echo "  # Edit .env with your actual values"
    exit 1
fi

# Step 2: Validate required environment variables
echo "Step 2: Checking required environment variables..."
required_vars=("DATABASE_URL" "REDIS_URL" "API_KEY" "SECRET_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=.\+" .env; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo -e "${RED}ERROR: Missing or empty required variables in .env:${NC}"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    exit 1
fi

echo -e "${GREEN}✓ Environment configuration validated${NC}"
echo ""

# Step 3: Check Docker availability
echo "Step 3: Checking Docker availability..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker not found${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}ERROR: docker-compose not found${NC}"
    echo "Please install docker-compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker is available${NC}"
echo ""

# Step 4: Build Docker images
echo "Step 4: Building Docker images..."
echo "This may take several minutes on first run..."
docker-compose build --no-cache || {
    echo -e "${RED}ERROR: Docker build failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Docker images built successfully${NC}"
echo ""

# Step 5: Start services
echo "Step 5: Starting services..."
docker-compose up -d || {
    echo -e "${RED}ERROR: Failed to start services${NC}"
    exit 1
}
echo -e "${GREEN}✓ Services started${NC}"
echo ""

# Step 6: Wait for health checks
echo "Step 6: Waiting for services to become healthy..."
echo "This may take up to 2 minutes..."

MAX_WAIT=120
ELAPSED=0
API_HEALTHY=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
        API_HEALTHY=1
        break
    fi
    echo -n "."
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

echo ""

if [ $API_HEALTHY -eq 0 ]; then
    echo -e "${RED}ERROR: API health check timed out after ${MAX_WAIT}s${NC}"
    echo "Checking service logs..."
    docker-compose logs --tail=50 api
    exit 1
fi

echo -e "${GREEN}✓ API is healthy${NC}"
echo ""

# Step 7: Verify all services
echo "Step 7: Verifying service status..."
docker-compose ps
echo ""

# Step 8: Run smoke tests
echo "Step 8: Running smoke tests..."
if [ -f "scripts/smoke_test.py" ]; then
    python3 scripts/smoke_test.py || {
        echo -e "${YELLOW}WARNING: Smoke tests failed${NC}"
        echo "Services are running but may have issues"
        echo "Check logs with: docker-compose logs"
    }
else
    echo -e "${YELLOW}WARNING: smoke_test.py not found, skipping automated tests${NC}"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}  Deployment Complete!${NC}"
echo "=================================================="
echo ""
echo "Services are now running:"
echo "  - API:       http://localhost:8000"
echo "  - UI:        http://localhost:8501"
echo "  - API Docs:  http://localhost:8000/docs"
echo "  - Metrics:   http://localhost:8000/metrics"
echo "  - MLflow:    http://localhost:5000"
echo ""
echo "Useful commands:"
echo "  - View logs:         docker-compose logs -f [service]"
echo "  - Stop services:     docker-compose down"
echo "  - Restart service:   docker-compose restart [service]"
echo "  - Check health:      curl http://localhost:8000/health"
echo ""
echo "Next steps:"
echo "  1. Test UI at http://localhost:8501"
echo "  2. Review API docs at http://localhost:8000/docs"
echo "  3. Monitor logs for any errors"
echo "  4. Run validation tests (see SYSTEM_AUDIT_REPORT.md)"
echo ""
