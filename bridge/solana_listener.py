# bridge/solana_listener.py
from __future__ import annotations
import time
import asyncio
import threading
from typing import Dict, Any, Callable, List, Optional

import yaml
from dotenv import load_dotenv

from bridge.providers.solana_provider import SolanaProvider
from bridge.decoders.solana_borsh import SolanaBorshDecoder
from telemetry.metrics import EVENTS_TOTAL, EVENTS_DECODE_ERRORS, CHAIN_HEAD_GAUGE
from core.state_store import StateStore
from resilience.circuit_breaker import CircuitBreaker
from resilience.adaptive_poll import AdaptivePoll

load_dotenv()

class SolanaListener:
    """
    Listener para Solana:
      - Emite CHAIN_HEAD (slot) periódico
      - WS logs para programs configurados
      - Catch-up de gaps por slot com checkpoint
      - Circuit breaker e adaptive polling
    """
    def __init__(self, emit: Callable[[Dict[str, Any]], None], config_path: str = "config/sync.yaml"):
        self.emit = emit
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        self.cfg = (cfg.get("listeners", {}) or {}).get("solana-testnet", {}) or {}
        self.evmap = (cfg.get("event_map", {}) or {}).get("solana-testnet", {}) or {}
        self.provider = SolanaProvider(self.cfg.get("ws_endpoint_env", ""), self.cfg.get("http_endpoint_env", ""))
        self.confirmations_required = int(self.cfg.get("confirmations_required", 1))
        self.poll = float(self.cfg.get("poll_interval_sec", 3.0))
        self.adapt = AdaptivePoll(
            base=self.poll,
            min_interval=float(self.cfg.get("min_poll_sec", 0.5)),
            max_interval=float(self.cfg.get("max_poll_sec", 6.0)),
        )
        gap_cfg = self.cfg.get("gap_scan", {}) or {}
        self.batch_slots = int(gap_cfg.get("batch_slots", 2000))
        self.max_backfill = int(gap_cfg.get("max_backfill", 50000))

        cb_cfg = self.cfg.get("circuit_breaker", {}) or {}
        self.cb = CircuitBreaker(window_errors=int(cb_cfg.get("window_errors", 5)),
                                 reset_after_sec=float(cb_cfg.get("reset_after_sec", 20)))

        self._running = False
        self._head_thread: threading.Thread | None = None
        self._state = StateStore()
        self.cp_key = (self.cfg.get("checkpoints", {}) or {}).get("key_scan", "cp:sol:scan_slot")
        self._last_scanned_slot: Optional[int] = self._state.get(self.cp_key, None)

        layouts = self.cfg.get("borsh_layouts") or {}
        self.decoder = SolanaBorshDecoder(layouts=layouts)

    def _emit_chain_head_once(self):
        try:
            slot = self.provider.get_slot("confirmed")
            CHAIN_HEAD_GAUGE.labels(chain="solana-testnet", unit="slot").set(slot)
            self.emit({"chain": "solana-testnet", "type": "CHAIN_HEAD", "payload": {"slot": slot}})
            return slot
        except Exception as e:
            print(f"[SolanaListener] head erro: {e}")
            raise

    def _emit_chain_head_loop(self):
        while self._running:
            try:
                slot = self._emit_chain_head_once()
                # relaxa se sem pressão
                self.adapt.slower()
                self.cb.on_success()
                time.sleep(self.adapt.interval())
            except Exception:
                self.cb.on_error()
                self.adapt.slower()
                time.sleep(self.adapt.interval())

    def _decode_and_emit_ws(self, value: Dict[str, Any]):
        try:
            programs: List[str] = self.cfg.get("programs") or []
            program_id = programs[0] if programs else "unknown"
            raw_logs: List[str] = value.get("logs") or []
            raw_concat = "\n".join(raw_logs).encode()
            decoded = self.decoder.decode(program_id, raw_concat) or {"logs": raw_logs}

            raw = {
                "chain": "solana-testnet",
                "slot": value.get("slot"),
                "type": self.evmap.get("default_type", "AGENT_SIGNAL"),
                "payload": {"signature": value.get("signature"), "err": value.get("err"), "decoded": decoded},
            }
            EVENTS_TOTAL.labels(chain="solana-testnet", type=raw["type"]).inc()
            self.emit(raw)
            # atividade → acelera
            self.adapt.faster()
        except Exception as e:
            EVENTS_DECODE_ERRORS.labels(chain="solana-testnet", where="decode_or_emit").inc()
            self.emit({
                "chain": "solana-testnet",
                "slot": value.get("slot"),
                "type": self.evmap.get("default_type", "AGENT_SIGNAL"),
                "payload": {"signature": value.get("signature"), "err": value.get("err"), "logs": value.get("logs"), "error": str(e)},
            })

    async def _ws_logs_task(self):
        async def on_log(value):
            self._decode_and_emit_ws(value)
        programs: List[str] = self.cfg.get("programs") or []
        await self.provider.ws_subscribe_logs(programs, on_log)

    def _catch_up(self, head_slot: int):
        """
        Varredura de gaps via HTTP (apenas CHAIN_HEAD para forçar confirmação progressiva).
        Em Solana, logs históricos detalhados exigem estratégias específicas por programa; 
        aqui usamos avanço de head e WS para fluxo vivo.
        """
        with_slot = self._last_scanned_slot if self._last_scanned_slot is not None else (head_slot - self.confirmations_required - 500)
        start = max(0, with_slot)
        target = max(start, head_slot - self.confirmations_required)
        total_backfill = min(self.max_backfill, max(0, target - start))
        if total_backfill == 0:
            return

        cur = start + 1
        while cur <= target and self._running:
            step = min(self.batch_slots, target - cur + 1)
            # Avança o head sinteticamente para dirigir confirmações
            self.emit({"chain": "solana-testnet", "type": "CHAIN_HEAD", "payload": {"slot": cur + step - 1}})
            self._last_scanned_slot = cur + step - 1
            self._state.set(self.cp_key, self._last_scanned_slot)
            cur += step
            self.adapt.faster()

    def start(self):
        self._running = True
        # Thread de head periódico
        t = threading.Thread(target=self._emit_chain_head_loop, daemon=True)
        t.start()
        self._head_thread = t

        # Loop de WS + catch-up cooperando com CB/adapt
        try:
            while self._running:
                if not self.cb.allow():
                    time.sleep(self.adapt.interval())
                    continue
                # tenta head e catch-up antes de iniciar WS (garante progresso)
                head_slot = self._emit_chain_head_once()
                self._catch_up(head_slot)
                # entra no WS até cair
                asyncio.run(self._ws_logs_task())
                # se sair do WS, marca erro para o CB administrar a retomada
                self.cb.on_error()
                self.adapt.slower()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"[SolanaListener] ws loop erro: {e}")

    def stop(self):
        self._running = False
