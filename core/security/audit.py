from typing import Optional, Dict, Any
from core.observability import logger

def audit_log(action: str, *, principal_id: str, decision: str, reason: Optional[str]=None, extra: Optional[Dict[str,Any]]=None):
    logger.info("security_audit", ctx={"trace":"security"}, action=action,
                principal_id=principal_id, decision=decision, reason=reason, **(extra or {}))
