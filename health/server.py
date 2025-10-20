# health/server.py
from __future__ import annotations
import threading
from fastapi import FastAPI
import uvicorn
from core.state_store import StateStore
from telemetry.metrics import READY_GAUGE

def run_health_server(port: int = 8080):
    app = FastAPI(title="Janus Health")

    @app.get("/healthz")
    def healthz():
        # vivo se consegue ler state store
        ok = True
        err = None
        try:
            s = StateStore()
            _ = s.get("dummy", None)
        except Exception as e:
            ok = False
            err = str(e)
        return {"status": "ok" if ok else "error", "error": err}

    @app.get("/readyz")
    def readyz():
        # pronto se já recebeu pelo menos um CHAIN_HEAD das duas chains (quando habilitadas)
        s = StateStore()
        base = s.get("head:base-testnet", {})
        sola = s.get("head:solana-testnet", {})
        ready = bool(base or sola)  # se uma chain estiver desabilitada, ainda consideramos pronto se a outra reportou
        READY_GAUGE.set(1 if ready else 0)
        return {"ready": ready, "base": base, "solana": sola}

    th = threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning"), daemon=True)
    th.start()
    return th
