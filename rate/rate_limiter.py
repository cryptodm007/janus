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
    def __init__(self, config: Dict[str, Dict[str, float]]):
        self.buckets: Dict[str, TokenBucket] = {}
        for key, spec in (config or {}).items():
            self.buckets[key] = TokenBucket(spec.get("rps", 10), spec.get("burst", 20))

    def allow(self, key: str) -> bool:
        b = self.buckets.get(key)
        if not b:
            return True
        return b.allow()
