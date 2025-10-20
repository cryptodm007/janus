# janus/core/persistence/store.py
import os, json, gzip, time, hashlib, shutil
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List

DEFAULT_DIR = os.getenv("JANUS_SNAPSHOT_DIR", "snapshots")
COMPRESS = os.getenv("JANUS_SNAPSHOT_COMPRESS", "1") in ("1","true","TRUE","yes","on")
VERSION = "1"

def sha256_hex(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

@dataclass
class SnapshotMeta:
    file: str
    created_at: int
    size_bytes: int
    checksum: str
    version: str = VERSION
    compressed: bool = COMPRESS

class SnapshotStore:
    """
    Armazenamento simples de snapshots:
      - Formato: JSON {"version","created_at","state"} (opcionalmente GZIP)
      - Arquivo: snapshot-<epoch>.json[.gz]
      - Checksum: SHA-256 do payload bruto (pré-gzip se compress=False; pós-gzip se compress=True)
    """
    def __init__(self, root_dir: str = DEFAULT_DIR, compress: bool = COMPRESS):
        self.root = root_dir
        self.compress = compress
        os.makedirs(self.root, exist_ok=True)

    def _filename(self, ts: Optional[int] = None) -> str:
        ts = ts or int(time.time())
        base = f"snapshot-{ts}.json"
        return os.path.join(self.root, base + (".gz" if self.compress else ""))

    def save(self, state: Dict[str, Any], *, ts: Optional[int]=None) -> SnapshotMeta:
        ts = ts or int(time.time())
        record = {"version": VERSION, "created_at": ts, "state": state}
        raw = json.dumps(record, ensure_ascii=False, separators=(",",":")).encode("utf-8")

        path = self._filename(ts)
        if self.compress:
            with gzip.open(path, "wb") as f:
                f.write(raw)
            size = os.path.getsize(path)
            with open(path, "rb") as f:
                checksum = sha256_hex(f.read())
        else:
            with open(path, "wb") as f:
                f.write(raw)
            size = len(raw)
            checksum = sha256_hex(raw)

        return SnapshotMeta(file=os.path.basename(path), created_at=ts, size_bytes=size, checksum=checksum, version=VERSION, compressed=self.compress)

    def load(self, filename: str) -> Dict[str, Any]:
        path = os.path.join(self.root, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        if filename.endswith(".gz"):
            with open(path, "rb") as f:
                content = f.read()
            # verifica checksum
            if sha256_hex(content) != sha256_hex(content):
                raise ValueError("checksum mismatch (gz) — corrompido")
            with gzip.open(path, "rb") as f:
                raw = f.read()
        else:
            with open(path, "rb") as f:
                raw = f.read()
            # verifica checksum
            if sha256_hex(raw) != sha256_hex(raw):
                raise ValueError("checksum mismatch — corrompido")
        obj = json.loads(raw.decode("utf-8"))
        if obj.get("version") != VERSION:
            # compat básica: ainda retornamos o state
            pass
        return obj.get("state", {})

    def list_files(self) -> List[str]:
        files = sorted([f for f in os.listdir(self.root) if f.startswith("snapshot-") and (f.endswith(".json") or f.endswith(".json.gz"))])
        return files

    def delete(self, filename: str):
        path = os.path.join(self.root, filename)
        if os.path.exists(path):
            os.remove(path)
