# janus/core/secrets/signer.py
import hmac, hashlib, base64
from typing import Protocol, Tuple, Optional
from .keystore import LocalKeyStore, KeyRecord

class Signer(Protocol):
    def sign(self, data: bytes) -> Tuple[str, bytes]:
        """
        Retorna (key_id, assinatura_bytes)
        """
        ...

    def verify(self, key_id: str, data: bytes, signature: bytes) -> bool:
        ...

class HMACSigner:
    """
    Assinatura simétrica HMAC-SHA256 usando chave do LocalKeyStore.
    Ideal para *proof-of-relay* e autenticidade entre relays conhecidos.
    """
    def __init__(self, keystore: LocalKeyStore):
        self.keystore = keystore

    def _key_for(self) -> KeyRecord:
        rec = self.keystore.resolve_active("HMAC-SHA256")
        if not rec:
            # gera uma automaticamente se não houver
            rec = self.keystore.generate_hmac_key(ttl_days=90)
        return rec

    def sign(self, data: bytes) -> Tuple[str, bytes]:
        rec = self._key_for()
        key = base64.b64decode(rec.material_b64)
        mac = hmac.new(key, data, hashlib.sha256).digest()
        return rec.key_id, mac

    def verify(self, key_id: str, data: bytes, signature: bytes) -> bool:
        rec = self.keystore.get(key_id)
        if not rec or rec.algo != "HMAC-SHA256":
            return False
        key = base64.b64decode(rec.material_b64)
        mac = hmac.new(key, data, hashlib.sha256).digest()
        return hmac.compare_digest(mac, signature)

# Observação: suporte a ED25519/secp256k1 pode ser adicionado aqui,
# pluggando uma lib externa quando desejar (ex.: pynacl/cryptography).
