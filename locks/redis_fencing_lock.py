# locks/redis_fencing_lock.py
from __future__ import annotations
import time
from typing import Optional
from redis import Redis

class RedisFencingLock:
    """
    Lock distribuído com FENCING TOKEN.
    - Gera token monotônico via INCR (namespace:ctr:<name>)
    - Escreve chave de posse (namespace:lock:<name>) com TTL
    - Retorna (locked=True, token=int). Quem tem o MAIOR token é o vencedor em caso de disputa.
    - O cliente chamador deve propagar e validar o token onde escreve (ou comparar com 'last_token' persistido).
    """
    def __init__(self, r: Redis, name: str, ttl: int = 15, namespace: str = "janus"):
        self.r = r
        self.name = name
        self.ttl = int(ttl)
        self.ns = namespace
        self.key_ctr = f"{self.ns}:ctr:{self.name}"
        self.key_lock = f"{self.ns}:lock:{self.name}"
        self.token: Optional[int] = None

    def acquire(self, timeout: float = 5.0) -> tuple[bool, Optional[int]]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            token = int(self.r.incr(self.key_ctr))
            # Tenta setar posse com TTL somente se inexistente
            if self.r.set(self.key_lock, token, nx=True, ex=self.ttl):
                self.token = token
                return True, token
            # Caso alguém esteja segurando, aguarda e tenta novamente
            time.sleep(0.05)
        return False, None

    def renew(self) -> bool:
        if self.token is None:
            return False
        # renova somente se ainda somos o dono (valor igual ao nosso token)
        pipe = self.r.pipeline()
        pipe.watch(self.key_lock)
        cur = pipe.get(self.key_lock)
        if cur is None or int(cur) != self.token:
            pipe.reset()
            return False
        pipe.multi()
        pipe.set(self.key_lock, self.token, ex=self.ttl)
        pipe.execute()
        return True

    def release(self) -> None:
        if self.token is None:
            return
        lua = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
          return redis.call('del', KEYS[1])
        else
          return 0
        end
        """
        try:
            self.r.eval(lua, 1, self.key_lock, str(self.token))
        finally:
            self.token = None

    def __enter__(self):
        ok, _ = self.acquire()
        if not ok:
            raise TimeoutError(f"Não foi possível adquirir fencing lock: {self.name}")
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
