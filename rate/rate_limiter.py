# rate/rate_limiter.py
from __future__ import annotations
import time
from typing import Dict

class TokenBucket:
    def __init__(self, rps: float, burst: int):
        self.capacity = float(burst)
        self.tokens = float(burst)
        self.refill = float(rps)
        self.last = time.time()

    def allow(self) -> bool:
        now = time.time()
        dt = now - self.last
        self.tokens = min(self.capacity, self.tokens + dt * self.refill)
        self.last = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False

class RateLimiter:
    """
    RateLimiter controla a taxa de eventos permitidos por chave.
    Configurada por `rate_limits` no `sync.yaml`, usando key = "{chain}:{type}".
    """
    def __init__(self, config: Dict[str, Dict[str, float]]):
        self.buckets: Dict[str, TokenBucket] = {}
        for key, spec in (config or {}).items():
            rps   = float(spec.get("rps", 0.0))
            burst = int(spec.get("burst", 0))
            self.buckets[key] = TokenBucket(rps, burst)

    def allow(self, key: str) -> bool:
        bucket = self.buckets.get(key)
        if not bucket:
            # Se não há configuração de limite para a key, permitir livremente
            return True
        return bucket.allow()
