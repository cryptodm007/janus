# api/admin.py
from __future__ import annotations
import os
from fastapi import APIRouter, Header, HTTPException
from core.state_store import StateStore
from replay.replayer import ReplayService

router = APIRouter(prefix="/admin", tags=["admin"])

def create_admin_router(cfg: dict, emit_raw: callable) -> APIRouter:
    s = StateStore()
    admin_cfg = cfg.get("admin", {}) or {}
    token_env = admin_cfg.get("token_env", "JANUS_ADMIN_TOKEN")
    token_value = os.getenv(token_env, "")
    replay_cfg = cfg.get("replay", {}) or {}
    reproc_cfg = (admin_cfg.get("reprocess") or {})
    max_span_blocks = int(reproc_cfg.get("max_span_blocks", 20000))

    replayer = ReplayService(emit_raw=emit_raw, cfg=cfg)

    def _require_admin(auth: str | None):
        if not admin_cfg.get("enabled", True):
            raise HTTPException(status_code=404, detail="Admin desabilitado")
        if not token_value:
            raise HTTPException(status_code=503, detail="Admin token não configurado")
        if not auth or not auth.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Bearer token ausente")
        if auth.split(" ", 1)[1] != token_value:
            raise HTTPException(status_code=403, detail="Token inválido")

    @router.post("/replay/base")
    def replay_base(from_block: int, to_block: int, authorization: str | None = Header(default=None)):
        _require_admin(authorization)
        if not replay_cfg.get("enabled", True):
            raise HTTPException(status_code=403, detail="Replay desabilitado")
        if to_block < from_block or (to_block - from_block) > max_span_blocks:
            raise HTTPException(status_code=400, detail="Faixa inválida")
        replayer.replay_base_range(from_block, to_block)
        return {"status": "queued", "chain": "base-testnet", "from": from_block, "to": to_block}

    @router.post("/replay/solana")
    def replay_solana(from_slot: int, to_slot: int, authorization: str | None = Header(default=None)):
        _require_admin(authorization)
        if not replay_cfg.get("enabled", True):
            raise HTTPException(status_code=403, detail="Replay desabilitado")
        replayer.replay_solana_range(from_slot, to_slot)
        return {"status": "queued", "chain": "solana-testnet", "from": from_slot, "to": to_slot}

    @router.post("/checkpoints/reset")
    def reset_checkpoints(authorization: str | None = Header(default=None)):
        _require_admin(authorization)
        keys = []
        base_key = (cfg.get("listeners", {}).get("base-testnet", {}).get("checkpoints", {}) or {}).get("key_scan")
        sol_key = (cfg.get("listeners", {}).get("solana-testnet", {}).get("checkpoints", {}) or {}).get("key_scan")
        if base_key: keys.append(base_key)
        if sol_key: keys.append(sol_key)
        for k in keys:
            s.set(k, None)
        return {"status": "ok", "reset_keys": keys}

    @router.post("/reprocess/base/tx")
    def reprocess_base_tx(tx_hash: str, authorization: str | None = Header(default=None)):
        _require_admin(authorization)
        if not tx_hash or not tx_hash.startswith("0x"):
            raise HTTPException(status_code=400, detail="tx_hash inválido")
        head = s.get("head:base-testnet", {}).get("block_number")
        if head is None:
            raise HTTPException(status_code=503, detail="Head desconhecido")
        emit_raw({"chain": "base-testnet", "type": "CHAIN_HEAD", "payload": {"block_number": int(head)}})
        return {"status": "enqueued", "tx_hash": tx_hash}

    @router.post("/reprocess/solana/signature")
    def reprocess_solana_sig(signature: str, authorization: str | None = Header(default=None)):
        _require_admin(authorization)
        if not signature:
            raise HTTPException(status_code=400, detail="signature inválida")
        slot = s.get("head:solana-testnet", {}).get("slot")
        if slot is None:
            raise HTTPException(status_code=503, detail="Head desconhecido")
        emit_raw({"chain": "solana-testnet", "type": "CHAIN_HEAD", "payload": {"slot": int(slot)}})
        return {"status": "enqueued", "signature": signature}

    @router.post("/reprocess/base/contract")
    def reprocess_base_contract(address: str, from_block: int, to_block: int, authorization: str | None = Header(default=None)):
        _require_admin(authorization)
        if not address or not address.startswith("0x"):
            raise HTTPException(status_code=400, detail="address inválido")
        if to_block < from_block or (to_block - from_block) > max_span_blocks:
            raise HTTPException(status_code=400, detail="faixa inválida")
        s.set(f"{(cfg.get('listeners', {}).get('base-testnet', {}).get('checkpoints', {}) or {}).get('per_contract_prefix', 'cp:base:contract:')}{address.lower()}", int(from_block - 1))
        head = s.get("head:base-testnet", {}).get("block_number")
        if head is not None:
            emit_raw({"chain": "base-testnet", "type": "CHAIN_HEAD", "payload": {"block_number": int(head)}})
        return {"status": "queued", "address": address, "from": from_block, "to": to_block}

    return router
