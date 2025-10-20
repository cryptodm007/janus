# janus/api/auth.py
import os
from typing import Set

# Le chaves do ambiente (use .env, Docker secrets, etc.)
READONLY_KEY = os.getenv("JANUS_API_KEY_READONLY", "")
ADMIN_KEY    = os.getenv("JANUS_API_KEY_ADMIN", "")

# Scopes canônicos (compatíveis com a Fase 14 + granularidades admin)
SCOPE_HEALTH   = "health:read"
SCOPE_STATE_R  = "state:read"
SCOPE_METRICS  = "metrics:read"

# Escopos administrativos (granulares)
SCOPE_ADMIN_ANY   = "admin:*"
SCOPE_ADMIN_SNAP  = "admin:snapshot"
SCOPE_ADMIN_REST  = "admin:restore"
SCOPE_ADMIN_PRUNE = "admin:prune"

READONLY_SCOPES: Set[str] = {SCOPE_HEALTH, SCOPE_STATE_R, SCOPE_METRICS}
ADMIN_SCOPES: Set[str] = {
    SCOPE_HEALTH, SCOPE_STATE_R, SCOPE_METRICS,
    SCOPE_ADMIN_ANY, SCOPE_ADMIN_SNAP, SCOPE_ADMIN_REST, SCOPE_ADMIN_PRUNE
}

def scopes_for_key(api_key: str) -> Set[str]:
    if not api_key:
        return set()
    if ADMIN_KEY and api_key == ADMIN_KEY:
        return set(ADMIN_SCOPES)
    if READONLY_KEY and api_key == READONLY_KEY:
        return set(READONLY_SCOPES)
    return set()

def check_scope(scopes: Set[str], required: str) -> bool:
    return (SCOPE_ADMIN_ANY in scopes) or (required in scopes)

def parse_auth_header(authorization: str | None) -> str:
    if not authorization:
        return ""
    # Aceita "Bearer <token>" ou o token cru
    parts = authorization.strip().split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return authorization.strip()
