# bridge/providers/evm_provider.py
from __future__ import annotations
import os
import time
from typing import Optional, Dict, Any, List
from web3 import Web3
from web3.types import FilterParams

class EVMProvider:
    def __init__(self, ws_env: str, http_env: str):
        self.ws_endpoint = os.getenv(ws_env, "")
        self.http_endpoint = os.getenv(http_env, "")
        self.w3_ws: Optional[Web3] = None
        self.w3_http: Optional[Web3] = None
        self._connect()

    def _connect(self):
        if self.ws_endpoint:
            self.w3_ws = Web3(Web3.WebsocketProvider(self.ws_endpoint, websocket_timeout=30))
        if self.http_endpoint:
            self.w3_http = Web3(Web3.HTTPProvider(self.http_endpoint, request_kwargs={"timeout": 30}))

    def is_connected(self) -> bool:
        w3 = self.w3_ws or self.w3_http
        return bool(w3 and w3.is_connected())

    def block_number(self) -> int:
        w3 = self.w3_ws or self.w3_http
        if not w3:
            raise RuntimeError("EVMProvider: sem provedor conectado")
        return w3.eth.block_number

    def get_logs(self, address: str, topics: List[str], from_block: int, to_block: int) -> List[Dict[str, Any]]:
        w3 = self.w3_ws or self.w3_http
        if not w3:
            raise RuntimeError("EVMProvider: sem provedor conectado")
        params: FilterParams = {
            "address": Web3.to_checksum_address(address),
            "fromBlock": from_block,
            "toBlock": to_block,
            "topics": topics or None,
        }
        return w3.eth.get_logs(params)

    def tx_receipt(self, tx_hash: str) -> Dict[str, Any]:
        w3 = self.w3_ws or self.w3_http
        if not w3:
            raise RuntimeError("EVMProvider: sem provedor conectado")
        return dict(w3.eth.get_transaction_receipt(tx_hash))
