import json, os, sys, time, traceback
from typing import Any, Dict, Optional

_LEVELS = {"DEBUG":10,"INFO":20,"WARN":30,"ERROR":40}
_DEFAULT_LEVEL = _LEVELS.get(os.getenv("JANUS_LOG_LEVEL","INFO").upper(),20)

def _ts_ms() -> int:
    return int(time.time() * 1000)

def _emit(record: Dict[str, Any]):
    sys.stdout.write(json.dumps(record, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def _log(level_name: str, msg: str, *, ctx: Optional[Dict[str,Any]]=None, **fields):
    level = _LEVELS[level_name]
    if level < _DEFAULT_LEVEL:
        return
    record = {
        "ts": _ts_ms(),
        "level": level_name,
        "msg": msg,
        **(ctx or {}),
        **fields,
    }
    _emit(record)

def debug(msg, **kw): _log("DEBUG", msg, **kw)
def info(msg, **kw):  _log("INFO",  msg, **kw)
def warn(msg, **kw):  _log("WARN",  msg, **kw)
def error(msg, **kw):
    exc = kw.pop("exc", None)
    if exc:
        kw["error"] = {"type": type(exc).__name__, "message": str(exc), "stack": traceback.format_exc()}
    _log("ERROR", msg, **kw)
