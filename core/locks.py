# core/locks.py
import time
import uuid
from pathlib import Path
from typing import Optional

class FileLock:
    """
    Lock por arquivo (coarse-grained). Em produção, prefira Redis ou Consul.
    """
    def __init__(self, name: str, dir_path: str = ".runtime/locks", ttl: float = 30.0):
        self.name = name
        self.ttl = ttl
        self.lock_id = str(uuid.uuid4())
        self.path = Path(dir_path) / f"{name}.lock"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def acquire(self, wait: float = 0.1, timeout: float = 5.0) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            if not self.path.exists():
                self.path.write_text(f"{self.lock_id}|{time.time()+self.ttl}")
                return True
            try:
                content = self.path.read_text()
                _, expires_at = content.split("|")
                if time.time() > float(expires_at):
                    self.path.write_text(f"{self.lock_id}|{time.time()+self.ttl}")
                    return True
            except Exception:
                pass
            time.sleep(wait)
        return False

    def release(self) -> None:
        try:
            if self.path.exists():
                content = self.path.read_text()
                if content.startswith(self.lock_id):
                    self.path.unlink(missing_ok=True)
        except Exception:
            pass

    def __enter__(self):
        if not self.acquire():
            raise TimeoutError(f"Não foi possível adquirir lock: {self.name}")
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
