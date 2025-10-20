# services/job_queue.py
from __future__ import annotations
import heapq
import time
from typing import List, Optional, Callable
from core.schemas import JobEnvelope, CoreEvent
from core.state_store import StateStore

class JobQueue:
    """
    Fila de jobs com prioridade por next_run_at, persistida em StateStore.
    Estratégia simples: min-heap em memória + espelho em disco.
    """
    KEY = "job_queue_heap"
    DLQ_KEY = "job_queue_dead"

    def __init__(self, state: Optional[StateStore] = None, handler: Optional[Callable[[CoreEvent], None]] = None):
        self.state = state or StateStore()
        self.handler = handler
        self.heap: List[tuple] = []
        self._load()

    def _load(self):
        data = self.state.get(self.KEY, [])
        self.heap = [(item["next_run_at"], item["job"]) for item in data]

        heapq.heapify(self.heap)

    def _persist(self):
        serialized = []
        for next_run_at, job in self.heap:
            serialized.append({"next_run_at": next_run_at, "job": job.dict()})
        self.state.set(self.KEY, serialized)

    def enqueue(self, event: CoreEvent, delay: float = 0.0):
        env = JobEnvelope(
            job_id=event.id,
            event=event,
            attempts=0,
            max_attempts=5,
            next_run_at=time.time() + delay,
            acked=False,
        )
        heapq.heappush(self.heap, (env.next_run_at, env))
        self._persist()

    def _backoff(self, attempts: int) -> float:
        return min(60.0, 2 ** attempts)  # até 60s

    def _mark_dead(self, env: JobEnvelope, reason: str):
        dead = self.state.get(self.DLQ_KEY, [])
        dead.append({"job": env.dict(), "dead_at": time.time(), "reason": reason})
        self.state.set(self.DLQ_KEY, dead)

    def tick(self):
        now = time.time()
        ran = 0
        changed = False
        while self.heap and self.heap[0][0] <= now:
            _, env = heapq.heappop(self.heap)
            changed = True
            try:
                if self.handler is None:
                    raise RuntimeError("Nenhum handler configurado para JobQueue")
                self.handler(env.event)
                env.acked = True
            except Exception as e:
                env.attempts += 1
                if env.attempts >= env.max_attempts:
                    self._mark_dead(env, str(e))
                else:
                    env.next_run_at = now + self._backoff(env.attempts)
                    heapq.heappush(self.heap, (env.next_run_at, env))
            ran += 1
        if changed:
            self._persist()
        return ran
