# bridge/base_listener.py
from __future__ import annotations
import time
import threading
from typing import Dict, Any, Callable, List

import yaml
from dotenv import load_dotenv

from bridge.providers.evm_provider import EVMProvider

load_dotenv()

class BaseListener:
    """
    Listener real para Base (EVM-like). Faz:
      - leitura periódica do head (block_number) -> emite CHAIN_HEAD
      - varredura incremental de logs para endereços+topics configurados
    """
    def __init__(self, emit: Callable[[Dict[str, Any]], None], config_path: str = "config/sync.yaml"):
        self.emit = emit
        self._running = False
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        self.cfg = cfg.get("listeners", {}).get("base-testnet", {})
        self.evmap = (yaml.safe_load(open(config_path, "r", encoding="utf-8")).get("event_map", {}) or {}).get("base-testnet", {})
        self.provider = EVMProvider(self.cfg.get("ws_endpoint_env", ""), self.cfg.get("http_endpoint_env", ""))
        self.poll = float(self.cfg.get("poll_interval_sec", 2))
        self.confirmations_required = int(self.cfg.get("confirmations_required", 2))
        self._last_scanned_block = None
        self._lock = threading.Lock()

    def start(self):
        if not self.provider.is_connected():
            raise RuntimeError("BaseListener: provider não conectado")
        self._running = True
        while self._running:
            try:
                head = self.provider.block_number()
                # Emite CHAIN_HEAD
                self.emit({
                    "chain": "base-testnet",
                    "type": "CHAIN_HEAD",
                    "payload": {"block_number": head},
                })

                # Varredura incremental
                with self._lock:
                    if self._last_scanned_block is None:
                        # inicia atrás do head para respeitar confirmações
                        self._last_scanned_block = max(0, head - self.confirmations_required - 5)
                    from_block = self._last_scanned_block + 1
                    # Só varre até (head - confirmations)
                    to_block = max(from_block, head - self.confirmations_required)
                    if to_block >= from_block:
                        for c in (self.cfg.get("contracts") or []):
                            address = c.get("address")
                            topics: List[str] = c.get("topics") or []
                            for log in self.provider.get_logs(address, topics, from_block, to_block):
                                raw = {
                                    "chain": "base-testnet",
                                    "block_number": int(log["blockNumber"], 16) if isinstance(log["blockNumber"], str) else log["blockNumber"],
                                    "tx_hash": log["transactionHash"].hex() if hasattr(log["transactionHash"], "hex") else str(log["transactionHash"]),
                                    "log_index": log["logIndex"],
                                    "type": self.evmap.get("default_type", "BRIDGE_MESSAGE"),
                                    "payload": {
                                        "address": address,
                                        "topics": [t.hex() if hasattr(t, "hex") else str(t) for t in (log.get("topics") or [])],
                                        "data": log.get("data"),
                                    },
                                }
                                self.emit(raw)
                        self._last_scanned_block = to_block
                time.sleep(self.poll)
            except Exception as e:
                # log simples; produção: logging estruturado + backoff
                print(f"[BaseListener] erro: {e}")
                time.sleep(self.poll)

    def stop(self):
        self._running = False
