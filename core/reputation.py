# janus/core/reputation.py
from typing import Dict

class ReputationManager:
    """
    Mantém reputação dos nós validadores/relays (0..1).
    Aumenta em eventos válidos, reduz em invalidados/inconsistentes.
    """
    def __init__(self):
        self._rep: Dict[str, float] = {}

    def get(self, node_id: str) -> float:
        return self._rep.get(node_id, 0.5)  # default neutro

    def boost(self, node_id: str, delta: float = 0.02):
        self._rep[node_id] = max(0.0, min(1.0, self.get(node_id) + delta))

    def penalize(self, node_id: str, delta: float = 0.05):
        self._rep[node_id] = max(0.0, min(1.0, self.get(node_id) - delta))

    def majority_ok(self, node_ids) -> bool:
        if not node_ids:
            return False
        avg = sum(self.get(n) for n in node_ids) / len(node_ids)
        return avg >= 0.5
