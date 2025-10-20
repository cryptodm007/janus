# services/job_queue.py
from __future__ import annotations
import time
from typing import Optional, Callable, List
from core.schemas import JobEnvelope, CoreEvent
from core.state_store import StateStore
from core.events import deterministic_event_id
from core.interfaces import JobQueueBackend
from storage.sqlite_queue import SQLiteQueueBackend
try:
    from storage.redis_queue import RedisQueueBackend  # opcional
except Exception:
    RedisQueueBackend = None  # type: ignore

from rate.rate_limiter import RateLimiter
from rate.backpressure import Backpressure
from telemetry.metrics import JOBS_PROCESSED, JOBS_FAILED

class JobQueue:
    """
    Orquestrador de fila com backend plugável (SQLite/Redis), rate-limit e backpressure.
    """
    def __init__(
        self,
        handler: Callable[[CoreEvent], None],
        state: Optional[StateStore] = None,
        config: Optional[dict] = None
    ):
        self.state = state or StateStore()
        self.handler = handler
        cfg = config or {}
        qcfg = (cfg.get("queue") or {})
        backend = (qcfg.get("backend") or "sqlite").lower()
        backoff_cap = float(qcfg.get("backoff_seconds_cap", 60))
        self.max_attempts = int(qcfg.get("max_attempts", 5))
        self.batch = int(qcfg.get("tick_batch", 50))

        if backend == "redis" and RedisQueueBackend:
            import os
            url = os.getenv((qcfg.get("redis") or {}).get("url_env", "REDIS_URL"), "")
            self.backend: JobQueueBackend = RedisQueueBackend(url=url, backoff_cap=backoff_cap)  # type: ignore
        else:
            path = (qcfg.get("sqlite") or {}).get("path", ".runtime/janus_queue.db")
            self.backend = SQLiteQueueBackend(path=path, backoff_cap=backoff_cap)

        # Rate limiters
        self.limiter = RateLimiter(cfg.get("rate_limits") or {})

        # Backpressure
        bpcfg = cfg.get("backpressure") or {}
        self.bp = Backpressure(
            high_watermark_inflight=int(bpcfg.get("high_watermark_inflight", 200)),
            resume_threshold=int(bpcfg.get("resume_threshold", 120))
        )

    # ----------------- API -----------------
    def enqueue(self, event: CoreEvent, delay: float = 0.0):
        env = JobEnvelope(
            job_id=event.id,
            event=event,
            attempts=0,
            max_attempts=self.max_attempts,
            next_run_at=time.time() + delay,
            acked=False,
        )
        self.backend.enqueue(env)

    def _backoff(self, attempts: int) -> float:
        return min(60.0, 2 ** attempts)

    def tick(self) -> int:
        """
        Processa até 'batch' jobs vencidos respeitando backpressure e rate limits.
        """
        now = time.time()
        due: List[JobEnvelope] = self.backend.pop_due(now, self.batch)
        processed = 0
        for env in due:
            if not self.bp.on_dispatch():
                # sem capacidade – pare este tick
                break

            # Chave de rate-limit: por chain + type
            k = f"{env.event.source.chain}:{env.event.type}"
            if not self.limiter.allow(k):
                # reprograma levemente (throttle suave)
                env.next_run_at = now + 0.25
                self.backend.requeue(env)
                self.bp.on_finish()
                continue

            try:
                self.handler(env.event)
                env.acked = True
                self.backend.ack(env)
                JOBS_PROCESSED.inc()
            except Exception as e:
                env.attempts += 1
                if env.attempts >= env.max_attempts:
                    self.backend.dead_letter(env, str(e))
                    JOBS_FAILED.inc()
                else:
                    env.error = str(e)
                    env.next_run_at = now + self._backoff(env.attempts)
                    self.backend.requeue(env)
                    JOBS_FAILED.inc()
            finally:
                processed += 1
                self.bp.on_finish()

        return processed
