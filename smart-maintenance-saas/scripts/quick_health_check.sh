#!/bin/bash
#
# Quick Health Check - Run this first to see if containers are already up and healthy
#
# Usage: ./scripts/quick_health_check.sh
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Quick Health Check ===${NC}\n"

cd "$(dirname "$0")/.."

# Check if containers are running
echo -e "${BLUE}[1/5]${NC} Checking container status..."
if docker compose ps --format json | jq -e '.[0]' &>/dev/null; then
    echo -e "${GREEN}✓${NC} Containers are running"
    docker compose ps
else
    echo -e "${RED}✗${NC} No containers running"
    echo -e "${YELLOW}→${NC} Run: docker compose up -d"
    exit 1
fi

echo ""

# Check API health
echo -e "${BLUE}[2/5]${NC} Checking API health..."
if curl -f http://localhost:8000/health &>/dev/null; then
    echo -e "${GREEN}✓${NC} API is healthy"
else
    echo -e "${RED}✗${NC} API is not responding"
    echo -e "${YELLOW}→${NC} Check: docker compose logs api --tail=50"
fi

echo ""

# Check UI
echo -e "${BLUE}[3/5]${NC} Checking UI..."
if curl -f http://localhost:8501 &>/dev/null; then
    echo -e "${GREEN}✓${NC} UI is accessible at http://localhost:8501"
else
    echo -e "${RED}✗${NC} UI is not responding"
    echo -e "${YELLOW}→${NC} Check: docker compose logs ui --tail=50"
fi

echo ""

# Check database connectivity
echo -e "${BLUE}[4/5]${NC} Checking database connectivity..."
if docker compose exec -T api curl -f http://localhost:8000/health/db &>/dev/null; then
    echo -e "${GREEN}✓${NC} Database is connected"
else
    echo -e "${YELLOW}!${NC} Database health check failed (may use cloud DB)"
fi

echo ""

# Check Redis connectivity
echo -e "${BLUE}[5/5]${NC} Checking Redis connectivity..."
if docker compose exec -T api curl -f http://localhost:8000/health/redis &>/dev/null; then
    echo -e "${GREEN}✓${NC} Redis is connected"
else
    echo -e "${YELLOW}!${NC} Redis health check failed (may use cloud Redis)"
fi

echo ""
echo -e "${GREEN}=== Health Check Complete ===${NC}"
echo ""
echo "Next steps:"
echo "  • If all checks passed: Run smoke tests with ./scripts/validate_deployment.sh"
echo "  • If checks failed: Review logs and restart services"
echo "  • To test UI manually: Open http://localhost:8501 in your browser"
