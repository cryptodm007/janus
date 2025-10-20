# services/ai_sync_manager.py
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Dict, Any

from core.schemas import CoreEvent
from core.state_store import StateStore
from core.locks import FileLock
from telemetry.metrics import APPLY_LATENCY, JOBS_PROCESSED, JOBS_FAILED
from security.ed25519 import verify_ed25519

class AISyncManager:
    """
    Aplica eventos ao estado dos agentes (PFNET), confirma cross-chain
    com base no 'head' observado (via eventos CHAIN_HEAD) e mantém snapshots.
    Opcionalmente verifica assinaturas Ed25519 em AGENT_SIGNAL quando presentes.
    """
    def __init__(self, snapshot_path: str = ".runtime/agents_state.json"):
        self.snapshot_path = Path(snapshot_path)
        self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        self.state = StateStore()

        if not self.snapshot_path.exists():
            self._write_snapshot({})

    # ---------- Snapshot ----------
    def _read_snapshot(self) -> Dict[str, Any]:
        if self.snapshot_path.exists():
            content = self.snapshot_path.read_text() or "{}"
            return json.loads(content)
        return {}

    def _write_snapshot(self, data: Dict[str, Any]) -> None:
        self.snapshot_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    # ---------- API ----------
    def apply_event(self, event: CoreEvent) -> None:
        start = time.time()
        try:
            if event.type == "CHAIN_HEAD":
                self._handle_chain_head(event)
                JOBS_PROCESSED.inc()
                return

            processed_key = f"processed:{event.id}"
            with FileLock(f"apply_event_{event.id}", ttl=10.0):
                if self.state.get(processed_key):
                    JOBS_PROCESSED.inc()
                    return

                if event.type == "AGENT_SIGNAL":
                    self._handle_agent_signal(event)
                elif event.type == "BRIDGE_MESSAGE":
                    self._handle_bridge_message(event)
                elif event.type == "TRANSFER":
                    self._handle_transfer(event)
                elif event.type == "ORACLE_UPDATE":
                    self._handle_oracle_update(event)
                else:
                    raise ValueError(f"Tipo de evento não suportado: {event.type}")

                self.state.set(processed_key, {"at": time.time(), "source": event.source.dict()})
                JOBS_PROCESSED.inc()
        except Exception:
            JOBS_FAILED.inc()
            raise
        finally:
            APPLY_LATENCY.observe(max(0.0, time.time() - start))

    # ---------- Handlers ----------
    def _handle_chain_head(self, event: CoreEvent) -> None:
        key = f"head:{event.source.chain}"
        head = self.state.get(key, {})
        if event.source.chain == "base-testnet":
            bn = event.payload.get("block_number")
            if bn is not None and (head.get("block_number") is None or bn > head.get("block_number", -1)):
                head["block_number"] = int(bn)
        elif event.source.chain == "solana-testnet":
            slot = event.payload.get("slot")
            if slot is not None and (head.get("slot") is None or slot > head.get("slot", -1)):
                head["slot"] = int(slot)
        head["updated_at"] = time.time()
        self.state.set(key, head)
        self._confirm_pending_messages()

    def _handle_agent_signal(self, event: CoreEvent) -> None:
        cfg_verify = bool(self.state.get("cfg:verify_agent_signatures", True))
        p = event.payload or {}
        if cfg_verify and all(k in p for k in ("pubkey", "sig", "message")):
            ok = verify_ed25519(p["pubkey"], p["message"], p["sig"])
            if not ok:
                raise ValueError("AGENT_SIGNAL: assinatura inválida")

        snap = self._read_snapshot()
        # suporta payloads decodificados via Borsh (em payload['decoded'])
        agent_id = p.get("agent_id") or (p.get("decoded", {}) or {}).get("agent_id") or "pfnet:unknown"
        signal = p.get("signal") or (p.get("decoded", {}) or {}).get("name") or "LOG"
        now = time.time()
        agent = snap.get(agent_id, {"status": {}, "meta": {}})
        agent["status"]["last_signal"] = signal
        agent["status"]["last_seen"] = now
        agent["status"]["chain"] = event.source.chain
        snap[agent_id] = agent
        self._write_snapshot(snap)

    def _handle_bridge_message(self, event: CoreEvent) -> None:
        snap = self._read_snapshot()
        msgs = snap.get("bridge:messages", [])
        if not any(m.get("id") == event.id for m in msgs):
            decoded = event.payload.get("args") or event.payload.get("decoded") or {}
            msgs.append({
                "id": event.id,
                "direction": event.payload.get("direction"),
                "asset": event.payload.get("asset") or decoded.get("asset"),
                "amount": event.payload.get("amount") or decoded.get("amount"),
                "src": event.source.dict(),
                "observed_at": event.observed_at,
                "confirmed": False,
                "pointer": {
                    "block_number": event.source.block_number,
                    "slot": event.source.slot,
                    "log_index": event.source.log_index,
                    "tx_hash": event.source.tx_hash,
                },
                "decoded": decoded,
            })
            snap["bridge:messages"] = msgs
            self._write_snapshot(snap)
        self._confirm_pending_messages()

    def _handle_transfer(self, event: CoreEvent) -> None:
        snap = self._read_snapshot()
        transfers = snap.get("transfers", [])
        decoded = event.payload.get("args") or {}
        transfers.append({
            "id": event.id,
            "asset": event.payload.get("asset") or decoded.get("token"),
            "amount": event.payload.get("amount") or decoded.get("value"),
            "to": event.payload.get("to") or decoded.get("to"),
            "from": event.payload.get("from") or decoded.get("from"),
            "src": event.source.dict(),
            "observed_at": event.observed_at,
        })
        snap["transfers"] = transfers
        self._write_snapshot(snap)

    def _handle_oracle_update(self, event: CoreEvent) -> None:
        snap = self._read_snapshot()
        oracle = snap.get("oracle", {})
        oracle.update(event.payload or {})
        snap["oracle"] = oracle
        self._write_snapshot(snap)

    # ---------- Confirmações ----------
    def _confirm_pending_messages(self) -> None:
        snap = self._read_snapshot()
        msgs = snap.get("bridge:messages", [])
        if not msgs:
            return

        base_req = int(self.state.get("confirmations:base-testnet", 2))
        sola_req = int(self.state.get("confirmations:solana-testnet", 1))

        head_base = self.state.get("head:base-testnet", {})
        head_sola = self.state.get("head:solana-testnet", {})

        changed = False
        now = time.time()
        for m in msgs:
            if m.get("confirmed"):
                continue
            src_chain = (m.get("src") or {}).get("chain")
            ptr = m.get("pointer") or {}
            if src_chain == "base-testnet":
                bn = ptr.get("block_number")
                head_bn = head_base.get("block_number")
                if bn is not None and head_bn is not None and head_bn >= int(bn) + base_req:
                    m["confirmed"] = True
                    m["confirmed_at"] = now
                    changed = True
            elif src_chain == "solana-testnet":
                slot = ptr.get("slot")
                head_slot = head_sola.get("slot")
                if slot is not None and head_slot is not None and head_slot >= int(slot) + sola_req:
                    m["confirmed"] = True
                    m["confirmed_at"] = now
                    changed = True

        if changed:
            snap["bridge:messages"] = msgs
            self._write_snapshot(snap)
