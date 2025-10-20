# janus/core/secrets/keystore.py
import os, json, stat, time, base64, secrets
from dataclasses import dataclass, asdict
from typing import Dict, Optional, List

SECRETS_DIR = ".secrets"
KEYS_FILE   = "keys.json"

@dataclass
class KeyRecord:
    key_id: str
    algo: str            # ex.: "HMAC-SHA256" | "ED25519"
    created_at: int      # epoch sec
    material_b64: str    # base64 do material da chave
    active: bool = True
    expires_at: Optional[int] = None  # epoch sec ou None

class LocalKeyStore:
    """
    Keystore local baseado em arquivo JSON (sem criptografia).
    **Atenção**: confie em permissões de FS + CI/CD vault externo.
    """
    def __init__(self, root_dir: str = SECRETS_DIR):
        self.root_dir = root_dir
        self.path = os.path.join(root_dir, KEYS_FILE)
        self._db: Dict[str, KeyRecord] = {}
        self._ensure_dirs()
        self._load()

    def _ensure_dirs(self):
        os.makedirs(self.root_dir, exist_ok=True)
        # chmod 700 no diretório
        try:
            os.chmod(self.root_dir, stat.S_IRWXU)
        except Exception:
            pass

    def _load(self):
        if not os.path.exists(self.path):
            self._save()
            return
        with open(self.path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self._db = {k: KeyRecord(**v) for k, v in raw.items()}

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({k: asdict(v) for k, v in self._db.items()}, f, indent=2)
        # chmod 600 no arquivo
        try:
            os.chmod(self.path, stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass

    # ------------ API pública ------------
    def list_keys(self, only_active: bool=False) -> List[KeyRecord]:
        items = list(self._db.values())
        return [k for k in items if (k.active if only_active else True)]

    def get(self, key_id: str) -> Optional[KeyRecord]:
        return self._db.get(key_id)

    def put(self, rec: KeyRecord):
        self._db[rec.key_id] = rec
        self._save()

    def deactivate(self, key_id: str):
        if key_id in self._db:
            self._db[key_id].active = False
            self._save()

    def delete(self, key_id: str):
        if key_id in self._db:
            del self._db[key_id]
            self._save()

    def generate_hmac_key(self, *, key_id: Optional[str]=None, bytes_len: int=32, ttl_days: Optional[int]=None) -> KeyRecord:
        kid = key_id or secrets.token_hex(8)
        material = secrets.token_bytes(bytes_len)
        rec = KeyRecord(
            key_id=kid,
            algo="HMAC-SHA256",
            created_at=int(time.time()),
            material_b64=base64.b64encode(material).decode(),
            active=True,
            expires_at=(int(time.time()) + ttl_days*86400) if ttl_days else None
        )
        self.put(rec)
        return rec

    def resolve_active(self, algo: str) -> Optional[KeyRecord]:
        # retorna a chave ativa mais nova do algoritmo
        candidates = [k for k in self._db.values() if k.active and k.algo == algo]
        if not candidates:
            return None
        return sorted(candidates, key=lambda r: r.created_at, reverse=True)[0]
