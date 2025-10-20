# janus/bridge/validation/schemas.py
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Signature:
    node_id: str
    valid: bool
    meta: Dict[str, Any]

@dataclass
class RelayEvent:
    block_hash: str
    payload: Dict[str, Any]
    timestamp: int
    signatures: List[Signature]
