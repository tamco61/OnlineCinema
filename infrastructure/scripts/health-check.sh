#!/bin/bash
# Health Check Script for Cinema Platform

set -e

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "Cinema Platform - Health Check"
echo "==============================="
echo ""

check_service() {
    local name=$1
    local url=$2
    local timeout=${3:-5}

    printf "  %-20s " "$name:"
    if curl -sf --max-time $timeout "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        return 1
    fi
}

check_container() {
    local name=$1
    local container=$2
    local cmd=$3

    printf "  %-20s " "$name:"
    if docker exec "$container" $cmd > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        return 1
    fi
}

echo "Infrastructure:"
check_container "PostgreSQL" "cinema-postgres" "pg_isready -U cinema_user" || true
check_container "Redis" "cinema-redis" "redis-cli -a redis_password ping" || true
check_service "Elasticsearch" "http://localhost:9200/_cluster/health" || true
check_service "ClickHouse" "http://localhost:8123/ping" || true
check_service "MinIO" "http://localhost:9002/minio/health/live" || true

echo ""
echo "Microservices:"
check_service "Auth Service" "http://localhost:8001/health" || true
check_service "User Service" "http://localhost:8002/health" || true
check_service "Catalog Service" "http://localhost:8003/health" || true
check_service "Search Service" "http://localhost:8004/health" || true
check_service "Streaming Service" "http://localhost:8005/health" || true
check_service "Analytics Service" "http://localhost:8006/health" || true

echo ""
echo "Gateway & Monitoring:"
check_service "NGINX Gateway" "http://localhost/health" || true
check_service "Prometheus" "http://localhost:9090/-/ready" || true
check_service "Grafana" "http://localhost:3000/api/health" || true
check_service "Jaeger" "http://localhost:16686" || true

echo ""
echo "Health check complete!"
