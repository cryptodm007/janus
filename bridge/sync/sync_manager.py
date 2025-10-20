# janus/bridge/sync/ai_sync_manager.py

import asyncio
from typing import Dict, Any, List, Optional

# ✅ Importa o vendor corretamente (conforme submódulo existente em vendor/)
from vendor.bridge_base_solana import BaseSolanaBridge

from bridge.sync.relay_proof import RelayProof
from bridge.validation.ai_validator import AIValidator
from bridge.validation.schemas import RelayEvent, Signature

from core.state_manager import StateManager
from core.policy_engine import PolicyEngine
from core.reputation import ReputationManager

# Fase 11 - Observability & Telemetry
from core.observability import logger
from core.observability.metrics import metrics, REQS_TOTAL, STATE_TS
from core.observability.middleware import ainstrumented
from core.observability.tracing import span


class AISyncManager:
    """
    Orquestra o ciclo de sincronização/validação:
      1) coleta estados/eventos a partir das redes (Base/Solana) via bridge vendor
      2) valida PoR (quorum de assinaturas)
      3) pontua IA (heurística/ML-ready)
      4) aplica políticas de decisão (PolicyEngine)
      5) atualiza estado global + reputação dos signatários
    """

    def __init__(
        self,
        bridge: BaseSolanaBridge,
        state_manager: StateManager,
        relay_proof: Optional[RelayProof] = None,
        ai_validator: Optional[AIValidator] = None,
        policy: Optional[PolicyEngine] = None,
        reputation: Optional[ReputationManager] = None,
    ):
        self.bridge = bridge
        self.state_manager = state_manager
        self.relay_proof = relay_proof or RelayProof()
        self.ai = ai_validator or AIValidator()
        self.policy = policy or PolicyEngine()
        self.reputation = reputation or ReputationManager()

    async def _fetch_event(self) -> Dict[str, Any]:
        """
        Obtém um 'evento' sintetizado a partir do estado das redes.
        Em produção, substitua por eventos reais provenientes do relay (vendor).
        """
        with span("fetch_event"):
            base_state = await self.bridge.get_base_state()
            sol_state = await self.bridge.get_solana_state()

        # Escolhe o mais recente como base do evento (pode ser substituído por lógica de reconciliação)
        ev = base_state if base_state.get("timestamp", 0) >= sol_state.get("timestamp", 0) else sol_state

        # Assinaturas simuladas — em produção, receba do relay e verifique via RelayProof
        signatures = [
            {"node_id": "nodeA", "valid": True, "meta": {}},
            {"node_id": "nodeB", "valid": True, "meta": {}},
            {"node_id": "nodeC", "valid": False, "meta": {}},
        ]
        ev["signatures"] = signatures

        # Garanta campos essenciais
        ev.setdefault("block_hash", ev.get("block_hash", ""))  # vendor deve prover um hash real
        ev.setdefault("payload", ev.get("payload", {}))
        ev["timestamp"] = int(ev.get("timestamp", 0))

        logger.debug("event_fetched", ctx={"trace": "ai_sync"}, chosen="base" if ev is base_state else "solana",
                     ts=ev["timestamp"], block_hash=ev.get("block_hash", ""))
        return ev

    def _to_relay_event(self, ev: Dict[str, Any]) -> RelayEvent:
        sigs: List[Signature] = [
            Signature(node_id=s["node_id"], valid=bool(s["valid"]), meta=s.get("meta", {}))
            for s in ev.get("signatures", [])
        ]
        return RelayEvent(
            block_hash=str(ev.get("block_hash", "")),
            payload=dict(ev.get("payload", {})),
            timestamp=int(ev.get("timestamp", 0)),
            signatures=sigs,
        )

    @ainstrumented("ai_sync.loop")
    async def loop(self, interval_sec: int = 10):
        """
        Loop principal de sincronização/validação.
        """
        while True:
            try:
                REQS_TOTAL.inc(1)

                raw_ev = await self._fetch_event()
                relay_ev = self._to_relay_event(raw_ev)

                # 1) PoR - quorum de assinaturas válidas (usando fração válida como proxy)
                total = len(relay_ev.signatures) or 1
                valid = sum(1 for s in relay_ev.signatures if s.valid)
                sig_fraction = valid / total

                # 2) IA - score heurístico
                ai_metrics = self.ai.score(relay_ev)  # dict: ai_score, sig_fraction (do AI), clock_skew_sec, entropy_proxy

                # 3) Reputação - média dos signatários
                signer_ids = [s.node_id for s in relay_ev.signatures]
                rep_ok = self.reputation.majority_ok(signer_ids)

                # 4) Políticas - decisão final
                decision = self.policy.decide({
                    "sig_fraction": sig_fraction,
                    "ai_score": ai_metrics["ai_score"],
                    "clock_skew_sec": ai_metrics["clock_skew_sec"],
                    "reputation_ok": rep_ok,
                })

                if decision["accepted"]:
                    # Atualiza estado global aceito
                    new_state = {
                        "timestamp": relay_ev.timestamp,
                        "block_hash": relay_ev.block_hash,
                        "payload": relay_ev.payload,
                        "ai": ai_metrics,
                        "sig_fraction": sig_fraction,
                        "accepted": True,
                    }
                    self.state_manager.update_state(new_state)
                    STATE_TS.set(relay_ev.timestamp)

                    # Reforço positivo/penalidade por assinatura válida/inválida
                    for s in relay_ev.signatures:
                        (self.reputation.boost if s.valid else self.reputation.penalize)(s.node_id)

                    logger.info(
                        "state_accepted",
                        ctx={"trace": "ai_sync"},
                        block_hash=relay_ev.block_hash,
                        ai_score=ai_metrics["ai_score"],
                        sig_fraction=sig_fraction,
                        reputation_ok=rep_ok,
                    )
                else:
                    # Penaliza todos os signatários em evento rejeitado
                    for s in relay_ev.signatures:
                        self.reputation.penalize(s.node_id)

                    logger.warn(
                        "state_rejected",
                        ctx={"trace": "ai_sync"},
                        reasons=decision["reasons"],
                        ai_score=ai_metrics["ai_score"],
                        sig_fraction=sig_fraction,
                        reputation_ok=rep_ok,
                    )

                await asyncio.sleep(interval_sec)

            except Exception as e:
                logger.error("ai_sync_error", ctx={"trace": "ai_sync"}, exc=e)
                await asyncio.sleep(5)
