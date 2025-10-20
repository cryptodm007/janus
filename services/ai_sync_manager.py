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
    Aplica eventos ao estado dos agentes (PFNET), confirma cross-chain e mantém snapshots idempotentes.
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
        """
        processed_key = f"processed:{event.id}"
        with FileLock(f"apply_event_{event.id}", ttl=10.0):
            if self.state.get(processed_key):
                # Já processado — idempotência
                return
            # Roteia por tipo
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
    def _handle_agent_signal(self, event: CoreEvent) -> None:
        snap = self._read_snapshot()
        agent_id = event.payload.get("agent_id")
        signal = event.payload.get("signal")
        if not agent_id:
            raise ValueError("AGENT_SIGNAL sem agent_id")

        agent = snap.get(agent_id, {"status": {}, "meta": {}})
        now = time.time()

        # Aplicação simples de heartbeat/sinais
        agent["status"]["last_signal"] = signal
        agent["status"]["last_seen"] = now
        agent["status"]["chain"] = event.source.chain

        snap[agent_id] = agent
        self._write_snapshot(snap)

    def _handle_bridge_message(self, event: CoreEvent) -> None:
        snap = self._read_snapshot()
        bridge_key = "bridge:messages"
        msgs = snap.get(bridge_key, [])
        # Adiciona mensagem normalizada
        msgs.append({
            "id": event.id,
            "direction": event.payload.get("direction"),
            "asset": event.payload.get("asset"),
            "amount": event.payload.get("amount"),
            "src": event.source.dict(),
            "observed_at": event.observed_at,
            "confirmed": False,
        })
        snap[bridge_key] = msgs
        self._write_snapshot(snap)

        # Confirmação simplificada por chain
        self._confirm_cross_chain(event)

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
        # Mescla payload do oráculo
        oracle.update(event.payload or {})
        snap["oracle"] = oracle
        self._write_snapshot(snap)

    # ---------- Confirmações ----------
    def _confirm_cross_chain(self, event: CoreEvent) -> None:
        """
        Placeholder de confirmação (mock).
        Em produção: consultar finality/confirmations por chain antes de marcar confirmada.
        """
        snap = self._read_snapshot()
        msgs = snap.get("bridge:messages", [])
        for m in msgs:
            if m["id"] == event.id and not m.get("confirmed"):
                # Regras simples: base-testnet requer 2 confirmações; solana-testnet 1.
                if event.source.chain == "base-testnet":
                    m["confirmed"] = True  # mock — substituir por leitura real na Fase 19
                    m["confirmed_at"] = time.time()
                elif event.source.chain == "solana-testnet":
                    m["confirmed"] = True
                    m["confirmed_at"] = time.time()
        snap["bridge:messages"] = msgs
        self._write_snapshot(snap)
