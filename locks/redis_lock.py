# locks/redis_lock.py
from __future__ import annotations
import time, uuid
from typing import Optional
from redis import Redis
from core.interfaces import DistributedLock

class RedisLock(DistributedLock):
    def __init__(self, r: Redis, name: str, ttl: float = 15.0):
        self.r = r
        self.name = f"janus:lock:{name}"
        self.ttl = int(ttl)
        self.token = str(uuid.uuid4())

    def acquire(self, timeout: float = 5.0) -> bool:
        end = time.time() + timeout
        while time.time() < end:
            if self.r.set(self.name, self.token, nx=True, ex=self.ttl):
                return True
            time.sleep(0.05)
        return False

    def release(self) -> None:
        lua = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
          return redis.call('del', KEYS[1])
        else
          return 0
        end
        """
        self.r.eval(lua, 1, self.name, self.token)

    def __enter__(self):
        if not self.acquire():
            raise TimeoutError(f"Não foi possível adquirir lock: {self.name}")
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
