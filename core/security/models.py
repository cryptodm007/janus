from dataclasses import dataclass, field
from typing import Set, Dict

Scope = str  # "namespace:action" (ex.: "state:update")

@dataclass
class Role:
    name: str
    scopes: Set[Scope] = field(default_factory=set)

@dataclass
class Principal:
    """
    Representa um agente/nó/usuário do sistema.
    """
    principal_id: str
    roles: Set[str] = field(default_factory=set)  # nomes de roles
    attrs: Dict[str, str] = field(default_factory=dict)
