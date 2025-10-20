# janus/bridge/validation/ai_validator.py
import math
import time
from typing import Dict, Any, List
from .schemas import RelayEvent, Signature

class AIValidator:
    """
    Camada IA/heurística (ML-ready) para pontuar eventos do relay.
    Implementa um score [0..1] com base em heurísticas simples,
    mas projetado para ser substituído por um modelo no futuro.
    """

    def __init__(self, now_provider=lambda: int(time.time())):
        self._now = now_provider

    def _sig_fraction(self, signatures: List[Signature]) -> float:
        if not signatures:
            return 0.0
        valid = sum(1 for s in signatures if s.valid)
        return valid / len(signatures)

    def _clock_skew(self, event_ts: int) -> int:
        return abs(self._now() - int(event_ts))

    def _hash_entropy_proxy(self, block_hash: str) -> float:
        """
        Proxy extremamente simples: diversidade de caracteres/len.
        (Apenas placeholder — troque por um verificador criptográfico real.)
        """
        if not block_hash:
            return 0.0
        unique = len(set(block_hash))
        return min(1.0, unique / max(16, len(block_hash)))

    def score(self, event: RelayEvent) -> Dict[str, Any]:
        sig_frac = self._sig_fraction(event.signatures)          # 0..1
        skew = self._clock_skew(event.timestamp)                 # segundos
        entropy = self._hash_entropy_proxy(event.block_hash)     # 0..1

        # Heurística: peso maior para assinaturas, depois entropia, penalidade por skew
        raw = 0.6 * sig_frac + 0.3 * entropy - 0.1 * (min(skew, 120) / 120.0)
        score = max(0.0, min(1.0, raw))
        return {
            "ai_score": score,
            "sig_fraction": sig_frac,
            "clock_skew_sec": skew,
            "entropy_proxy": entropy,
        }
