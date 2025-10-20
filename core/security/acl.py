from typing import Set, Dict
from .models import Principal
from .policy_bindings import DEFAULT_ROLES

class ACL:
    """
    Resolve os scopes efetivos de um principal a partir de seus roles.
    Permite bindings extras em runtime (ex.: carregados de config).
    """
    def __init__(self, roles=None):
        self.roles = roles or DEFAULT_ROLES

    def effective_scopes(self, p: Principal) -> Set[str]:
        scopes: Set[str] = set()
        for rname in p.roles:
            role = self.roles.get(rname)
            if role:
                scopes |= set(role.scopes)
        return scopes

    def allowed(self, p: Principal, scope: str) -> bool:
        return scope in self.effective_scopes(p)
