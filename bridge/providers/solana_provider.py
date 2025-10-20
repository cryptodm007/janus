# bridge/providers/solana_provider.py
from __future__ import annotations
import os
from typing import Optional, List, Dict, Any
from solana.rpc.api import Client as SolanaClient
from solana.rpc.websocket_api import connect as solana_ws_connect
from websockets.exceptions import ConnectionClosed
import asyncio

class SolanaProvider:
    def __init__(self, ws_env: str, http_env: str):
        self.ws_endpoint = os.getenv(ws_env, "")
        self.http_endpoint = os.getenv(http_env, "")
        if not self.http_endpoint:
            raise RuntimeError("SOLANA_HTTP_ENDPOINT não configurado")
        self.http = SolanaClient(self.http_endpoint)

    def get_slot(self, commitment: str = "confirmed") -> int:
        resp = self.http.get_slot(commitment=commitment)
        if resp.get("result") is None:
            raise RuntimeError(f"Erro ao obter slot: {resp}")
        return int(resp["result"])

    def get_block_height(self, commitment: str = "confirmed") -> int:
        resp = self.http.get_block_height(commitment=commitment)
        if resp.get("result") is None:
            raise RuntimeError(f"Erro ao obter block_height: {resp}")
        return int(resp["result"])

    async def ws_subscribe_logs(self, program_ids: List[str], on_log):
        if not self.ws_endpoint:
            raise RuntimeError("SOLANA_WS_ENDPOINT não configurado")
        async with solana_ws_connect(self.ws_endpoint) as ws:
            subs_ids = []
            for pid in program_ids:
                sub_id = await ws.logs_subscribe({"mentions": [pid]}, commitment="confirmed")
                subs_ids.append(sub_id)
            try:
                while True:
                    msg = await ws.recv()
                    # Estrutura: {"result": {..., "value": {"signature": "...", "err": None, "logs": [...], "slot": ...}}}
                    value = msg.get("params", {}).get("result", {}).get("value", {})
                    if value:
                        await on_log(value)
            except ConnectionClosed:
                return
