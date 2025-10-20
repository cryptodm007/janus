# replay/replayer.py
from __future__ import annotations
from typing import Callable, Dict, Any
from core.events import deterministic_event_id
from core.schemas import ChainPointer

class ReplayService:
    """
    Dispara reprocessamento controlado. NÃO lê da chain diretamente aqui;
    apenas cria 'raw events' sintéticos para o EventRouter normalizar/enfileirar,
    garantindo que o pipeline regular (idempotente) seja reaproveitado.
    A coleta real (get_logs/WS) continua a cargo dos listeners.
    """
    def __init__(self, emit_raw: Callable[[Dict[str, Any]], None], cfg: dict):
        self.emit_raw = emit_raw
        self.cfg = cfg

    def replay_base_range(self, from_block: int, to_block: int):
        max_span = int(((self.cfg.get("replay") or {}).get("max_span") or {}).get("base-testnet", 5000))
        if to_block < from_block or (to_block - from_block) > max_span:
            raise ValueError("Faixa inválida para Base")
        # Sinaliza ao pipeline para revarrer (tipo especial)
        raw = {
            "chain": "base-testnet",
            "type": "CHAIN_HEAD",
            "payload": {"block_number": to_block},  # força 'head' a avançar para disparar confirmações
        }
        self.emit_raw(raw)
        # NOTA: A varredura histórica real é feita pelo listener ao detectar lacunas (próxima fase).

    def replay_solana_range(self, from_slot: int, to_slot: int):
        max_span = int(((self.cfg.get("replay") or {}).get("max_span") or {}).get("solana-testnet", 10000))
        if to_slot < from_slot or (to_slot - from_slot) > max_span:
            raise ValueError("Faixa inválida para Solana")
        raw = {
            "chain": "solana-testnet",
            "type": "CHAIN_HEAD",
            "payload": {"slot": to_slot},
        }
        self.emit_raw(raw)
