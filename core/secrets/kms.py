# janus/core/secrets/kms.py
import os, base64, time
from typing import Optional
from .keystore import KeyRecord

class KMS:
    """
    Interface p/ KMS externo (HashiCorp Vault, AWS KMS, GCP KMS, Azure).
    """
    def get_key(self, key_id: str) -> Optional[KeyRecord]:
        raise NotImplementedError
    def put_key(self, rec: KeyRecord) -> None:
        raise NotImplementedError

class DummyKMS(KMS):
    """
    KMS dummy via ENV (para CI/PoC). Define:
      - JANUS_KMS_KEY_ID
      - JANUS_KMS_MATERIAL_B64  (material simétrico HMAC)
    """
    def get_key(self, key_id: str) -> Optional[KeyRecord]:
        kid = os.getenv("JANUS_KMS_KEY_ID")
        mat = os.getenv("JANUS_KMS_MATERIAL_B64")
        if not kid or not mat or kid != key_id:
            return None
        return KeyRecord(
            key_id=kid,
            algo="HMAC-SHA256",
            created_at=int(time.time()),
            material_b64=mat,
            active=True
        )

    def put_key(self, rec: KeyRecord) -> None:
        # Apenas logicamente — não persiste
        pass
