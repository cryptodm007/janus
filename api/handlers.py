# janus/api/handlers.py
import json
import time
from typing import Tuple, Dict, Any
from http import HTTPStatus

from core.observability.metrics import metrics
from core.observability import logger
from core.state_manager import StateManager

from core.persistence.store import SnapshotStore
from core.persistence.manifest import SnapshotManifest

from .auth import (
    check_scope,
    SCOPE_HEALTH, SCOPE_STATE_R, SCOPE_METRICS,
    SCOPE_ADMIN_SNAP, SCOPE_ADMIN_REST, SCOPE_ADMIN_PRUNE
)

# -------- helpers de resposta --------
def _json_ok(data: dict) -> Tuple[int, bytes, str]:
    return (HTTPStatus.OK, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

def _json_err(code: int, error: str, detail: Dict[str, Any] | None = None) -> Tuple[int, bytes, str]:
    payload = {"error": error}
    if detail:
        payload["detail"] = detail
    return (code, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

# -------- endpoints públicos (read-only) --------
def handle_health(state: StateManager, *, scopes) -> Tuple[int, bytes, str]:
    if not check_scope(scopes, SCOPE_HEALTH):
        return _json_err(HTTPStatus.FORBIDDEN, "forbidden")
    payload = {
        "status": "ok",
        "time": int(time.time()),
        "last_state_ts": state.get_last_update() if hasattr(state, "get_last_update") else None,
    }
    return _json_ok(payload)

def handle_state(state: StateManager, *, scopes) -> Tuple[int, bytes, str]:
    if not check_scope(scopes, SCOPE_STATE_R):
        return _json_err(HTTPStatus.FORBIDDEN, "forbidden")
    data = state.get_state() if hasattr(state, "get_state") else {}
    return _json_ok({"state": data})

def handle_metrics(*, scopes) -> Tuple[int, bytes, str]:
    if not check_scope(scopes, SCOPE_METRICS):
        return (HTTPStatus.FORBIDDEN, b'forbidden', "text/plain; charset=utf-8")
    text = metrics.export_text()
    return (HTTPStatus.OK, text.encode("utf-8"), "text/plain; version=0.0.4; charset=utf-8")

# -------- endpoints administrativos --------
def handle_admin_snapshot(state: StateManager, *, scopes) -> Tuple[int, bytes, str]:
    """
    Cria um snapshot do estado atual e adiciona ao manifest.
    """
    if not check_scope(scopes, SCOPE_ADMIN_SNAP):
        return _json_err(HTTPStatus.FORBIDDEN, "forbidden")
    try:
        st = state.get_state() if hasattr(state, "get_state") else {}
        store = SnapshotStore()
        meta = store.save(st)
        SnapshotManifest(store.root).add(meta)
        logger.info("admin_snapshot_created", ctx={"trace":"api"}, file=meta.file, size=meta.size_bytes, ts=meta.created_at)
        return _json_ok({
            "file": meta.file,
            "created_at": meta.created_at,
            "size_bytes": meta.size_bytes,
            "checksum": meta.checksum,
            "version": meta.version,
            "compressed": meta.compressed
        })
    except Exception as e:
        logger.error("admin_snapshot_error", ctx={"trace":"api"}, exc=e)
        return _json_err(HTTPStatus.INTERNAL_SERVER_ERROR, "snapshot_failed", {"message": str(e)})

def handle_admin_snapshots_list(*, scopes) -> Tuple[int, bytes, str]:
    if not check_scope(scopes, SCOPE_ADMIN_SNAP):
        return _json_err(HTTPStatus.FORBIDDEN, "forbidden")
    try:
        man = SnapshotManifest()
        return _json_ok({"snapshots": man.list(), "latest": man.latest()})
    except Exception as e:
        return _json_err(HTTPStatus.INTERNAL_SERVER_ERROR, "list_failed", {"message": str(e)})

def handle_admin_restore(state: StateManager, *, scopes, body: Dict[str, Any]) -> Tuple[int, bytes, str]:
    """
    Restaura estado a partir de um arquivo (campo JSON: {"file":"snapshot-<ts>.json[.gz]"}).
    """
    if not check_scope(scopes, SCOPE_ADMIN_REST):
        return _json_err(HTTPStatus.FORBIDDEN, "forbidden")
    try:
        filename = body.get("file", "")
        if not filename:
            return _json_err(HTTPStatus.BAD_REQUEST, "missing_file")
        store = SnapshotStore()
        data = store.load(filename)
        if not hasattr(state, "update_state"):
            return _json_err(HTTPStatus.NOT_IMPLEMENTED, "state_manager_not_writable")
        state.update_state(data)
        logger.info("admin_restore_ok", ctx={"trace":"api"}, file=filename, ts=data.get("timestamp"))
        return _json_ok({"restored_from": filename, "timestamp": data.get("timestamp")})
    except FileNotFoundError:
        return _json_err(HTTPStatus.NOT_FOUND, "file_not_found")
    except Exception as e:
        logger.error("admin_restore_error", ctx={"trace":"api"}, exc=e)
        return _json_err(HTTPStatus.INTERNAL_SERVER_ERROR, "restore_failed", {"message": str(e)})

def handle_admin_prune(*, scopes, body: Dict[str, Any]) -> Tuple[int, bytes, str]:
    """
    Aplica retenção: campos JSON opcionais {"keep_last": N, "keep_days": D}
    """
    if not check_scope(scopes, SCOPE_ADMIN_PRUNE):
        return _json_err(HTTPStatus.FORBIDDEN, "forbidden")
    try:
        keep_last = int(body.get("keep_last", 10))
        keep_days = int(body.get("keep_days", 7))
        man = SnapshotManifest()
        store = SnapshotStore()
        to_delete = man.prune(keep_last=keep_last, keep_days=keep_days)
        for f in to_delete:
            store.delete(f)
        logger.info("admin_prune_ok", ctx={"trace":"api"}, keep_last=keep_last, keep_days=keep_days, deleted=len(to_delete))
        return _json_ok({"deleted": to_delete, "keep_last": keep_last, "keep_days": keep_days})
    except Exception as e:
        logger.error("admin_prune_error", ctx={"trace":"api"}, exc=e)
        return _json_err(HTTPStatus.INTERNAL_SERVER_ERROR, "prune_failed", {"message": str(e)})
