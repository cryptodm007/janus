# resilience/circuit_breaker.py
from __future__ import annotations
import time
from dataclasses import dataclass

@dataclass
class CBState:
    errors: int = 0
    opened_at: float = 0.0
    state: str = "closed"  # closed | open | half_open

class CircuitBreaker:
    def __init__(self, window_errors: int = 5, reset_after_sec: float = 20.0):
        self.cfg_errors = int(window_errors)
        self.reset_after = float(reset_after_sec)
        self.s = CBState()

    def on_success(self):
        if self.s.state in ("half_open", "open"):
            # fecha após um sucesso em half-open
            self.s = CBState(state="closed")
        else:
            self.s.errors = 0

    def on_error(self):
        if self.s.state == "open":
            return
        self.s.errors += 1
        if self.s.errors >= self.cfg_errors:
            self.s.state = "open"
            self.s.opened_at = time.time()

    def allow(self) -> bool:
        if self.s.state == "closed":
            return True
        if self.s.state == "open":
            if (time.time() - self.s.opened_at) >= self.reset_after:
                self.s.state = "half_open"
                return True
            return False
        # half_open → permite UMA tentativa
        self.s.state = "open"  # em caso de falha, chamador deve on_error(); em sucesso, on_success() fecha
        return True
