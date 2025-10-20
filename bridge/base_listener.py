# bridge/base_listener.py
from __future__ import annotations
import time
import threading
from typing import Dict, Any, Callable, List, Optional

import yaml
from dotenv import load_dotenv

from bridge.providers.evm_provider import EVMProvider
from bridge.decoders.evm_abi import EVMAbiDecoder
from telemetry.metrics import EVENTS_TOTAL, EVENTS_DECODE_ERRORS, CHAIN_HEAD_GAUGE
from core.state_store import StateStore
from resilience.circuit_breaker import CircuitBreaker
from resilience.adaptive_poll import AdaptivePoll

load_dotenv()

class BaseListener:
    """
    Listener para Base (EVM-like) com:
      - Head + emissão de CHAIN_HEAD
      - Varredura incremental + catch-up de gaps (checkpoint persistente)
      - Decodificação via ABI
      - Circuit breaker e adaptive polling
    """
    def __init__(self, emit: Callable[[Dict[str, Any]], None], config_path: str = "config/sync.yaml"):
        self.emit = emit
        self._running = False
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        self.cfg = (cfg.get("listeners", {}) or {}).get("base-testnet", {}) or {}
        self.evmap = (cfg.get("event_map", {}) or {}).get("base-testnet", {}) or {}

        self.provider = EVMProvider(self.cfg.get("ws_endpoint_env", ""), self.cfg.get("http_endpoint_env", ""))
        self.confirmations_required = int(self.cfg.get("confirmations_required", 2))
        self.poll = float(self.cfg.get("poll_interval_sec", 2.0))
        self.adapt = AdaptivePoll(
            base=self.poll,
            min_interval=float(self.cfg.get("min_poll_sec", 0.5)),
            max_interval=float(self.cfg.get("max_poll_sec", 5.0)),
        )
        gap_cfg = self.cfg.get("gap_scan", {}) or {}
        self.batch_blocks = int(gap_cfg.get("batch_blocks", 500))
        self.max_backfill = int(gap_cfg.get("max_backfill", 20000))

        cb_cfg = self.cfg.get("circuit_breaker", {}) or {}
        self.cb = CircuitBreaker(window_errors=int(cb_cfg.get("window_errors", 5)),
                                 reset_after_sec=float(cb_cfg.get("reset_after_sec", 20)))

        self._lock = threading.Lock()
        self.state = StateStore()
        self.cp_key = (self.cfg.get("checkpoints", {}) or {}).get("key_scan", "cp:base:scan_block")
        self._last_scanned_block: Optional[int] = self.state.get(self.cp_key, None)

        abi_files = self.cfg.get("abi_files") or []
        self.decoder = EVMAbiDecoder(abi_files=abi_files)

    def _emit_chain_head(self, head: int):
        CHAIN_HEAD_GAUGE.labels(chain="base-testnet", unit="block").set(head)
        self.emit({"chain": "base-testnet", "type": "CHAIN_HEAD", "payload": {"block_number": head}})

    def _scan_range(self, from_block: int, to_block: int):
        for c in (self.cfg.get("contracts") or []):
            address = c.get("address")
            topics: List[str] = c.get("topics") or []
            for log in self.provider.get_logs(address, topics, from_block, to_block):
                try:
                    t0 = log.get("topics", [None])[0]
                    topic0 = t0.hex() if hasattr(t0, "hex") else str(t0) if t0 else ""
                    decoded = None
                    if topic0 and self.decoder.can_decode(topic0):
                        decoded = self.decoder.decode({
                            "address": address,
                            "topics": log.get("topics"),
                            "data": log.get("data"),
                        })
                    payload = decoded or {
                        "address": address,
                        "topics": [t.hex() if hasattr(t, "hex") else str(t) for t in (log.get("topics") or [])],
                        "data": log.get("data"),
                    }
                    raw = {
                        "chain": "base-testnet",
                        "block_number": int(log["blockNumber"], 16) if isinstance(log["blockNumber"], str) else log["blockNumber"],
                        "tx_hash": log["transactionHash"].hex() if hasattr(log["transactionHash"], "hex") else str(log["transactionHash"]),
                        "log_index": log["logIndex"],
                        "type": self.evmap.get("default_type", "BRIDGE_MESSAGE"),
                        "payload": payload,
                    }
                    EVENTS_TOTAL.labels(chain="base-testnet", type=raw["type"]).inc()
                    self.emit(raw)
                except Exception as e:
                    EVENTS_DECODE_ERRORS.labels(chain="base-testnet", where="decode_or_emit").inc()
                    self.emit({
                        "chain": "base-testnet",
                        "block_number": log.get("blockNumber"),
                        "tx_hash": log.get("transactionHash"),
                        "log_index": log.get("logIndex"),
                        "type": self.evmap.get("default_type", "BRIDGE_MESSAGE"),
                        "payload": {"error": str(e)},
                    })

    def _catch_up(self, head: int):
        """
        Varredura de gaps com checkpoint persistente.
        """
        with self._lock:
            start = self._last_scanned_block
            if start is None:
                # inicia um pouco antes do head para respeitar confirmações e cobrir margem
                start = max(0, head - self.confirmations_required - 500)
            # Só pode varrer até (head - confirmations)
            target = max(start, head - self.confirmations_required)
            total_backfill = min(self.max_backfill, max(0, target - start))
            if total_backfill == 0:
                return

            cur_from = start + 1
            remaining = total_backfill
            while remaining > 0 and self._running:
                step = min(self.batch_blocks, remaining)
                cur_to = cur_from + step - 1
                self._scan_range(cur_from, cur_to)
                self._last_scanned_block = cur_to
                self.state.set(self.cp_key, self._last_scanned_block)
                cur_from = cur_to + 1
                remaining -= step
                # acelera polling quando há trabalho
                self.adapt.faster()

    def start(self):
        if not self.provider.is_connected():
            raise RuntimeError("BaseListener: provider não conectado")
        self._running = True
        while self._running:
            try:
                # circuit breaker “abre” o circuito se muitos erros
                if not self.cb.allow():
                    time.sleep(self.adapt.interval())
                    continue

                head = self.provider.block_number()
                self._emit_chain_head(head)
                self._catch_up(head)

                # Se alcançou o alvo, relaxa (slow)
                self.adapt.slower()
                self.cb.on_success()
                time.sleep(self.adapt.interval())
            except Exception as e:
                print(f"[BaseListener] erro: {e}")
                self.cb.on_error()
                # reduz velocidade para aliviar pressão
                self.adapt.slower()
                time.sleep(self.adapt.interval())

    def stop(self):
        self._running = False
