# bridge/base_listener.py
from __future__ import annotations
import time
import threading
from typing import Dict, Any, Callable, List, Optional

import yaml
from dotenv import load_dotenv

from bridge.providers.evm_provider import EVMProvider
from bridge.decoders.evm_abi import EVMAbiDecoder
from bridge.historical.evm_scanner import EVMHistoricalScanner
from telemetry.metrics import EVENTS_TOTAL, EVENTS_DECODE_ERRORS, CHAIN_HEAD_GAUGE, CHECKPOINT_BASE, CHECKPOINT_BASE_CONTRACT
from core.state_store import StateStore
from resilience.circuit_breaker import CircuitBreaker
from resilience.adaptive_poll import AdaptivePoll

load_dotenv()

class BaseListener:
    """
    Listener para Base (EVM-like) com:
      - Emissão periódica de CHAIN_HEAD
      - Varredura incremental + catch-up de gaps (checkpoint global)
      - Scanner histórico dedicado por contrato (checkpoints por address)
      - Decodificação ABI, Circuit breaker e Adaptive polling
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

        hist_cfg = self.cfg.get("historical_scan", {}) or {}
        self.hscan_enabled = bool(hist_cfg.get("enabled", True))
        self.hscan_page = int(hist_cfg.get("page_blocks", 2000))
        self.hscan_start = hist_cfg.get("start_from", "auto")
        self.hscan_margin = int(hist_cfg.get("margin_confirmations", 256))

        cb_cfg = self.cfg.get("circuit_breaker", {}) or {}
        self.cb = CircuitBreaker(window_errors=int(cb_cfg.get("window_errors", 5)),
                                 reset_after_sec=float(cb_cfg.get("reset_after_sec", 20)))

        self._lock = threading.Lock()
        self.state = StateStore()

        # CPs: global e por contrato
        self.cp_key_global = (self.cfg.get("checkpoints", {}) or {}).get("key_scan", "cp:base:scan_block")
        self.cp_prefix_addr = (self.cfg.get("checkpoints", {}) or {}).get("per_contract_prefix", "cp:base:contract:")
        self._last_scanned_block: Optional[int] = self.state.get(self.cp_key_global, None)

        abi_files = self.cfg.get("abi_files") or []
        self.decoder = EVMAbiDecoder(abi_files=abi_files)

        # Scanner histórico dedicado
        self.hscanner = EVMHistoricalScanner(
            provider=self.provider,
            emit=self.emit,
            decoder=self.decoder,
            per_contract_cp_get=lambda addr: self.state.get(self.cp_prefix_addr + addr.lower()),
            per_contract_cp_set=lambda addr, v: self.state.set(self.cp_prefix_addr + addr.lower(), int(v)),
            default_type=self.evmap.get("default_type", "BRIDGE_MESSAGE"),
            page_blocks=self.hscan_page
        )

    def _emit_chain_head(self, head: int):
        CHAIN_HEAD_GAUGE.labels(chain="base-testnet", unit="block").set(head)
        self.emit({"chain": "base-testnet", "type": "CHAIN_HEAD", "payload": {"block_number": head}})

    def _scan_range_live(self, from_block: int, to_block: int):
        for c in (self.cfg.get("contracts") or []):
            address = c.get("address")
            topics: List[str] = c.get("topics") or []
            for log in self.provider.get_logs(address, topics, from_block, to_block):
                try:
                    t0 = log.get("topics", [None])[0]
                    topic0 = t0.hex() if hasattr(t0, "hex") else str(t0) if t0 else ""
                    decoded = None
                    if topic0 and self.decoder and self.decoder.can_decode(topic0):
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
        # atualiza CP global
        CHECKPOINT_BASE.set(to_block)
        self.state.set(self.cp_key_global, int(to_block))

    def _catch_up_global(self, head: int):
        with self._lock:
            start = self._last_scanned_block
            if start is None:
                start = max(0, head - self.confirmations_required - 500)
            target = max(start, head - self.confirmations_required)
            total = max(0, target - start)
            if total == 0:
                return
            cur_from = start + 1
            remaining = min(self.max_backfill, total)
            while remaining > 0 and self._running:
                step = min(self.batch_blocks, remaining)
                cur_to = cur_from + step - 1
                self._scan_range_live(cur_from, cur_to)
                self._last_scanned_block = cur_to
                cur_from = cur_to + 1
                remaining -= step
                self.adapt.faster()

    def _historical_auto_start(self, head: int) -> int:
        """
        Decide ponto inicial para scanner histórico:
          - menor CP entre contratos (se existir), senão head - margin_confirmations.
        """
        start_candidates = []
        for c in (self.cfg.get("contracts") or []):
            addr = (c.get("address") or "").lower()
            if not addr:
                continue
            cp = self.state.get(self.cp_prefix_addr + addr)
            if cp is not None:
                start_candidates.append(int(cp))
        if start_candidates:
            return min(start_candidates)
        return max(0, head - self.hscan_margin)

    def _historical_scan_all_contracts(self, from_block: int, to_block: int):
        for c in (self.cfg.get("contracts") or []):
            addr = (c.get("address") or "").lower()
            if not addr:
                continue
            topics: List[str] = c.get("topics") or []
            # ponto de partida por contrato (respeita CP por address)
            cp = self.state.get(self.cp_prefix_addr + addr)
            start = int(from_block if cp is None else max(cp, from_block))
            if start >= to_block:
                continue
            self.hscanner.scan_range_for_contract(addr, topics, start + 1, to_block)

    def start(self):
        if not self.provider.is_connected():
            raise RuntimeError("BaseListener: provider não conectado")
        self._running = True
        while self._running:
            try:
                if not self.cb.allow():
                    time.sleep(self.adapt.interval()); continue

                head = self.provider.block_number()
                self._emit_chain_head(head)

                # 1) catch-up “ao vivo” até head - confirmations (CP global)
                self._catch_up_global(head)

                # 2) scanner histórico dedicado (por contrato), quando habilitado
                if self.hscan_enabled:
                    if self.hscan_start == "auto":
                        h_from = self._historical_auto_start(head)
                    else:
                        h_from = int(self.hscan_start)
                    h_to = max(h_from, head - self.confirmations_required)
                    if h_to > h_from:
                        self._historical_scan_all_contracts(h_from, h_to)

                # relaxa
                self.adapt.slower()
                self.cb.on_success()
                time.sleep(self.adapt.interval())
            except Exception as e:
                print(f"[BaseListener] erro: {e}")
                self.cb.on_error()
                self.adapt.slower()
                time.sleep(self.adapt.interval())

    def stop(self):
        self._running = False
