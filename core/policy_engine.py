# janus/core/policy_engine.py
from typing import Dict, Any

class PolicyEngine:
    """
    Define políticas de decisão para aceitar/rejeitar eventos de bridge.
    Ajuste os thresholds conforme o ambiente (testnet/mainnet).
    """
    def __init__(self,
                 min_sig_quorum: float = 0.67,   # 2/3 dos validadores
                 min_ai_score: float = 0.65,     # score [0..1]
                 max_clock_skew_sec: int = 45):  # desvio de relógio tolerado
        self.min_sig_quorum = min_sig_quorum
        self.min_ai_score = min_ai_score
        self.max_clock_skew_sec = max_clock_skew_sec

    def decide(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        context esperado:
          - sig_fraction: float  (0..1)
          - ai_score: float      (0..1)
          - clock_skew_sec: int
          - reputation_ok: bool
        """
        reasons = []

        if context.get("sig_fraction", 0) < self.min_sig_quorum:
            reasons.append("assinaturas_insuficientes")
        if context.get("ai_score", 0) < self.min_ai_score:
            reasons.append("ai_score_baixo")
        if context.get("clock_skew_sec", 0) > self.max_clock_skew_sec:
            reasons.append("clock_skew_alto")
        if not context.get("reputation_ok", False):
            reasons.append("reputacao_baixa")

        accepted = len(reasons) == 0
        return {"accepted": accepted, "reasons": reasons}
