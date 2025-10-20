# core/events.py
from __future__ import annotations
from typing import Dict, Any
from hashlib import sha256

def deterministic_event_id(source: Dict[str, Any], payload: Dict[str, Any]) -> str:
    """
    Gera um ID estável a partir de ponteiros on-chain + payload normalizado.
    """
    base = f"{source.get('chain')}|{source.get('tx_hash')}|{source.get('log_index')}|{source.get('slot')}|{sorted(payload.items())}"
    return sha256(base.encode()).hexdigest()
