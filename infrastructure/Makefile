# ===========================================
# Cinema Platform - Infrastructure Makefile
# ===========================================

.PHONY: help init up down restart status logs health-check clean-all \
        infrastructure-up infrastructure-down services-up services-down \
        build rebuild scale logs-service db-shell redis-cli \
        prod-up prod-down monitoring-up monitoring-down \
        open-grafana open-prometheus open-jaeger open-kibana \
        run-auth run-user run-catalog run-search run-streaming run-analytics \
        run-core run-messaging run-storage run-monitoring run-gateway

# Default shell
SHELL := /bin/bash

# Docker Compose files
COMPOSE_FILE := docker/docker-compose.yml
COMPOSE_PROD_FILE := docker/docker-compose.prod.yml

# Docker Compose command
DC := docker compose -f $(COMPOSE_FILE)
DC_PROD := docker compose -f $(COMPOSE_FILE) -f $(COMPOSE_PROD_FILE)

# Load environment variables from .env if exists
-include .env
export

# Default values (fallback if .env not loaded)
REDIS_PASSWORD ?= redis_password
MINIO_API_PORT ?= 9002

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# ===========================================
# HELP
# ===========================================

help: ## Show this help message
	@echo ""
	@echo "Cinema Platform - Infrastructure Commands"
	@echo "=========================================="
	@echo ""
	@echo "$(GREEN)QUICK START (Low Memory):$(NC)"
	@echo "  make run-core          - Start PostgreSQL + Redis only"
	@echo "  make run-auth          - Start Auth service + dependencies"
	@echo "  make run-catalog       - Start Catalog service + dependencies"
	@echo ""
	@echo "$(GREEN)FULL PLATFORM:$(NC)"
	@echo "  make up                - Start ALL services"
	@echo "  make prod-up           - Start in production mode with scaling"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ===========================================
# INITIALIZATION
# ===========================================

