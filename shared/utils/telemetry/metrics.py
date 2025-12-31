from typing import Dict

from opentelemetry import metrics
from opentelemetry.metrics import Counter, Histogram

_counter_defs = {
    # -------- Kafka --------
    "kafka_messages_total" : {
        "description": "Total Kafka messages consumed"
    },
    "kafka_message_errors_total" : {
        "description": "Kafka message processing errors"
    },
    # -------- Clickhouse --------
    "clickhouse_queries_total" : {
        "description": "Total ClickHouse queries"
    },
    "clickhouse_query_errors_total" : {
        "description": "Total ClickHouse query errors"
    },
    # -------- Redis --------
    "redis_calls_total" : {
        "description": "Total Redis calls"
    },
    "redis_call_errors_total" : {
        "description": "Total Redis call errors"
    },
    "redis_cache_hits_total" : {
        "description": "Total Redis cache hits"
    },
    "redis_cache_misses_total" : {
        "description": "Total Redis cache misses"
    },
    # -------- JWT --------
    "jwt_calls_total" : {
        "description": "Total JWT calls"
    },
    "jwt_call_errors_total" : {
        "description": "Total JWT call errors"
    },
    # -------- Auth --------
    "auth_calls_total" : {
        "description": "Total Auth calls"
    },
    "auth_call_errors_total" : {
        "description": "Total Auth call errors"
    },
    # -------- Elasticsearch --------
    "es_queries_total" : {
        "description": "Total Elasticsearch queries"
    },
    # -------- S3 --------
    "s3_requests_total" : {
        "description": "Total S3 requests"
    },
    "s3_request_errors_total" : {
        "description": "Total S3 request errors"
    },
}

_histogram_defs = {
    # -------- Kafka --------
    "kafka_message_processing_seconds" : {
        "description": "Kafka message processing latency",
        "unit": "s"
    },
    # -------- Clickhouse --------
    "clickhouse_query_duration_seconds" : {
        "description": "ClickHouse query duration",
        "unit": "s"
    },
    # -------- Redis --------
    "redis_call_duration_seconds" : {
        "description": "Total Redis call duration",
        "unit": "s"
    },
    # -------- JWT --------
    "jwt_call_duration_seconds" : {
        "description": "JWT call duration",
        "unit": "s"
    },
    # -------- Auth --------
    "auth_call_duration_seconds" : {
        "description": "Auth call duration",
        "unit": "s"
    },
    # -------- Elasticsearch --------
    "es_query_duration_seconds" : {
        "description": "Elasticsearch query duration",
        "unit": "s"
    },
    # -------- S3 --------
    "s3_request_duration_seconds" : {
        "description": "S3 request duration",
        "unit": "s"
    },
}

_counters: Dict[str, Counter] = {}
_histograms: Dict[str, Histogram] = {}

_initialized: bool = False

def init_metrics() -> None:
    global _initialized
    if _initialized:
        return

    meter = metrics.get_meter("shared.telemetry")

    for name, cfg in _counter_defs.items():
        _counters[name] = meter.create_counter(
            name=name,
            description=cfg["description"],
        )

    for name, cfg in _histogram_defs.items():
        _histograms[name] = meter.create_histogram(
            name=name,
            description=cfg["description"],
            unit=cfg.get("unit"),
        )

    _initialized = True

def counter(name: str) -> Counter:
    if name not in _counters:
        raise RuntimeError(f"Counter '{name}' is not initialized")
    return _counters[name]

def histogram(name: str) -> Histogram:
    if name not in _histograms:
        raise RuntimeError(f"Histogram '{name}' is not initialized")
    return _histograms[name]