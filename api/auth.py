# janus/api/auth.py
import os
from typing import Set, Tuple

# Le chaves do ambiente (use .env, Docker secrets, etc.)
READONLY_KEY = os.getenv("JANUS_API_KEY_READONLY", "")
ADMIN_KEY    = os.getenv("JANUS_API_KEY_ADMIN", "")

# Scopes canônicos (compatíveis com a Fase 14)
SCOPE_HEALTH  = "health:read"
SCOPE_STATE_R = "state:read"
SCOPE_METRICS = "metrics:read"
SCOPE_ADMIN   = "admin:*"

def scopes_for_key(api_key: str) -> Set[str]:
    if not api_key:
        return set()
    if ADMIN_KEY and api_key == ADMIN_KEY:
        return {SCOPE_HEALTH, SCOPE_STATE_R, SCOPE_METRICS, SCOPE_ADMIN}
    if READONLY_KEY and api_key == READONLY_KEY:
        return {SCOPE_HEALTH, SCOPE_STATE_R, SCOPE_METRICS}
    return set()

def check_scope(scopes: Set[str], required: str) -> bool:
    if "admin:*" in scopes:
        return True
    return required in scopes

def parse_auth_header(authorization: str | None) -> str:
    if not authorization:
        return ""
    # Aceita "Bearer <token>" ou o token cru
    parts = authorization.strip().split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return authorization.strip()
