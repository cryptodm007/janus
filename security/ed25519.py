# security/ed25519.py
from __future__ import annotations
from typing import Optional
import nacl.signing
import nacl.exceptions

def verify_ed25519(pubkey_hex: str, message_hex: str, sig_hex: str) -> bool:
    try:
        pk = nacl.signing.VerifyKey(bytes.fromhex(pubkey_hex))
        pk.verify(bytes.fromhex(message_hex), bytes.fromhex(sig_hex))
        return True
    except (nacl.exceptions.BadSignatureError, ValueError):
        return False
