import time, os, random, contextvars
from typing import Optional, Dict

_current_span = contextvars.ContextVar("janus_current_span", default=None)

def _rand64():
    return "%016x" % random.getrandbits(64)

class Span:
    def __init__(self, name: str, trace_id: Optional[str]=None, parent_id: Optional[str]=None):
        self.name = name
        self.trace_id = trace_id or _rand64() + _rand64()
        self.span_id = _rand64()
        self.parent_id = parent_id
        self.start_ns = time.time_ns()
        self.end_ns = None
        self.tags: Dict[str, str] = {}
        self.error: Optional[str] = None
    def set_tag(self, k, v): self.tags[str(k)] = str(v)
    def finish(self): self.end_ns = time.time_ns()
    def duration_ms(self):
        end = self.end_ns or time.time_ns()
        return (end - self.start_ns)/1e6

class Tracer:
    def start_span(self, name: str) -> Span:
        parent = _current_span.get()
        span = Span(name, trace_id=(parent.trace_id if parent else None), parent_id=(parent.span_id if parent else None))
        _current_span.set(span)
        return span
    def end_span(self, span: Span):
        span.finish()
        _current_span.set(None)
        return span

tracer = Tracer()

# Context manager
class span:
    def __init__(self, name: str):
        self._span = tracer.start_span(name)
    def __enter__(self): return self._span
    def __exit__(self, exc_type, exc, tb):
        if exc:
            self._span.error = f"{exc_type.__name__}: {exc}"
        tracer.end_span(self._span)
        # não suprime exceção
        return False
