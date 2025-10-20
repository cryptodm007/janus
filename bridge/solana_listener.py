# bridge/solana_listener.py
from __future__ import annotations
import time
import asyncio
import threading
from typing import Dict, Any, Callable, List

import yaml
from dotenv import load_dotenv

from bridge.providers.solana_provider import SolanaProvider
from bridge.decoders.solana_borsh import SolanaBorshDecoder
from telemetry.metrics import EVENTS_TOTAL, EVENTS_DECODE_ERRORS, CHAIN_HEAD_GAUGE

load_dotenv()

class SolanaListener:
    """
    Listener real para Solana:
      - Emite CHAIN_HEAD (slot) via HTTP client
      - Assina logs via WebSocket para os program_ids configurados
      - Decodifica logs com Borsh quando layout está configurado
    """
    def __init__(self, emit: Callable[[Dict[str, Any]], None], config_path: str = "config/sync.yaml"):
        self.emit = emit
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        self.cfg = cfg.get("listeners", {}).get("solana-testnet", {})
        self.evmap = (yaml.safe_load(open(config_path, "r", encoding="utf-8")).get("event_map", {}) or {}).get("solana-testnet", {})
        self.provider = SolanaProvider(self.cfg.get("ws_endpoint_env", ""), self.cfg.get("http_endpoint_env", ""))
        self.poll = float(self.cfg.get("poll_interval_sec", 3))
        self._running = False
        self._head_thread: threading.Thread | None = None

        layouts = self.cfg.get("borsh_layouts") or {}
        self.decoder = SolanaBorshDecoder(layouts=layouts)

    def _emit_chain_head_loop(self):
        while self._running:
            try:
                slot = self.provider.get_slot("confirmed")
                CHAIN_HEAD_GAUGE.labels(chain="solana-testnet", unit="slot").set(slot)
                self.emit({
                    "chain": "solana-testnet",
                    "type": "CHAIN_HEAD",
                    "payload": {"slot": slot},
                })
            except Exception as e:
                print(f"[SolanaListener] head erro: {e}")
            time.sleep(self.poll)

    async def _on_log(self, value: Dict[str, Any]):
        # Estrutura: {"signature": "...", "err": None, "logs": [...], "slot": ...}
        try:
            # Muitas vezes o dado vem em base64 nos logs do programa; aqui supomos logs textuais.
            # Caso utilize data base64, adapte para passar raw_bytes no decoder.
            program_ids: List[str] = (self.cfg.get("programs") or [])
            program_id = program_ids[0] if program_ids else "unknown"
            raw_logs: List[str] = value.get("logs") or []
            raw_concat = "\n".join(raw_logs).encode()
            decoded = self.decoder.decode(program_id, raw_concat) or {"logs": raw_logs}

            raw = {
                "chain": "solana-testnet",
                "slot": value.get("slot"),
                "type": self.evmap.get("default_type", "AGENT_SIGNAL"),
                "payload": {
                    "signature": value.get("signature"),
                    "err": value.get("err"),
                    "decoded": decoded,
                },
            }
            EVENTS_TOTAL.labels(chain="solana-testnet", type=raw["type"]).inc()
            self.emit(raw)
        except Exception as e:
            EVENTS_DECODE_ERRORS.labels(chain="solana-testnet", where="decode_or_emit").inc()
            self.emit({
                "chain": "solana-testnet",
                "slot": value.get("slot"),
                "type": self.evmap.get("default_type", "AGENT_SIGNAL"),
                "payload": {"signature": value.get("signature"), "err": value.get("err"), "logs": value.get("logs"), "error": str(e)},
            })

    async def _ws_logs_task(self):
        programs: List[str] = self.cfg.get("programs") or []
        await self.provider.ws_subscribe_logs(programs, self._on_log)

    def start(self):
        self._running = True
        # thread de head
        t = threading.Thread(target=self._emit_chain_head_loop, daemon=True)
        t.start()
        self._head_thread = t

        # loop ws
        try:
            asyncio.run(self._ws_logs_task())
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"[SolanaListener] ws erro: {e}")

    def stop(self):
        self._running = False
