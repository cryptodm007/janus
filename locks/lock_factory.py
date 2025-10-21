# locks/lock_factory.py
from __future__ import annotations
import os
from typing import Protocol
from redis import Redis
from locks.redis_fencing_lock import RedisFencingLock
from core.locks import FileLock

class ILock(Protocol):
    def acquire(self, timeout: float = 5.0) -> bool: ...
    def release(self) -> None: ...
    def __enter__(self): ...
    def __exit__(self, exc_type, exc, tb): ...

def make_lock(name: str, cfg: dict) -> ILock:
    backend = (cfg.get("locks", {}) or {}).get("backend", "file")
    ttl = float((cfg.get("locks", {}) or {}).get("ttl_seconds", 15))
    if backend == "redis":
        url_env = ((cfg.get("locks", {}) or {}).get("redis", {}) or {}).get("url_env", "REDIS_URL")
        ns = ((cfg.get("locks", {}) or {}).get("redis", {}) or {}).get("namespace", "janus")
        url = os.getenv(url_env, "")
        r = Redis.from_url(url, decode_responses=True)
        return RedisFencingLock(r, name=name, ttl=ttl, namespace=ns)
    return FileLock(name=name, ttl=ttl)
