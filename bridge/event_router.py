# bridge/event_router.py
from __future__ import annotations
import time
from typing import Dict, Any, Callable
from core.schemas import CoreEvent, ChainPointer
from core.events import deterministic_event_id

class EventRouter:
    """
    Normaliza eventos de diferentes chains e entrega para o handler (ex.: job_queue.enqueue).
    """
    def __init__(self, handler: Callable[[CoreEvent], None]):
        self.handler = handler

    def _normalize(self, raw: Dict[str, Any]) -> CoreEvent:
        # Espera-se que raw contenha: chain, tx_hash/slot, log_index (quando houver), type, payload
        source = ChainPointer(
            chain=raw["chain"],
            block_number=raw.get("block_number"),
            slot=raw.get("slot"),
            tx_hash=raw.get("tx_hash"),
            log_index=raw.get("log_index"),
        )
        payload = raw.get("payload", {})
        ev_id = deterministic_event_id(source.dict(), payload)
        return CoreEvent(
            id=ev_id,
            type=raw["type"],
            payload=payload,
            source=source,
            observed_at=time.time(),
        )

    def route(self, raw: Dict[str, Any]) -> CoreEvent:
        event = self._normalize(raw)
        self.handler(event)
        return event
