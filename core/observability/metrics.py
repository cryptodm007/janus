import time
from typing import Dict, Callable, Optional, List
from collections import defaultdict

class Counter:
    def __init__(self, name: str, description: str=""):
        self.name, self.description = name, description
        self._value = 0
    def inc(self, amount: int=1):
        self._value += amount
    def value(self): return self._value

class Gauge:
    def __init__(self, name: str, description: str=""):
        self.name, self.description = name, description
        self._value = 0.0
    def set(self, value: float): self._value = float(value)
    def value(self): return self._value

class Histogram:
    def __init__(self, name: str, buckets: Optional[List[float]]=None, description: str=""):
        self.name, self.description = name, description
        self.buckets = sorted(buckets or [0.01,0.05,0.1,0.25,0.5,1,2,5,10])
        self.counts = defaultdict(int)
        self.sum = 0.0
        self.n = 0
    def observe(self, value: float):
        self.sum += value
        self.n += 1
        for b in self.buckets:
            if value <= b:
                self.counts[b] += 1
                break
        else:
            self.counts[float("inf")] += 1

class Registry:
    def __init__(self):
        self.counters: Dict[str, Counter] = {}
        self.gauges: Dict[str, Gauge] = {}
        self.histograms: Dict[str, Histogram] = {}
    def counter(self, name, desc=""):
        return self.counters.setdefault(name, Counter(name, desc))
    def gauge(self, name, desc=""):
        return self.gauges.setdefault(name, Gauge(name, desc))
    def histogram(self, name, desc="", buckets=None):
        return self.histograms.setdefault(name, Histogram(name, buckets, desc))
    def export_text(self) -> str:
        lines = []
        for c in self.counters.values():
            lines.append(f"# HELP {c.name} {c.description}")
            lines.append(f"# TYPE {c.name} counter")
            lines.append(f"{c.name} {c.value()}")
        for g in self.gauges.values():
            lines.append(f"# HELP {g.name} {g.description}")
            lines.append(f"# TYPE {g.name} gauge")
            lines.append(f"{g.name} {g.value()}")
        for h in self.histograms.values():
            lines.append(f"# HELP {h.name} {h.description}")
            lines.append(f"# TYPE {h.name} histogram")
            cum = 0
            for b in h.buckets + [float("inf")]:
                cum += h.counts.get(b, 0)
                b_label = "+Inf" if b == float("inf") else str(b)
                lines.append(f'{h.name}_bucket{{le="{b_label}"}} {cum}')
            lines.append(f"{h.name}_sum {h.sum}")
            lines.append(f"{h.name}_count {h.n}")
        return "\n".join(lines)

# Registry global simples
metrics = Registry()

# Helpers comuns
REQS_TOTAL = metrics.counter("janus_requests_total", "Total de ciclos/processamentos")
ERR_TOTAL  = metrics.counter("janus_errors_total", "Total de erros")
LOOP_SEC   = metrics.histogram("janus_loop_seconds", "Tempo do loop AISync/Sync")
STATE_TS   = metrics.gauge("janus_state_last_timestamp", "Último timestamp de estado aceito")
