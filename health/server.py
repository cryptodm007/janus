# health/server.py
from __future__ import annotations
import os, threading
from fastapi import FastAPI, Header, HTTPException
import uvicorn
from core.state_store import StateStore
from telemetry.metrics import READY_GAUGE, CHECKPOINT_BASE, CHECKPOINT_SOL
from replay.replayer import ReplayService

def run_health_server(port: int = 8080, cfg: dict | None = None, emit_raw=None):
    cfg = cfg or {}
    app = FastAPI(title="Janus Health/Admin")
    s = StateStore()

    @app.get("/healthz")
    def healthz():
        ok = True; err = None
        try:
            _ = s.get("dummy", None)
        except Exception as e:
            ok = False; err = str(e)
        return {"status": "ok" if ok else "error", "error": err}

    @app.get("/readyz")
    def readyz():
        base = s.get("head:base-testnet", {})
        sola = s.get("head:solana-testnet", {})
        cpb = s.get((cfg.get("listeners", {}).get("base-testnet", {}) or {}).get("checkpoints", {}).get("key_scan", "cp:base:scan_block"), None)
        cps = s.get((cfg.get("listeners", {}).get("solana-testnet", {}) or {}).get("checkpoints", {}).get("key_scan", "cp:sol:scan_slot"), None)
        if cpb is not None:
            CHECKPOINT_BASE.set(float(cpb))
        if cps is not None:
            CHECKPOINT_SOL.set(float(cps))
        ready = bool(base or sola)
        READY_GAUGE.set(1 if ready else 0)
        return {"ready": ready, "base": base, "solana": sola, "checkpoints": {"base": cpb, "solana": cps}}

    # Admin / Auth
    admin_cfg = cfg.get("admin", {}) or {}
    replay_cfg = cfg.get("replay", {}) or {}
    reproc_cfg = (admin_cfg.get("reprocess") or {})
    admin_enabled = bool(admin_cfg.get("enabled", True))
    token_env = admin_cfg.get("token_env", "JANUS_ADMIN_TOKEN")
    token_value = os.getenv(token_env, "")
    max_span_blocks = int(reproc_cfg.get("max_span_blocks", 20000))

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
        if not replay_cfg.get("enabled", True) or not replayer:
            raise HTTPException(status_code=503, detail="Replay indisponível")
        if to_block < from_block or (to_block - from_block) > max_span_blocks:
            raise HTTPException(status_code=400, detail="Faixa inválida")
        replayer.replay_base_range(from_block, to_block)
        return {"status": "queued", "chain": "base-testnet", "from": from_block, "to": to_block}

    @app.post("/admin/replay/solana")
    def admin_replay_solana(from_slot: int, to_slot: int, authorization: str | None = Header(default=None)):
        _require_admin(authorization)
        if not replay_cfg.get("enabled", True) or not replayer:
            raise HTTPException(status_code=503, detail="Replay indisponível")
        replayer.replay_solana_range(from_slot, to_slot)
        return {"status": "queued", "chain": "solana-testnet", "from": from_slot, "to": to_slot}

    @app.post("/admin/checkpoints/reset")
    def admin_reset_checkpoints(authorization: str | None = Header(default=None)):
        _require_admin(authorization)
        keys = [
            (cfg.get("listeners", {}).get("base-testnet", {}).get("checkpoints", {}) or {}).get("key_scan", "cp:base:scan_block"),
            (cfg.get("listeners", {}).get("solana-testnet", {}).get("checkpoints", {}) or {}).get("key_scan", "cp:sol:scan_slot"),
        ]
        for k in keys:
            if k:
                s.set(k, None)
        return {"status": "ok", "reset_keys": keys}

    @app.post("/admin/reprocess/base/contract")
    def admin_reprocess_base_contract(address: str, from_block: int, to_block: int, authorization: str | None = Header(default=None)):
        _require_admin(authorization)
        if not address or not address.startswith("0x"):
            raise HTTPException(status_code=400, detail="address inválido")
        if to_block < from_block or (to_block - from_block) > max_span_blocks:
            raise HTTPException(status_code=400, detail="faixa inválida")
        s.set(f"{(cfg.get('listeners', {}).get('base-testnet', {}).get('checkpoints', {}) or {}).get('per_contract_prefix', 'cp:base:contract:')}{address.lower()}", int(from_block - 1))
        head = s.get("head:base-testnet", {}).get("block_number")
        if head is not None and emit_raw:
            emit_raw({"chain": "base-testnet", "type": "CHAIN_HEAD", "payload": {"block_number": int(head)}})
        return {"status": "queued", "address": address, "from": from_block, "to": to_block}

    th = threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning"), daemon=True)
    th.start()
    return th
