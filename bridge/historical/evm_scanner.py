# bridge/historical/evm_scanner.py
from __future__ import annotations
from typing import List, Dict, Any, Callable, Optional
from bridge.providers.evm_provider import EVMProvider
from telemetry.metrics import EVENTS_TOTAL, EVENTS_DECODE_ERRORS, CHECKPOINT_BASE, CHECKPOINT_BASE_CONTRACT
from bridge.decoders.evm_abi import EVMAbiDecoder

class EVMHistoricalScanner:
    """
    Scanner histórico paginado por contrato, com checkpoints por address.
    Não emite CHAIN_HEAD; apenas logs normalizados para o EventRouter.
    """
    def __init__(
        self,
        provider: EVMProvider,
        emit: Callable[[Dict[str, Any]], None],
        decoder: Optional[EVMAbiDecoder],
        per_contract_cp_get: Callable[[str], Optional[int]],
        per_contract_cp_set: Callable[[str, int], None],
        default_type: str = "BRIDGE_MESSAGE",
        page_blocks: int = 2000
    ):
        self.provider = provider
        self.emit = emit
        self.decoder = decoder
        self.get_cp = per_contract_cp_get
        self.set_cp = per_contract_cp_set
        self.default_type = default_type
        self.page_blocks = int(page_blocks)

    def scan_range_for_contract(self, address: str, topics: List[str], from_block: int, to_block: int):
        cur_from = int(from_block)
        to_block = int(to_block)
        while cur_from <= to_block:
            cur_to = min(cur_from + self.page_blocks - 1, to_block)
            logs = self.provider.get_logs(address, topics, cur_from, cur_to)
            for log in logs:
                try:
                    topic0 = log.get("topics", [None])[0]
                    t0 = topic0.hex() if hasattr(topic0, "hex") else str(topic0) if topic0 else ""
                    decoded = None
                    if t0 and self.decoder and self.decoder.can_decode(t0):
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
                        "type": self.default_type,
                        "payload": payload,
                    }
                    EVENTS_TOTAL.labels(chain="base-testnet", type=raw["type"]).inc()
                    self.emit(raw)
                except Exception as e:
                    EVENTS_DECODE_ERRORS.labels(chain="base-testnet", where="historical_scan").inc()
            # atualiza CP por contrato
            self.set_cp(address, cur_to)
            CHECKPOINT_BASE_CONTRACT.labels(address=address).set(cur_to)
            CHECKPOINT_BASE.set(cur_to)
            cur_from = cur_to + 1
