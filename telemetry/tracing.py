# telemetry/tracing.py
from __future__ import annotations
import os
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

def init_tracing(service_name: str, exporter: str, otlp_endpoint_env: str) -> None:
    if exporter == "none":
        return
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    if exporter == "otlp":
        endpoint = os.getenv(otlp_endpoint_env, "http://localhost:4317")
        exporter_impl = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    else:
        exporter_impl = ConsoleSpanExporter()

    processor = BatchSpanProcessor(exporter_impl)
    provider.add_span_processor(processor)
