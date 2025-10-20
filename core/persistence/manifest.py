# janus/core/persistence/manifest.py
import os, json, time
from typing import List, Dict, Any, Optional
from .store import SnapshotMeta, DEFAULT_DIR

MANIFEST_FILE = "manifest.json"

class SnapshotManifest:
    """
    Mantém um índice simples dos snapshots (append-only).
    """
    def __init__(self, root_dir: str = DEFAULT_DIR):
        self.root = root_dir
        self.path = os.path.join(self.root, MANIFEST_FILE)
        os.makedirs(self.root, exist_ok=True)
        self._data: Dict[str, Any] = {"snapshots": []}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            self._data = json.load(open(self.path, "r", encoding="utf-8"))

    def _save(self):
        json.dump(self._data, open(self.path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    def add(self, meta: SnapshotMeta):
        self._data.setdefault("snapshots", []).append({
            "file": meta.file,
            "created_at": meta.created_at,
            "size_bytes": meta.size_bytes,
            "checksum": meta.checksum,
            "version": meta.version,
            "compressed": meta.compressed
        })
        self._save()

    def list(self) -> List[Dict[str, Any]]:
        return list(self._data.get("snapshots", []))

    def latest(self) -> Optional[Dict[str, Any]]:
        items = self.list()
        if not items:
            return None
        return sorted(items, key=lambda x: x["created_at"], reverse=True)[0]

    def prune(self, *, keep_last: int = 10, keep_days: int = 7) -> List[str]:
        """
        Retém os N últimos e os criados nos últimos D dias.
        Retorna lista de arquivos sugeridos para remoção.
        """
        items = sorted(self.list(), key=lambda x: x["created_at"], reverse=True)
        keep = set()
        now = int(time.time())

        # mantém últimos N
        for it in items[:keep_last]:
            keep.add(it["file"])

        # mantém janela de dias
        for it in items:
            if now - int(it["created_at"]) <= keep_days * 86400:
                keep.add(it["file"])

        # candidatos a remoção
        to_delete = [it["file"] for it in items if it["file"] not in keep]
        # atualiza manifest removendo os deletados
        if to_delete:
            self._data["snapshots"] = [it for it in items if it["file"] not in to_delete]
            self._save()
        return to_delete
