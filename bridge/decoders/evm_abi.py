# bridge/decoders/evm_abi.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from web3 import Web3

class EVMAbiDecoder:
    """
    Carrega ABIs e resolve eventos por topic0. Decodifica args usando o padrão web3.
    """
    def __init__(self, abi_files: Optional[List[str]] = None):
        self._events_by_topic: Dict[str, Dict[str, Any]] = {}
        for f in abi_files or []:
            p = Path(f)
            if p.exists():
                data = json.loads(p.read_text())
                abi = data.get("abi", data)  # aceita arquivo já contendo 'abi' ou a lista direto
                self._index_events(abi)

    def _index_events(self, abi: List[Dict[str, Any]]):
        for item in abi:
            if item.get("type") == "event":
                name = item["name"]
                types = ",".join(i["type"] for i in item.get("inputs", []))
                sig = f"{name}({types})"
                topic0 = Web3.keccak(text=sig).hex()
                self._events_by_topic[topic0] = {"name": name, "abi": item}

    def can_decode(self, topic0: str) -> bool:
        return topic0.lower() in self._events_by_topic

    def decode(self, log: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        topics = [t.hex() if hasattr(t, "hex") else str(t) for t in (log.get("topics") or [])]
        if not topics:
            return None
        topic0 = topics[0].lower()
        evt = self._events_by_topic.get(topic0)
        if not evt:
            return None

        # Usa web3 para decodificar
        from web3._utils.events import get_event_data
        from web3._utils.abi import build_event_signature_hex

        # Monta ABI "contract" mínimo
        fake_abi = [evt["abi"]]
        w3 = Web3()  # offline ok
        event_abi = evt["abi"]
        # Reconstroi a assinatura para sanidade (não estritamente necessário)
        _ = build_event_signature_hex(event_abi)

        data = log.get("data") or "0x"
        # Estrutura esperada pelo util
        entry = {
            "address": log.get("address"),
            "topics": topics,
            "data": data,
        }
        decoded = get_event_data(w3.codec, event_abi, entry)
        args = dict(decoded.get("args", {}))
        return {
            "event_name": evt["name"],
            "args": args,
            "address": log.get("address"),
            "topics": topics,
            "data": data,
        }
