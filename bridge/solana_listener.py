# bridge/solana_listener.py
from __future__ import annotations
import time
import asyncio
import threading
from typing import Dict, Any, Callable, List

import yaml
from dotenv import load_dotenv

from bridge.providers.solana_provider import SolanaProvider

load_dotenv()

class SolanaListener:
    """
    Listener real para Solana:
      - Emite CHAIN_HEAD (slot/block_height) via HTTP client
      - Assina logs via WebSocket para os program_ids configurados
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
        self._ws_thread: threading.Thread | None = None

    def _emit_chain_head_loop(self):
        # Thread apenas para head periódico
        while self._running:
            try:
                slot = self.provider.get_slot("confirmed")
                self.emit({
                    "chain": "solana-testnet",
                    "type": "CHAIN_HEAD",
                    "payload": {"slot": slot},
                })
            except Exception as e:
                print(f"[SolanaListener] head erro: {e}")
            time.sleep(self.poll)

    async def _on_log(self, value: Dict[str, Any]):
        # value: {"signature": "...", "err": None, "logs": [...], "slot": ...}
        raw = {
            "chain": "solana-testnet",
            "slot": value.get("slot"),
            "type": self.evmap.get("default_type", "AGENT_SIGNAL"),
            "payload": {
                "signature": value.get("signature"),
                "err": value.get("err"),
                "logs": value.get("logs") or [],
            },
        }
        self.emit(raw)

    async def _ws_logs_task(self):
        programs: List[str] = self.cfg.get("programs") or []
        await self.provider.ws_subscribe_logs(programs, self._on_log)

    def start(self):
        self._running = True
        # 1) head thread
        t = threading.Thread(target=self._emit_chain_head_loop, daemon=True)
        t.start()
        self._ws_thread = t

        # 2) websocket loop
        try:
            asyncio.run(self._ws_logs_task())
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"[SolanaListener] ws erro: {e}")

    def stop(self):
        self._running = False
