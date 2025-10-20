# storage/redis_queue.py
from __future__ import annotations
import time, json, os
from typing import List
from redis import Redis
from core.interfaces import JobQueueBackend
from core.schemas import JobEnvelope

# Estrutura:
#  - ZSET janus:due -> score=next_run_at, member=job_id
#  - HASH janus:job:<job_id> -> payload JSON
#  - LIST janus:dlq -> append de itens mortos (JSON)

class RedisQueueBackend(JobQueueBackend):
    def __init__(self, url: str, backoff_cap: float = 60.0):
        self.r = Redis.from_url(url, decode_responses=True)
        self.backoff_cap = backoff_cap
        self.key_due = "janus:due"
        self.key_dlq = "janus:dlq"

    def enqueue(self, env: JobEnvelope) -> None:
        key = f"janus:job:{env.job_id}"
        self.r.hsetnx(key, "payload", env.model_dump_json())
        self.r.zadd(self.key_due, {env.job_id: env.next_run_at})

    def pop_due(self, now: float, limit: int) -> List[JobEnvelope]:
        # obtém e retorna sem remover (remoção na ack/requeue)
        ids = self.r.zrangebyscore(self.key_due, "-inf", now, 0, limit)
        out: List[JobEnvelope] = []
        for jid in ids:
            pl = self.r.hget(f"janus:job:{jid}", "payload")
            if pl:
                out.append(JobEnvelope.model_validate_json(pl))
        return out

    def requeue(self, env: JobEnvelope) -> None:
        key = f"janus:job:{env.job_id}"
        self.r.hset(key, "payload", env.model_dump_json())
        self.r.zadd(self.key_due, {env.job_id: env.next_run_at})

    def ack(self, env: JobEnvelope) -> None:
        key = f"janus:job:{env.job_id}"
        pipe = self.r.pipeline()
        pipe.delete(key)
        pipe.zrem(self.key_due, env.job_id)
        pipe.execute()

    def dead_letter(self, env: JobEnvelope, reason: str) -> None:
        self.r.rpush(self.key_dlq, json.dumps({
            "job": json.loads(env.model_dump_json()),
            "reason": reason,
            "dead_at": time.time()
        }))
        self.r.zrem(self.key_due, env.job_id)
        self.r.delete(f"janus:job:{env.job_id}")
