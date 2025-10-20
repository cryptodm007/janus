# bridge/base_listener.py
from __future__ import annotations
import time
from typing import Dict, Any, Callable, Optional

class BaseListener:
    """
    Listener simplificado para Base (EVM-like) — mockado nesta fase.
    Substituir por web3.py com filtros reais na Fase 19.
    """
    def __init__(self, emit: Callable[[Dict[str, Any]], None], poll_interval: float = 2.0):
        self.emit = emit
        self.poll_interval = poll_interval
        self._running = False

    def start(self):
        self._running = True
        # Mock: em produção, conecte em websockets de logs.
        while self._running:
            # Exemplo de evento fictício
            raw = {
                "chain": "base-testnet",
                "block_number": 1234567,
                "tx_hash": "0xabc123",
                "log_index": 0,
                "type": "BRIDGE_MESSAGE",
                "payload": {"direction": "base->solana", "amount": "1000000000000000000", "asset": "USDC"},
            }
            self.emit(raw)
            time.sleep(self.poll_interval)

    def stop(self):
        self._running = False
