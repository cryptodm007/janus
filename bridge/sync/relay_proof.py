import hashlib
import time

class RelayProof:
    def __init__(self):
        self.validators = {}

    def register_validator(self, node_id, public_key):
        self.validators[node_id] = public_key

    def verify_block(self, block_hash, signatures):
        # mínimo de ⅔ dos validadores devem assinar (simulação)
        required = (len(self.validators) * 2) // 3
        valid = sum(sig.get("valid", False) for sig in signatures)
        return valid >= required

    def generate_proof(self, data: str):
        digest = hashlib.sha256(data.encode()).hexdigest()
        return {
            "timestamp": int(time.time()),
            "hash": digest
        }
