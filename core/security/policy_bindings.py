from .models import Role

# Papéis padrão do Janus
DEFAULT_ROLES = {
    "relay-node": Role("relay-node", scopes={
        "relay:validate",
        "state:propose"
    }),
    "core-operator": Role("core-operator", scopes={
        "state:update",
        "secrets:rotate",
        "metrics:read"
    }),
    "auditor": Role("auditor", scopes={
        "metrics:read",
        "audit:read"
    }),
}
