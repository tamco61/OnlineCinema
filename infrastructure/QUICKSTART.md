# Quick Start Guide - Cinema Platform

Быстрый запуск всей инфраструктуры локально.

## Требования

- **Docker Desktop** (или Docker Engine + Docker Compose v2)
  - Минимум 8GB RAM выделено для Docker
  - Минимум 20GB свободного места
- **Make** (обычно уже установлен на macOS/Linux)
- **curl** (для проверки здоровья сервисов)

## Запуск (выберите вариант)

### Вариант A: Минимальный запуск (Low Memory)

Для систем с ограниченной памятью запускайте сервисы по отдельности:

```bash
cd infrastructure
make init

# Шаг 1: Только базы данных (~500MB RAM)
make run-core

# Шаг 2: Запуск нужного сервиса (выберите один)
make run-auth      # Auth service + PostgreSQL + Redis
make run-catalog   # Catalog + PostgreSQL + Redis + Kafka
make run-search    # Search + Elasticsearch + Redis + Kafka
make run-streaming # Streaming + PostgreSQL + Redis + MinIO
make run-analytics # Analytics + ClickHouse + Kafka
```

### Вариант B: Полный запуск (8GB+ RAM)

```bash
cd infrastructure
make init
make up
```

Эта команда запустит:

**Базы данных:**
- PostgreSQL (основная БД, порт 5432)
- Redis (кэш и сессии, порт 6379)
- ClickHouse (аналитика, порт 8123/9000)
- Elasticsearch (поиск, порт 9200)

**Message Queue:**
- Kafka + Zookeeper (порт 9092)

**Storage:**
- MinIO (S3-compatible, порты 9001/9002)

**Микросервисы:**
- Auth Service (порт 8001)
- User Service (порт 8002)
- Catalog Service (порт 8003)
- Search Service (порт 8004)
- Streaming Service (порт 8005)
- Analytics Service (порт 8006)

**API Gateway:**
- NGINX (порт 80)

**Мониторинг:**
- Prometheus (порт 9090)
- Grafana (порт 3000)
- Jaeger (порт 16686)

**Ожидание**: 2-5 минут (первый запуск дольше)

### Шаг 3: Проверка работоспособности

```bash
# Подождите 60 секунд, затем:
make health-check
```

## Доступ к сервисам

| Сервис | URL | Логин/Пароль |
|--------|-----|--------------|
| **API Gateway** | http://localhost | - |
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Jaeger** | http://localhost:16686 | - |
| **MinIO Console** | http://localhost:9001 | minio / minio_dev_password |

## Полезные команды

```bash
# Просмотр статуса контейнеров
make status

# Просмотр логов всех сервисов
make logs

# Просмотр логов конкретного сервиса
make logs-service SERVICE=catalog-service

# Перезапуск всех сервисов
make restart

# Остановка всех сервисов
make down

# Полная очистка (удаление всех данных!)
make clean-all
```

## Масштабирование

### Development (docker-compose)

```bash
# Масштабировать конкретный сервис
make scale SERVICE=catalog-service REPLICAS=3

# Просмотреть статус
make status
```

### Production (с deploy настройками)

```bash
# Запуск в production режиме с репликами
make prod-up

# Масштабирование в production
make prod-scale SERVICE=streaming-service REPLICAS=5
```

Количество реплик по умолчанию настраивается в `.env`:
```env
AUTH_REPLICAS=2
USER_REPLICAS=2
CATALOG_REPLICAS=3
SEARCH_REPLICAS=2
STREAMING_REPLICAS=3
ANALYTICS_REPLICAS=2
```

## Тестирование API

```bash
# Тест gateway
curl http://localhost/health

# Тест сервисов через gateway
curl http://localhost/services/auth/health
curl http://localhost/services/catalog/health

# Прямой доступ к сервисам
curl http://localhost:8001/health  # auth
curl http://localhost:8003/health  # catalog
```

## Troubleshooting

### Контейнеры не запускаются

```bash
# Проверьте ресурсы Docker
docker system df

# Увеличьте RAM в Docker Desktop:
# Settings → Resources → Advanced → Memory: 8GB+

# Проверьте логи конкретного сервиса
make logs-service SERVICE=postgres
```

### Порт уже занят

```bash
# Найдите процесс на порту
lsof -i :8000

# Или измените порты в .env
```

### Out of memory

```bash
# Запустите только инфраструктуру
make infrastructure-up

# После стабилизации добавьте сервисы
make services-up
```

### Сервис не отвечает

```bash
# Проверьте логи
make logs-service SERVICE=catalog-service

# Перезапустите сервис
docker compose -f docker/docker-compose.yml restart catalog-service

# Пересоберите сервис
make rebuild SERVICE=catalog-service
```

## Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                         NGINX Gateway                          │
│                        (Load Balancer)                          │
└─────────────────┬───────────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐   ┌─────▼─────┐   ┌───▼───┐
│ Auth  │   │  Catalog  │   │Search │  ... (другие сервисы)
│Service│   │  Service  │   │Service│
└───┬───┘   └─────┬─────┘   └───┬───┘
    │             │             │
    └─────────────┼─────────────┘
                  │
┌─────────────────┼─────────────────────────────────────────────┐
│                 │           Backend Network                    │
│  ┌──────────┐ ┌─▼────────┐ ┌────────────┐ ┌──────────────────┐│
│  │PostgreSQL│ │  Redis   │ │Elasticsearch│ │ Kafka + Zookeeper││
│  └──────────┘ └──────────┘ └────────────┘ └──────────────────┘│
│  ┌──────────┐ ┌──────────┐                                     │
│  │ClickHouse│ │  MinIO   │                                     │
│  └──────────┘ └──────────┘                                     │
└───────────────────────────────────────────────────────────────┘
```

## Мониторинг

### Prometheus
- Сбор метрик со всех сервисов
- URL: http://localhost:9090

### Grafana
- Визуализация метрик
- URL: http://localhost:3000
- Данные из Prometheus, Jaeger, Elasticsearch

### Jaeger
- Распределённая трассировка запросов
- URL: http://localhost:16686

## Production Deployment

Для production используйте:

```bash
# С настройками масштабирования и ресурсов
make prod-up
```

Или для Kubernetes (будущая реализация):
```bash
cd k8s/
kubectl apply -f .
```
