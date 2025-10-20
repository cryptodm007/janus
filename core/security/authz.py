from functools import wraps
from typing import Optional, Callable
from .acl import ACL
from .models import Principal
from .audit import audit_log

class AuthorizationError(Exception):
    pass

class Authorizer:
    def __init__(self, acl: Optional[ACL]=None):
        self.acl = acl or ACL()

    def check(self, principal: Principal, scope: str):
        if not self.acl.allowed(principal, scope):
            audit_log("deny", principal_id=principal.principal_id, decision="deny", reason=f"missing:{scope}")
            raise AuthorizationError(f"principal '{principal.principal_id}' lacks scope '{scope}'")
        audit_log("allow", principal_id=principal.principal_id, decision="allow", extra={"scope": scope})

def require(authorizer: Authorizer, scope: str):
    def deco(fn: Callable):
        @wraps(fn)
        def inner(*args, **kwargs):
            principal: Principal = kwargs.get("principal")
            if principal is None:
                raise AuthorizationError("principal required")
            authorizer.check(principal, scope)
            return fn(*args, **kwargs)
        return inner
    return deco

def arequire(authorizer: Authorizer, scope: str):
    def deco(fn: Callable):
        @wraps(fn)
        async def inner(*args, **kwargs):
            principal: Principal = kwargs.get("principal")
            if principal is None:
                raise AuthorizationError("principal required")
            authorizer.check(principal, scope)
            return await fn(*args, **kwargs)
        return inner
    return deco
