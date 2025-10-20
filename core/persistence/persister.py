# janus/core/persistence/persister.py
import asyncio, json, time
from typing import Optional, Dict, Any
from core.observability import logger
from core.observability.metrics import metrics
from core.state_manager import StateManager
from .store import SnapshotStore
from .manifest import SnapshotManifest

SNAP_TOTAL = metrics.counter("janus_snapshots_total", "Snapshots criados")
SNAP_ERRORS = metrics.counter("janus_snapshots_errors_total", "Erros ao criar snapshot")

class AutoPersister:
    """
    Tarefa assíncrona que cria snapshots periódicos ou sob mudança de timestamp.
    Critérios:
      - Intervalo fixo (interval_sec)
      - Mudança detectada no timestamp do estado (se 'timestamp' aumentar)
    """
    def __init__(self, state: StateManager, store: Optional[SnapshotStore]=None, manifest: Optional[SnapshotManifest]=None,
                 interval_sec: int = 60, on_change: bool = True):
        self.state = state
        self.store = store or SnapshotStore()
        self.manifest = manifest or SnapshotManifest(self.store.root)
        self.interval_sec = interval_sec
        self.on_change = on_change
        self._last_ts = None
        self._running = False

    def _changed(self, st: Dict[str, Any]) -> bool:
        ts = st.get("timestamp")
        if ts is None:
            return False
        if self._last_ts is None:
            self._last_ts = ts
            return True  # primeiro estado conhecido
        if ts > self._last_ts:
            self._last_ts = ts
            return True
        return False

    async def run(self):
        self._running = True
        while self._running:
            try:
                st = self.state.get_state() if hasattr(self.state, "get_state") else {}
                should = True
                if self.on_change:
                    should = self._changed(st)
                if should:
                    meta = self.store.save(st)
                    self.manifest.add(meta)
                    SNAP_TOTAL.inc(1)
                    logger.info("snapshot_saved", ctx={"trace":"persist"}, file=meta.file, size=meta.size_bytes, ts=meta.created_at)
            except Exception as e:
                SNAP_ERRORS.inc(1)
                logger.error("snapshot_error", ctx={"trace":"persist"}, exc=e)
            await asyncio.sleep(self.interval_sec)

    def stop(self):
        self._running = False
