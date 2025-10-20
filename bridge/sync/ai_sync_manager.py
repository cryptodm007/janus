# janus/bridge/sync/ai_sync_manager.py
import asyncio
from typing import Dict, Any

from bridge.vendor.bridge_base_solana import BaseSolanaBridge
from bridge.sync.relay_proof import RelayProof
from bridge.validation.ai_validator import AIValidator
from bridge.validation.schemas import RelayEvent, Signature
from core.state_manager import StateManager
from core.policy_engine import PolicyEngine
from core.reputation import ReputationManager

class AISyncManager:
    """
    Orquestra o ciclo:
      1) colhe estados/eventos (Base/Solana)
      2) valida PoR (assinaturas/quorum)
      3) pontua IA (heurísticas/modelo)
      4) aplica política (PolicyEngine)
      5) atualiza estado + reputação
    """

    def __init__(self,
                 bridge: BaseSolanaBridge,
                 state_manager: StateManager,
                 relay_proof: RelayProof | None = None,
                 ai_validator: AIValidator | None = None,
                 policy: PolicyEngine | None = None,
                 reputation: ReputationManager | None = None):
        self.bridge = bridge
        self.state_manager = state_manager
        self.relay_proof = relay_proof or RelayProof()
        self.ai = ai_validator or AIValidator()
        self.policy = policy or PolicyEngine()
        self.reputation = reputation or ReputationManager()

    async def _fetch_event(self) -> Dict[str, Any]:
        """
        Obtém um 'evento' sintetizado a partir do estado das redes.
        Em produção, substitua por eventos reais do bridge vendor.
        """
        base_state = await self.bridge.get_base_state()
        sol_state = await self.bridge.get_solana_state()
        # Escolhe o mais recente como 'evento' base
        ev = base_state if base_state["timestamp"] >= sol_state["timestamp"] else sol_state
        # Assinaturas simuladas – troque por reais vindas do relay
        signatures = [ {"node_id": "nodeA", "valid": True, "meta": {}},
                       {"node_id": "nodeB", "valid": True, "meta": {}},
                       {"node_id": "nodeC", "valid": False, "meta": {}} ]
        ev["signatures"] = signatures
        return ev

    def _to_relay_event(self, ev: Dict[str, Any]) -> RelayEvent:
        sigs = [Signature(node_id=s["node_id"], valid=s["valid"], meta=s.get("meta", {}))
                for s in ev.get("signatures", [])]
        return RelayEvent(
            block_hash=ev.get("block_hash", ""),
            payload=ev.get("payload", {}),
            timestamp=int(ev["timestamp"]),
            signatures=sigs
        )

    async def loop(self, interval_sec: int = 10):
        while True:
            try:
                raw_ev = await self._fetch_event()
                relay_ev = self._to_relay_event(raw_ev)

                # 1) PoR (quorum por assinaturas válidas)
                total = len(relay_ev.signatures) or 1
                valid = sum(1 for s in relay_ev.signatures if s.valid)
                sig_fraction = valid / total

                # 2) IA (score heurístico/ML-ready)
                ai_metrics = self.ai.score(relay_ev)

                # 3) Reputação (média dos nós que assinaram)
                signer_ids = [s.node_id for s in relay_ev.signatures]
                rep_ok = self.reputation.majority_ok(signer_ids)

                # 4) Políticas
                decision = self.policy.decide({
                    "sig_fraction": sig_fraction,
                    "ai_score": ai_metrics["ai_score"],
                    "clock_skew_sec": ai_metrics["clock_skew_sec"],
                    "reputation_ok": rep_ok,
                })

                if decision["accepted"]:
                    # Atualiza estado global
                    self.state_manager.update_state({
                        "timestamp": relay_ev.timestamp,
                        "block_hash": relay_ev.block_hash,
                        "payload": relay_ev.payload,
                        "ai": ai_metrics,
                        "sig_fraction": sig_fraction,
                        "accepted": True
                    })
                    # Ajusta reputação (reforço positivo para quem assinou válido)
                    for s in relay_ev.signatures:
                        (self.reputation.boost if s.valid else self.reputation.penalize)(s.node_id)
                else:
                    # Penaliza todos que assinaram o evento rejeitado
                    for s in relay_ev.signatures:
                        self.reputation.penalize(s.node_id)

                await asyncio.sleep(interval_sec)

            except Exception as e:
                print(f"[AI_SYNC ERROR] {e}")
                await asyncio.sleep(5)
