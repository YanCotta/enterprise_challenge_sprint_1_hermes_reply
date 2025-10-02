#!/bin/bash
#
# V1.0 Deployment Validation Script
# Automates health checks and smoke tests for Smart Maintenance SaaS
#
# Usage:
#   ./scripts/validate_deployment.sh [--rebuild]
#
# Options:
#   --rebuild    Force rebuild of all containers before validation
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
API_KEY="${API_KEY:-dev_api_key_123}"
MAX_WAIT_SECONDS=120

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose v2 is not installed"
        exit 1
    fi
    
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log_error ".env file not found in $PROJECT_ROOT"
        exit 1
    fi
    
    log_success "Prerequisites OK"
}

rebuild_containers() {
    log_info "Rebuilding containers (--no-cache)..."
    cd "$PROJECT_ROOT"
    docker compose build --no-cache
    log_success "Build complete"
}

start_containers() {
    log_info "Starting containers..."
    cd "$PROJECT_ROOT"
    docker compose up -d
    log_success "Containers started"
}

wait_for_health() {
    log_info "Waiting for services to become healthy (max ${MAX_WAIT_SECONDS}s)..."
    
    local elapsed=0
    local interval=5
    
    while [ $elapsed -lt $MAX_WAIT_SECONDS ]; do
        # Check if API container is healthy
        local api_health=$(docker compose ps api --format json | jq -r '.[0].Health' 2>/dev/null || echo "")
        
        if [ "$api_health" = "healthy" ]; then
            log_success "API service is healthy"
            return 0
        fi
        
        echo -n "."
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    log_error "Services did not become healthy within ${MAX_WAIT_SECONDS}s"
    docker compose ps
    docker compose logs api --tail=50
    exit 1
}

check_service_health() {
    log_info "Running health checks..."
    
    cd "$PROJECT_ROOT"
    
    # Check API health
    if docker compose exec -T api curl -f -H "x-api-key: $API_KEY" http://localhost:8000/health &>/dev/null; then
        log_success "API health check passed"
    else
        log_error "API health check failed"
        return 1
    fi
    
    # Check database health
    if docker compose exec -T api curl -f -H "x-api-key: $API_KEY" http://localhost:8000/health/db &>/dev/null; then
        log_success "Database health check passed"
    else
        log_warning "Database health check failed (may be expected if using cloud DB)"
    fi
    
    # Check Redis health
    if docker compose exec -T api curl -f -H "x-api-key: $API_KEY" http://localhost:8000/health/redis &>/dev/null; then
        log_success "Redis health check passed"
    else
        log_warning "Redis health check failed (may be expected if using cloud Redis)"
    fi
    
    # Check UI accessibility
    if curl -f http://localhost:8501 &>/dev/null; then
        log_success "UI is accessible"
    else
        log_warning "UI accessibility check failed"
    fi
    
    return 0
}

run_smoke_tests() {
    log_info "Running automated smoke tests..."
    
    cd "$PROJECT_ROOT"
    
    if docker compose exec -T api poetry run python scripts/smoke_v1.py; then
        log_success "Smoke tests PASSED"
        return 0
    else
        log_error "Smoke tests FAILED"
        log_info "Check output above for details"
        return 1
    fi
}

show_service_status() {
    log_info "Current service status:"
    cd "$PROJECT_ROOT"
    docker compose ps
}

show_logs() {
    log_info "Recent API logs (last 20 lines):"
    cd "$PROJECT_ROOT"
    docker compose logs api --tail=20
}

main() {
    echo "========================================="
    echo "V1.0 Deployment Validation"
    echo "========================================="
    echo ""
    
    local rebuild=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --rebuild)
                rebuild=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Usage: $0 [--rebuild]"
                exit 1
                ;;
        esac
    done
    
    # Run validation steps
    check_prerequisites
    
    if [ "$rebuild" = true ]; then
        rebuild_containers
    fi
    
    start_containers
    wait_for_health
    
    echo ""
    log_info "=== Phase 1: Service Health Checks ==="
    check_service_health
    health_result=$?
    
    echo ""
    log_info "=== Phase 2: Automated Smoke Tests ==="
    run_smoke_tests
    smoke_result=$?
    
    echo ""
    log_info "=== Validation Summary ==="
    show_service_status
    
    echo ""
    if [ $health_result -eq 0 ] && [ $smoke_result -eq 0 ]; then
        log_success "✅ ALL VALIDATIONS PASSED"
        echo ""
        log_info "Next steps:"
        echo "  1. Run UI validation (see docs/V1_DEPLOYMENT_VALIDATION_CHECKLIST.md)"
        echo "  2. Review http://localhost:8501 manually"
        echo "  3. Proceed to VM deployment when ready"
        exit 0
    else
        log_error "❌ SOME VALIDATIONS FAILED"
        echo ""
        log_info "Troubleshooting:"
        echo "  - Check logs: docker compose logs api"
        echo "  - Check services: docker compose ps"
        echo "  - Review error messages above"
        show_logs
        exit 1
    fi
}

main "$@"
