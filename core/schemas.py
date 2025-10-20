# core/schemas.py
from __future__ import annotations
from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

ChainName = Literal["base-testnet", "solana-testnet"]

class ChainPointer(BaseModel):
    chain: ChainName
    block_number: Optional[int] = None         # Base/EVM-like
    slot: Optional[int] = None                 # Solana
    tx_hash: Optional[str] = None
    log_index: Optional[int] = None

class CoreEvent(BaseModel):
    id: str = Field(..., description="Determinístico p/ idempotência (tx_hash+log_index ou hash do payload)")
    type: Literal["TRANSFER", "ORACLE_UPDATE", "AGENT_SIGNAL", "BRIDGE_MESSAGE", "CHAIN_HEAD"]
    payload: Dict[str, Any]
    source: ChainPointer
    observed_at: float

class JobEnvelope(BaseModel):
    job_id: str
    event: CoreEvent
    attempts: int = 0
    max_attempts: int = 5
    next_run_at: float
    acked: bool = False
    error: Optional[str] = None
