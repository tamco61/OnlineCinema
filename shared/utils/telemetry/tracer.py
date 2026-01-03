"""
OpenTelemetry telemetry setup for Cinema microservices.

Collector-first architecture:
- Traces + Metrics via OTLP
- Auto-instrumentation
- Manual spans for business logic
"""

from contextlib import contextmanager
from typing import Any, Dict, Optional

from fastapi import FastAPI

from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from opentelemetry.trace import SpanKind, Status, StatusCode

import logging

logger = logging.getLogger(__name__)


# ---------------------------
# Telemetry setup
# ---------------------------
def setup_telemetry(
    app: FastAPI,
    service_name: str,
    service_version: str = "1.0.0",
    environment: str = "development",
    otlp_endpoint: str = "http://otel-collector:4318",
    enable_fastapi: bool = True,
    enable_httpx: bool = True,
) -> None:
    """
    Setup OpenTelemetry (traces + metrics) with OTLP → Collector.

    This function MUST be called once at app startup.
    """

    # ---------- Resource ----------
    resource = Resource.create({
        "service.name": service_name,
        "service.version": service_version,
        "deployment.environment": environment,
    })

    # ---------- Tracing ----------
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    trace_exporter = OTLPSpanExporter(
        endpoint=f"{otlp_endpoint}/v1/traces",
    )

    tracer_provider.add_span_processor(
        BatchSpanProcessor(trace_exporter)
    )

    # ---------- Metrics ----------
    metric_exporter = OTLPMetricExporter(
        endpoint=f"{otlp_endpoint}/v1/metrics",
    )

    metric_reader = PeriodicExportingMetricReader(
        metric_exporter,
        export_interval_millis=5000,
    )

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
    )
    metrics.set_meter_provider(meter_provider)

    # ---------- Instrumentation ----------
    if enable_fastapi:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI auto-instrumentation enabled")

    if enable_httpx:
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX auto-instrumentation enabled")

    logger.info(
        "OpenTelemetry initialized",
        extra={
            "service": service_name,
            "version": service_version,
            "environment": environment,
            "collector": otlp_endpoint,
        },
    )


# ---------------------------
# Manual spans (business logic)
# ---------------------------
@contextmanager
def trace_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    kind: SpanKind = SpanKind.INTERNAL,
):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span(name, kind=kind) as span:
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


# ---------------------------
# Helpers
# ---------------------------
def add_span_attribute(key: str, value: Any) -> None:
    span = trace.get_current_span()
    if span:
        span.set_attribute(key, value)


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    span = trace.get_current_span()
    if span:
        span.add_event(name, attributes=attributes or {})


def get_trace_id() -> str:
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, "032x")
    return ""


def get_span_id() -> str:
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().span_id, "016x")
    return ""
