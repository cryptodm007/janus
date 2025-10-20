import time
from functools import wraps
from .metrics import LOOP_SEC, ERR_TOTAL
from .tracing import span

def instrumented(name: str):
    """
    Decorator para funções síncronas: mede duração, conta erros, cria span.
    """
    def _wrap(fn):
        @wraps(fn)
        def _inner(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                with span(name) as sp:
                    res = fn(*args, **kwargs)
                return res
            except Exception:
                ERR_TOTAL.inc(1)
                raise
            finally:
                dt = time.perf_counter() - t0
                LOOP_SEC.observe(dt)
        return _inner
    return _wrap

def ainstrumented(name: str):
    """
    Decorator para corrotinas: idem acima, para async def.
    """
    def _wrap(fn):
        @wraps(fn)
        async def _inner(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                with span(name) as sp:
                    res = await fn(*args, **kwargs)
                return res
            except Exception:
                ERR_TOTAL.inc(1)
                raise
            finally:
                dt = time.perf_counter() - t0
                LOOP_SEC.observe(dt)
        return _inner
    return _wrap
