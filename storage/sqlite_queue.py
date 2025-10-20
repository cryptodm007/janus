# storage/sqlite_queue.py
from __future__ import annotations
import sqlite3, json, time
from typing import List
from core.schemas import JobEnvelope, CoreEvent
from core.interfaces import JobQueueBackend

class SQLiteQueueBackend(JobQueueBackend):
    def __init__(self, path: str, backoff_cap: float = 60.0):
        self.path = path
        self.backoff_cap = backoff_cap
        self._ensure_schema()

    def _conn(self):
        return sqlite3.connect(self.path, timeout=10, isolation_level=None)

    def _ensure_schema(self):
        with self._conn() as c:
            c.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
              job_id TEXT PRIMARY KEY,
              payload TEXT NOT NULL,
              attempts INTEGER NOT NULL,
              max_attempts INTEGER NOT NULL,
              next_run_at REAL NOT NULL,
              acked INTEGER NOT NULL DEFAULT 0,
              error TEXT,
              created_at REAL NOT NULL
            )""")
            c.execute("""
            CREATE TABLE IF NOT EXISTS dlq (
              job_id TEXT,
              payload TEXT,
              attempts INTEGER,
              reason TEXT,
              dead_at REAL
            )""")
            c.execute("CREATE INDEX IF NOT EXISTS idx_jobs_next ON jobs(next_run_at)")

    def enqueue(self, env: JobEnvelope) -> None:
        with self._conn() as c:
            c.execute("""
              INSERT OR IGNORE INTO jobs(job_id,payload,attempts,max_attempts,next_run_at,acked,error,created_at)
              VALUES(?,?,?,?,?,?,?,?)
            """, (env.job_id, env.model_dump_json(), env.attempts, env.max_attempts, env.next_run_at, int(env.acked), env.error, time.time()))

    def pop_due(self, now: float, limit: int) -> List[JobEnvelope]:
        out: List[JobEnvelope] = []
        with self._conn() as c:
            rows = c.execute("""
              SELECT payload FROM jobs
              WHERE acked=0 AND next_run_at<=?
              ORDER BY next_run_at ASC
              LIMIT ?
            """, (now, limit)).fetchall()
        for (payload_json,) in rows:
            out.append(JobEnvelope.model_validate_json(payload_json))
        return out

    def requeue(self, env: JobEnvelope) -> None:
        with self._conn() as c:
            c.execute("""
              UPDATE jobs SET attempts=?, next_run_at=?, error=?
              WHERE job_id=?
            """, (env.attempts, env.next_run_at, env.error, env.job_id))

    def ack(self, env: JobEnvelope) -> None:
        with self._conn() as c:
            c.execute("UPDATE jobs SET acked=1 WHERE job_id=?", (env.job_id,))

    def dead_letter(self, env: JobEnvelope, reason: str) -> None:
        with self._conn() as c:
            c.execute("INSERT INTO dlq(job_id,payload,attempts,reason,dead_at) VALUES(?,?,?,?,?)",
                      (env.job_id, env.model_dump_json(), env.attempts, reason, time.time()))
            c.execute("DELETE FROM jobs WHERE job_id=?", (env.job_id,))
