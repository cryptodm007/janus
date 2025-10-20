# rate/backpressure.py
from __future__ import annotations

class Backpressure:
    def __init__(self, high_watermark_inflight: int, resume_threshold: int):
        self.high = int(high_watermark_inflight)
        self.resume = int(resume_threshold)
        self.paused = False
        self.inflight = 0

    def on_dispatch(self) -> bool:
        """Retorna True se pode despachar; False se deve pausar."""
        if self.paused:
            return False
        if self.inflight >= self.high:
            self.paused = True
            return False
        self.inflight += 1
        return True

    def on_finish(self):
        self.inflight = max(0, self.inflight - 1)
        if self.paused and self.inflight <= self.resume:
            self.paused = False
