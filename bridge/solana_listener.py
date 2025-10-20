# bridge/solana_listener.py
from __future__ import annotations
import time
from typing import Dict, Any, Callable

class SolanaListener:
    """
    Listener simplificado para Solana — mockado nesta fase.
    Substituir por websockets RPC/Logs na Fase 19.
    """
    def __init__(self, emit: Callable[[Dict[str, Any]], None], poll_interval: float = 3.0):
        self.emit = emit
        self.poll_interval = poll_interval
        self._running = False

    def start(self):
        self._running = True
        while self._running:
            raw = {
                "chain": "solana-testnet",
                "slot": 12345678,
                "type": "AGENT_SIGNAL",
                "payload": {"agent_id": "pfnet:node:001", "signal": "HEARTBEAT"},
            }
            self.emit(raw)
            time.sleep(self.poll_interval)

    def stop(self):
        self._running = False
