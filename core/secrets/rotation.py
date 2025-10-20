# janus/core/secrets/rotation.py
import time
from typing import Optional
from .keystore import LocalKeyStore, KeyRecord

class RotationPolicy:
    """
    Política simples de rotação:
     - Expira em `max_age_days` (se expires_at ausente, usa created_at + max_age_days)
     - Mantém no máximo `max_active` chaves ativas por algoritmo
    """
    def __init__(self, max_age_days: int = 90, max_active: int = 2):
        self.max_age_days = max_age_days
        self.max_active = max_active

    def is_expired(self, rec: KeyRecord) -> bool:
        now = int(time.time())
        exp = rec.expires_at or (rec.created_at + self.max_age_days * 86400)
        return now >= exp

def rotate_if_needed(keystore: LocalKeyStore, algo: str = "HMAC-SHA256", policy: Optional[RotationPolicy]=None) -> Optional[KeyRecord]:
    policy = policy or RotationPolicy()
    # desativa chaves expiradas
    for rec in list(keystore.list_keys(only_active=True)):
        if rec.algo == algo and policy.is_expired(rec):
            keystore.deactivate(rec.key_id)

    # garante limite de ativas
    active = [r for r in keystore.list_keys(only_active=True) if r.algo == algo]
    if len(active) > policy.max_active:
        # desativa as mais antigas
        for old in sorted(active, key=lambda r: r.created_at)[:-policy.max_active]:
            keystore.deactivate(old.key_id)

    # se não há nenhuma ativa, gera uma nova
    if not any(r.algo == algo for r in keystore.list_keys(only_active=True)):
        return keystore.generate_hmac_key(ttl_days=policy.max_age_days)
    return None
