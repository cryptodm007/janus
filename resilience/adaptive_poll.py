# resilience/adaptive_poll.py
from __future__ import annotations

class AdaptivePoll:
    def __init__(self, base: float, min_interval: float, max_interval: float):
        self.base = float(base)
        self.min = float(min_interval)
        self.max = float(max_interval)
        self.cur = self.base

    def faster(self):
        self.cur = max(self.min, self.cur / 2.0)

    def slower(self):
        self.cur = min(self.max, self.cur * 1.5)

    def reset(self):
        self.cur = self.base

    def interval(self) -> float:
        return self.cur
