# health/server.py
from __future__ import annotations
import os, threading
from fastapi import FastAPI, Header, HTTPException
import uvicorn
from core.state_store import StateStore
from telemetry.metrics import READY_GAUGE
from replay.replayer import ReplayService

def run_health_server(port: int = 8080, cfg: dict | None = None, emit_raw=None):
    cfg = cfg or {}
    app = FastAPI(title="Janus Health/Admin")
    s = StateStore()

    @app.get("/healthz")
    def healthz():
        ok = True
        err = None
        try:
            _ = s.get("dummy", None)
        except Exception as e:
            ok = False
            err = str(e)
        return {"status": "ok" if ok else "error", "error": err}

    @app.get("/readyz")
    def readyz():
        base = s.get("head:base-testnet", {})
        sola = s.get("head:solana-testnet", {})
        ready = bool(base or sola)
        READY_GAUGE.set(1 if ready else 0)
        return {"ready": ready, "base": base, "solana": sola}

    # -------- Admin (opcional) --------
    admin_cfg = cfg.get("admin", {}) or {}
    replay_cfg = cfg.get("replay", {}) or {}
    admin_enabled = bool(admin_cfg.get("enabled", True))
    token_env = admin_cfg.get("token_env", "JANUS_ADMIN_TOKEN")
    token_value = os.getenv(token_env, "")

    replayer = ReplayService(emit_raw=emit_raw, cfg=cfg) if emit_raw else None

    def _require_admin(auth: str | None):
        if not admin_enabled:
            raise HTTPException(status_code=404, detail="Admin desabilitado")
        if not token_value:
            raise HTTPException(status_code=503, detail="Admin token não configurado")
        if not auth or not auth.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Bearer token ausente")
        if auth.split(" ", 1)[1] != token_value:
            raise HTTPException(status_code=403, detail="Token inválido")

    @app.post("/admin/replay/base")
    def admin_replay_base(from_block: int, to_block: int, authorization: str | None = Header(default=None)):
        _require_admin(authorization)
        if not replay_cfg.get("enabled", True):
            raise HTTPException(status_code=403, detail="Replay desabilitado")
        if not replayer:
            raise HTTPException(status_code=503, detail="Replayer indisponível")
        replayer.replay_base_range(from_block, to_block)
        return {"status": "queued", "chain": "base-testnet", "from": from_block, "to": to_block}

    @app.post("/admin/replay/solana")
    def admin_replay_solana(from_slot: int, to_slot: int, authorization: str | None = Header(default=None)):
        _require_admin(authorization)
        if not replay_cfg.get("enabled", True):
            raise HTTPException(status_code=403, detail="Replay desabilitado")
        if not replayer:
            raise HTTPException(status_code=503, detail="Replayer indisponível")
        replayer.replay_solana_range(from_slot, to_slot)
        return {"status": "queued", "chain": "solana-testnet", "from": from_slot, "to": to_slot}

    th = threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning"), daemon=True)
    th.start()
    return th
