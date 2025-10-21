# telemetry/metrics.py
from __future__ import annotations
from typing import Optional
from prometheus_client import Counter, Histogram, Gauge, start_http_server

METRICS_STARTED = False

# Contadores e histogramas
EVENTS_TOTAL = Counter("janus_events_total", "Eventos recebidos", ["chain", "type"])
EVENTS_DECODE_ERRORS = Counter("janus_decode_errors_total", "Falhas de decodificação", ["chain", "where"])
JOBS_PROCESSED = Counter("janus_jobs_processed_total", "Jobs processados")
JOBS_FAILED = Counter("janus_jobs_failed_total", "Jobs falhados")
APPLY_LATENCY = Histogram("janus_apply_event_seconds", "Latência do apply_event")
CHAIN_HEAD_GAUGE = Gauge("janus_chain_head", "Head por cadeia", ["chain", "unit"])  # unit: block|slot
READY_GAUGE = Gauge("janus_ready", "Sinalização de prontidão (0/1)")

# Métricas de checkpoint (novas)
CHECKPOINT_BASE = Gauge("janus_checkpoint_base", "Último bloco processado (visão global Base)")
CHECKPOINT_SOL = Gauge("janus_checkpoint_solana", "Último slot processado (visão global Solana)")
CHECKPOINT_BASE_CONTRACT = Gauge("janus_checkpoint_base_contract", "Checkpoint por contrato (Base)", ["address"])

def ensure_metrics_server(port: int = 9090):
    global METRICS_STARTED
    if not METRICS_STARTED:
        start_http_server(port)
        METRICS_STARTED = True
