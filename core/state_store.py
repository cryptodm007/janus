# core/state_store.py
from __future__ import annotations
import json
import threading
from pathlib import Path
from typing import Any, Optional, Dict

class StateStore:
    """
    KV Store simples baseado em arquivo para snapshots e marcações de progresso.
    Substituível por Redis/SQLite posteriormente.
    """
    def __init__(self, path: str = ".runtime/state.json"):
        self._path = Path(path)
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write({})

    def _read(self) -> Dict[str, Any]:
        with self._lock:
            if self._path.exists():
                return json.loads(self._path.read_text() or "{}")
            return {}

    def _write(self, data: Dict[str, Any]) -> None:
        with self._lock:
            self._path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        data = self._read()
        return data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        data = self._read()
        data[key] = value
        self._write(data)

    def compare_and_set(self, key: str, expected: Any, new_value: Any) -> bool:
        data = self._read()
        if data.get(key) == expected:
            data[key] = new_value
            self._write(data)
            return True
        return False
