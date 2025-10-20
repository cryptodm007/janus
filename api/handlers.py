# janus/api/handlers.py
import json
import time
from typing import Tuple
from http import HTTPStatus

from core.observability.metrics import metrics
from core.observability import logger
from core.state_manager import StateManager
from .auth import check_scope, SCOPE_HEALTH, SCOPE_STATE_R, SCOPE_METRICS

def _json(data: dict) -> Tuple[int, bytes, str]:
    return (HTTPStatus.OK, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

def handle_health(state: StateManager, *, scopes) -> Tuple[int, bytes, str]:
    if not check_scope(scopes, SCOPE_HEALTH):
        return (HTTPStatus.FORBIDDEN, b'{"error":"forbidden"}', "application/json")
    payload = {
        "status": "ok",
        "time": int(time.time()),
        "last_state_ts": state.get_last_update() if hasattr(state, "get_last_update") else None,
    }
    return _json(payload)

def handle_state(state: StateManager, *, scopes) -> Tuple[int, bytes, str]:
    if not check_scope(scopes, SCOPE_STATE_R):
        return (HTTPStatus.FORBIDDEN, b'{"error":"forbidden"}', "application/json")
    data = state.get_state() if hasattr(state, "get_state") else {}
    return _json({"state": data})

def handle_metrics(*, scopes) -> Tuple[int, bytes, str]:
    if not check_scope(scopes, SCOPE_METRICS):
        return (HTTPStatus.FORBIDDEN, b'forbidden', "text/plain; charset=utf-8")
    text = metrics.export_text()
    return (HTTPStatus.OK, text.encode("utf-8"), "text/plain; version=0.0.4; charset=utf-8")