init: ## Initialize environment (create .env, directories)
	@echo "$(GREEN)Initializing environment...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)Created .env file from .env.example$(NC)"; \
	else \
		echo "$(YELLOW).env file already exists$(NC)"; \
	fi
	@mkdir -p docker/init-scripts
	@mkdir -p nginx/conf.d nginx/ssl
	@mkdir -p monitoring/prometheus monitoring/grafana/provisioning/datasources monitoring/grafana/provisioning/dashboards
	@chmod +x docker/init-scripts/*.sh 2>/dev/null || true
	@echo "$(GREEN)Environment initialized successfully!$(NC)"

# ===========================================
# PROFILE-BASED COMMANDS (LOW MEMORY)
# ===========================================

run-core: init ## Start only core (PostgreSQL + Redis) - minimal memory
	@echo "$(GREEN)Starting core services (PostgreSQL + Redis)...$(NC)"
	$(DC) --profile core up -d
	@echo "$(GREEN)Core services started!$(NC)"
	@echo "  PostgreSQL: localhost:5432"
	@echo "  Redis: localhost:6379"

run-messaging: init ## Start Kafka + Zookeeper
	@echo "$(GREEN)Starting messaging services...$(NC)"
	$(DC) --profile messaging up -d
	@echo "$(GREEN)Messaging services started!$(NC)"

run-storage: init ## Start MinIO (S3 storage)
	@echo "$(GREEN)Starting storage services...$(NC)"
	$(DC) --profile storage up -d
	@echo "$(GREEN)MinIO started at localhost:9001$(NC)"

run-monitoring: init ## Start monitoring (Prometheus, Grafana, Jaeger)
	@echo "$(GREEN)Starting monitoring services...$(NC)"
	$(DC) --profile monitoring up -d
	@echo "$(GREEN)Monitoring started!$(NC)"
	@echo "  Prometheus: localhost:9090"
	@echo "  Grafana: localhost:3000"
	@echo "  Jaeger: localhost:16686"

run-gateway: init ## Start NGINX gateway
	@echo "$(GREEN)Starting NGINX gateway...$(NC)"
	$(DC) --profile gateway up -d
	@echo "$(GREEN)Gateway started at localhost:80$(NC)"

# ===========================================
# INDIVIDUAL MICROSERVICES (WITH DEPS)
# ===========================================

run-auth: init ## Start Auth service + PostgreSQL + Redis
	@echo "$(GREEN)Starting Auth service with dependencies...$(NC)"
	$(DC) --profile auth up -d
	@echo "$(GREEN)Auth service started at localhost:8001$(NC)"

run-user: init ## Start User service + PostgreSQL + Redis
	@echo "$(GREEN)Starting User service with dependencies...$(NC)"
	$(DC) --profile user up -d
	@echo "$(GREEN)User service started at localhost:8002$(NC)"

run-catalog: init ## Start Catalog service + PostgreSQL + Redis + Kafka
	@echo "$(GREEN)Starting Catalog service with dependencies...$(NC)"
	$(DC) --profile catalog up -d
	@echo "$(GREEN)Catalog service started at localhost:8003$(NC)"

run-search: init ## Start Search service + Elasticsearch + Redis + Kafka
	@echo "$(GREEN)Starting Search service with dependencies...$(NC)"
	$(DC) --profile search up -d
	@echo "$(GREEN)Search service started at localhost:8004$(NC)"

run-streaming: init ## Start Streaming service + PostgreSQL + Redis + MinIO + Kafka
	@echo "$(GREEN)Starting Streaming service with dependencies...$(NC)"
	$(DC) --profile streaming up -d
	@echo "$(GREEN)Streaming service started at localhost:8005$(NC)"

run-analytics: init ## Start Analytics service + ClickHouse + Kafka
	@echo "$(GREEN)Starting Analytics service with dependencies...$(NC)"
	$(DC) --profile analytics up -d
	@echo "$(GREEN)Analytics service started at localhost:8006$(NC)"

# ===========================================
# FULL PLATFORM
# ===========================================

up: init ## Start all services (full profile)
	@echo "$(GREEN)Starting all Cinema Platform services...$(NC)"
	$(DC) --profile full up -d
	@echo ""
	@echo "$(GREEN)Services started! Run 'make health-check' to verify.$(NC)"
	@echo ""
	@echo "Available endpoints:"
	@echo "  - API Gateway:  http://localhost"
	@echo "  - Prometheus:   http://localhost:9090"
	@echo "  - Grafana:      http://localhost:3000 (admin/admin)"
	@echo "  - Jaeger:       http://localhost:16686"
	@echo "  - MinIO:        http://localhost:9001 (minio/minio_dev_password)"

down: ## Stop all services
	@echo "$(YELLOW)Stopping all services...$(NC)"
	$(DC) --profile full --profile core --profile messaging --profile storage \
		--profile monitoring --profile gateway --profile auth --profile user \
		--profile catalog --profile search --profile streaming --profile analytics \
		--profile services down
	@echo "$(GREEN)All services stopped.$(NC)"

restart: down up ## Restart all services

status: ## Show status of all containers
	@echo "$(GREEN)Container Status:$(NC)"
	@echo ""
	@docker ps --filter "name=cinema-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "No running containers"
	@echo ""

logs: ## Show logs for all cinema containers
	@docker logs -f $$(docker ps -q --filter "name=cinema-" | head -1) 2>/dev/null || $(DC) --profile full logs -f --tail=100

logs-service: ## Show logs for specific service (usage: make logs-service SERVICE=auth-service)
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)ERROR: SERVICE is required. Usage: make logs-service SERVICE=auth-service$(NC)"; \
		exit 1; \
	fi
	docker logs -f cinema-$(SERVICE) 2>/dev/null || $(DC) logs -f --tail=100 $(SERVICE)

# ===========================================
# HEALTH CHECKS
# ===========================================

health-check: ## Check health of running services
	@echo "$(GREEN)Checking service health...$(NC)"
	@echo ""
	@echo "Infrastructure:"
	@echo -n "  PostgreSQL:     "; docker exec cinema-postgres pg_isready -U cinema_user 2>/dev/null && echo "$(GREEN)OK$(NC)" || echo "$(YELLOW)NOT RUNNING$(NC)"
	@echo -n "  Redis:          "; docker exec cinema-redis redis-cli -a $(REDIS_PASSWORD) ping 2>/dev/null | grep -q PONG && echo "$(GREEN)OK$(NC)" || echo "$(YELLOW)NOT RUNNING$(NC)"
	@echo -n "  Elasticsearch:  "; curl -sf http://localhost:9200/_cluster/health 2>/dev/null | grep -q "green\|yellow" && echo "$(GREEN)OK$(NC)" || echo "$(YELLOW)NOT RUNNING$(NC)"
	@echo -n "  ClickHouse:     "; curl -sf http://localhost:8123/ping 2>/dev/null && echo "$(GREEN)OK$(NC)" || echo "$(YELLOW)NOT RUNNING$(NC)"
	@echo -n "  Kafka:          "; docker exec cinema-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 2>/dev/null | head -1 > /dev/null && echo "$(GREEN)OK$(NC)" || echo "$(YELLOW)NOT RUNNING$(NC)"
	@echo -n "  MinIO:          "; curl -sf "http://localhost:$(MINIO_API_PORT)/minio/health/live" 2>/dev/null && echo "$(GREEN)OK$(NC)" || echo "$(YELLOW)NOT RUNNING$(NC)"
	@echo ""
	@echo "Microservices:"
	@echo -n "  Auth (8001):      "; curl -sf http://localhost:8001/health 2>/dev/null && echo "$(GREEN)OK$(NC)" || echo "$(YELLOW)NOT RUNNING$(NC)"
	@echo -n "  User (8002):      "; curl -sf http://localhost:8002/health 2>/dev/null && echo "$(GREEN)OK$(NC)" || echo "$(YELLOW)NOT RUNNING$(NC)"
	@echo -n "  Catalog (8003):   "; curl -sf http://localhost:8003/health 2>/dev/null && echo "$(GREEN)OK$(NC)" || echo "$(YELLOW)NOT RUNNING$(NC)"
	@echo -n "  Search (8004):    "; curl -sf http://localhost:8004/health 2>/dev/null && echo "$(GREEN)OK$(NC)" || echo "$(YELLOW)NOT RUNNING$(NC)"
	@echo -n "  Streaming (8005): "; curl -sf http://localhost:8005/health 2>/dev/null && echo "$(GREEN)OK$(NC)" || echo "$(YELLOW)NOT RUNNING$(NC)"
	@echo -n "  Analytics (8006): "; curl -sf http://localhost:8006/health 2>/dev/null && echo "$(GREEN)OK$(NC)" || echo "$(YELLOW)NOT RUNNING$(NC)"
	@echo ""
	@echo "Gateway & Monitoring:"
	@echo -n "  NGINX:          "; curl -sf http://localhost/health 2>/dev/null && echo "$(GREEN)OK$(NC)" || echo "$(YELLOW)NOT RUNNING$(NC)"
	@echo -n "  Prometheus:     "; curl -sf http://localhost:9090/-/ready 2>/dev/null && echo "$(GREEN)OK$(NC)" || echo "$(YELLOW)NOT RUNNING$(NC)"
	@echo -n "  Grafana:        "; curl -sf http://localhost:3000/api/health 2>/dev/null && echo "$(GREEN)OK$(NC)" || echo "$(YELLOW)NOT RUNNING$(NC)"
	@echo -n "  Jaeger:         "; curl -sf http://localhost:16686/ 2>/dev/null && echo "$(GREEN)OK$(NC)" || echo "$(YELLOW)NOT RUNNING$(NC)"

test-api: ## Test API endpoints through gateway
	@echo "$(GREEN)Testing API endpoints...$(NC)"
	@echo ""
	@echo "Gateway Health:"
	@curl -sf http://localhost/health | jq . 2>/dev/null || echo "Gateway not responding"
	@echo ""
	@echo "Auth Service:"
	@curl -sf http://localhost/services/auth/health | jq . 2>/dev/null || echo "Auth service not responding"
	@echo ""
	@echo "Catalog Service:"
	@curl -sf http://localhost/services/catalog/health | jq . 2>/dev/null || echo "Catalog service not responding"

# ===========================================
# LEGACY COMMANDS (for compatibility)
# ===========================================

infrastructure-up: run-core run-messaging ## Start infrastructure (PostgreSQL, Redis, Kafka)
	@echo "$(GREEN)Infrastructure started.$(NC)"

infrastructure-down: ## Stop infrastructure services
	@echo "$(YELLOW)Stopping infrastructure services...$(NC)"
	$(DC) --profile core --profile messaging stop
	@echo "$(GREEN)Infrastructure services stopped.$(NC)"

services-up: ## Start all microservices
	@echo "$(GREEN)Starting microservices...$(NC)"
	$(DC) --profile services up -d
	@echo "$(GREEN)Microservices started.$(NC)"

services-down: ## Stop microservices
	@echo "$(YELLOW)Stopping microservices...$(NC)"
	$(DC) --profile services stop
	@echo "$(GREEN)Microservices stopped.$(NC)"

monitoring-up: run-monitoring ## Start monitoring stack

monitoring-down: ## Stop monitoring stack
	@echo "$(YELLOW)Stopping monitoring services...$(NC)"
	$(DC) --profile monitoring stop
	@echo "$(GREEN)Monitoring services stopped.$(NC)"

# ===========================================
# BUILD & REBUILD
# ===========================================

build: ## Build all service images
	@echo "$(GREEN)Building all service images...$(NC)"
	$(DC) --profile full build
	@echo "$(GREEN)Build complete.$(NC)"

rebuild: ## Rebuild and restart a specific service (usage: make rebuild SERVICE=auth-service)
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)ERROR: SERVICE is required. Usage: make rebuild SERVICE=auth-service$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Rebuilding $(SERVICE)...$(NC)"
	$(DC) build --no-cache $(SERVICE)
	$(DC) up -d $(SERVICE)
	@echo "$(GREEN)$(SERVICE) rebuilt and restarted.$(NC)"

rebuild-all: ## Rebuild all services without cache
	@echo "$(GREEN)Rebuilding all services...$(NC)"
	$(DC) --profile full build --no-cache
	$(DC) --profile full up -d
	@echo "$(GREEN)All services rebuilt and restarted.$(NC)"

# ===========================================
# SCALING (Docker Compose)
# ===========================================

scale: ## Scale a service (usage: make scale SERVICE=catalog-service REPLICAS=3)
	@if [ -z "$(SERVICE)" ] || [ -z "$(REPLICAS)" ]; then \
		echo "$(RED)ERROR: SERVICE and REPLICAS are required.$(NC)"; \
		echo "Usage: make scale SERVICE=catalog-service REPLICAS=3"; \
		exit 1; \
	fi
	@echo "$(GREEN)Scaling $(SERVICE) to $(REPLICAS) replicas...$(NC)"
	$(DC) up -d --scale $(SERVICE)=$(REPLICAS) --no-recreate
	@echo "$(GREEN)$(SERVICE) scaled to $(REPLICAS) replicas.$(NC)"

# ===========================================
# PRODUCTION
# ===========================================

prod-up: init ## Start services in production mode with scaling
	@echo "$(GREEN)Starting Cinema Platform in PRODUCTION mode...$(NC)"
	$(DC_PROD) --profile full up -d
	@echo "$(GREEN)Production services started with scaling!$(NC)"

prod-down: ## Stop production services
	@echo "$(YELLOW)Stopping production services...$(NC)"
	$(DC_PROD) --profile full down
	@echo "$(GREEN)Production services stopped.$(NC)"

prod-scale: ## Scale service in production (usage: make prod-scale SERVICE=catalog-service REPLICAS=5)
	@if [ -z "$(SERVICE)" ] || [ -z "$(REPLICAS)" ]; then \
		echo "$(RED)ERROR: SERVICE and REPLICAS are required.$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Scaling $(SERVICE) to $(REPLICAS) replicas (production)...$(NC)"
	$(DC_PROD) up -d --scale $(SERVICE)=$(REPLICAS) --no-recreate

# ===========================================
# DATABASE ACCESS
# ===========================================

db-shell: ## Open PostgreSQL shell
	@echo "$(GREEN)Connecting to PostgreSQL...$(NC)"
	docker exec -it cinema-postgres psql -U cinema_user -d postgres

db-auth: ## Connect to auth database
	docker exec -it cinema-postgres psql -U cinema_user -d auth_db

db-catalog: ## Connect to catalog database
	docker exec -it cinema-postgres psql -U cinema_user -d catalog_db

redis-cli: ## Open Redis CLI
	@echo "$(GREEN)Connecting to Redis...$(NC)"
	docker exec -it cinema-redis redis-cli -a $(REDIS_PASSWORD)

# ===========================================
# CLEANUP
# ===========================================

clean-containers: ## Remove all stopped containers
	@echo "$(YELLOW)Removing stopped containers...$(NC)"
	docker rm $$(docker ps -aq --filter "name=cinema-") 2>/dev/null || true
	@echo "$(GREEN)Containers removed.$(NC)"

clean-volumes: ## Remove all volumes (WARNING: Deletes all data!)
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	$(DC) --profile full down -v
	@echo "$(GREEN)Volumes removed.$(NC)"

clean-images: ## Remove all project images
	@echo "$(YELLOW)Removing project images...$(NC)"
	docker images | grep "cinema" | awk '{print $$3}' | xargs -r docker rmi -f 2>/dev/null || true
	@echo "$(GREEN)Images removed.$(NC)"

clean-all: clean-containers clean-volumes clean-images ## Full cleanup (containers, volumes, images)
	@echo "$(GREEN)Full cleanup complete.$(NC)"

prune: ## Docker system prune (remove unused data)
	@echo "$(YELLOW)Pruning Docker system...$(NC)"
	docker system prune -f
	@echo "$(GREEN)Prune complete.$(NC)"

# ===========================================
# OPEN SERVICES IN BROWSER
# ===========================================

open-grafana: ## Open Grafana in browser
	@open http://localhost:3000 2>/dev/null || xdg-open http://localhost:3000 2>/dev/null || echo "Open http://localhost:3000 in your browser"

open-prometheus: ## Open Prometheus in browser
	@open http://localhost:9090 2>/dev/null || xdg-open http://localhost:9090 2>/dev/null || echo "Open http://localhost:9090 in your browser"

open-jaeger: ## Open Jaeger in browser
	@open http://localhost:16686 2>/dev/null || xdg-open http://localhost:16686 2>/dev/null || echo "Open http://localhost:16686 in your browser"

open-minio: ## Open MinIO Console in browser
	@open http://localhost:9001 2>/dev/null || xdg-open http://localhost:9001 2>/dev/null || echo "Open http://localhost:9001 in your browser"

# ===========================================
# QUICK START
# ===========================================

quick-start: run-core ## Quick start with minimal resources
	@echo ""
	@echo "$(GREEN)Core infrastructure started!$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Wait 10-20 seconds for databases to initialize"
	@echo "  2. Run individual services as needed:"
	@echo "     make run-auth      - Auth service"
	@echo "     make run-catalog   - Catalog service (needs Kafka)"
	@echo "     make run-search    - Search service (needs Elasticsearch)"
	@echo "  3. Check health: make health-check"
