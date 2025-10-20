# services/ai_sync_manager.py
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Dict, Any

from core.schemas import CoreEvent
from core.state_store import StateStore
from core.locks import FileLock

class AISyncManager:
    """
    Aplica eventos ao estado dos agentes (PFNET), confirma cross-chain
    com base no 'head' observado (via eventos CHAIN_HEAD) e mantém snapshots.
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
        """
        Entrada principal chamada pela job_queue.
        Garante idempotência via marcação de 'processed:<event_id>'.
        Eventos CHAIN_HEAD atualizam ponteiros de finality por chain.
        """
        if event.type == "CHAIN_HEAD":
            self._handle_chain_head(event)
            return

        processed_key = f"processed:{event.id}"
        with FileLock(f"apply_event_{event.id}", ttl=10.0):
            if self.state.get(processed_key):
                # Já processado — idempotência
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

            # Marcação de processado
            self.state.set(processed_key, {"at": time.time(), "source": event.source.dict()})

    # ---------- Handlers ----------
    def _handle_chain_head(self, event: CoreEvent) -> None:
        """
        Atualiza o head observado por chain, usado para confirmação assíncrona.
        payload: {"block_number": int} (EVM) ou {"slot": int} (Solana)
        """
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

        # Tenta confirmar pendências da ponte ao avançar head
        self._confirm_pending_messages()

    def _handle_agent_signal(self, event: CoreEvent) -> None:
        snap = self._read_snapshot()
        agent_id = event.payload.get("agent_id", "pfnet:unknown")
        # Heurística: se veio de Solana logs sem parsing, ainda guardamos heartbeat bruto
        signal = event.payload.get("signal") or "LOG"
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
        # Evita duplicação por ID
        if not any(m.get("id") == event.id for m in msgs):
            msgs.append({
                "id": event.id,
                "direction": event.payload.get("direction"),
                "asset": event.payload.get("asset"),
                "amount": event.payload.get("amount"),
                "src": event.source.dict(),
                "observed_at": event.observed_at,
                "confirmed": False,
                "pointer": {
                    "block_number": event.source.block_number,
                    "slot": event.source.slot,
                    "log_index": event.source.log_index,
                    "tx_hash": event.source.tx_hash,
                }
            })
            snap["bridge:messages"] = msgs
            self._write_snapshot(snap)

        # Tenta confirmar imediatamente (caso head já satisfaça)
        self._confirm_pending_messages()

    def _handle_transfer(self, event: CoreEvent) -> None:
        snap = self._read_snapshot()
        transfers = snap.get("transfers", [])
        transfers.append({
            "id": event.id,
            "asset": event.payload.get("asset"),
            "amount": event.payload.get("amount"),
            "to": event.payload.get("to"),
            "from": event.payload.get("from"),
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
        """
        Confirma mensagens pendentes de acordo com o head atual por chain.
        - base-testnet: confirmed quando head_block >= msg.block_number + confirmations_required
        - solana-testnet: confirmed quando head_slot >= msg.slot + confirmations_required (slot-heurística)
        """
        snap = self._read_snapshot()
        msgs = snap.get("bridge:messages", [])
        if not msgs:
            return

        # Lê heads e confirmações requeridas (gravadas no StateStore pelo bootstrap/config)
        # Guardamos confirmações requeridas em chaves:
        #   confirmations:base-testnet  e  confirmations:solana-testnet
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
