# janus/api/server.py
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from typing import Callable, Dict, Tuple
import json
import os

from core.observability import logger
from core.observability.tracing import span
from core.state_manager import StateManager
from .auth import parse_auth_header, scopes_for_key
from .handlers import (
    handle_health, handle_state, handle_metrics,
    handle_admin_snapshot, handle_admin_snapshots_list,
    handle_admin_restore, handle_admin_prune
)

HandlerFn = Callable[..., Tuple[int, bytes, str]]

class _Context:
    def __init__(self, state: StateManager):
        self.state = state
        # GET routes
        self.routes_get: Dict[Tuple[str, str], HandlerFn] = {
            ("GET", "/health"):  lambda scopes: handle_health(self.state, scopes=scopes),
            ("GET", "/state"):   lambda scopes: handle_state(self.state, scopes=scopes),
            ("GET", "/metrics"): lambda scopes: handle_metrics(scopes=scopes),
            # admin list
            ("GET", "/admin/snapshots"): lambda scopes: handle_admin_snapshots_list(scopes=scopes),
        }
        # POST routes
        self.routes_post: Dict[Tuple[str, str], HandlerFn] = {
            ("POST", "/admin/snapshot"): lambda scopes, body: handle_admin_snapshot(self.state, scopes=scopes),
            ("POST", "/admin/restore"):  lambda scopes, body: handle_admin_restore(self.state, scopes=scopes, body=body),
            ("POST", "/admin/prune"):    lambda scopes, body: handle_admin_prune(scopes=scopes, body=body),
        }

class JanusHTTPRequestHandler(BaseHTTPRequestHandler):
    server_version = "JanusHTTP/1.1"
    protocol_version = "HTTP/1.1"

    # context é injetado pela fábrica de server
    context: _Context = None  # type: ignore

    def _write(self, status: int, body: bytes, ctype: str):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _scopes(self):
        token = parse_auth_header(self.headers.get("Authorization"))
        return scopes_for_key(token)

    def _read_json_body(self) -> dict:
        length = self.headers.get("Content-Length")
        if not length:
            return {}
        try:
            n = int(length)
        except Exception:
            n = 0
        if n <= 0:
            return {}
        raw = self.rfile.read(n)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def do_GET(self):
        try:
            with span("http.get") as sp:
                route = (self.command, self.path.split("?")[0])
                handler = self.context.routes_get.get(route)
                if not handler:
                    self._write(404, b'{"error":"not_found"}', "application/json")
                    return
                scopes = self._scopes()
                status, body, ctype = handler(scopes=scopes)
                self._write(status, body, ctype)
        except Exception as e:
            logger.error("http_error", ctx={"trace":"api"}, exc=e)
            self._write(500, b'{"error":"internal"}', "application/json")

    def do_POST(self):
        try:
            with span("http.post") as sp:
                route = (self.command, self.path.split("?")[0])
                handler = self.context.routes_post.get(route)
                if not handler:
                    self._write(404, b'{"error":"not_found"}', "application/json")
                    return
                scopes = self._scopes()
                body = self._read_json_body()
                status, resp, ctype = handler(scopes=scopes, body=body)
                self._write(status, resp, ctype)
        except Exception as e:
            logger.error("http_error", ctx={"trace":"api"}, exc=e)
            self._write(500, b'{"error":"internal"}', "application/json")

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

def serve_http(state: StateManager, host: str = "127.0.0.1", port: int = 8080):
    """
    Sobe um HTTP server simples (multi-thread) com os handlers da API.
    """
    context = _Context(state)
    JanusHTTPRequestHandler.context = context
    httpd = ThreadedHTTPServer((host, port), JanusHTTPRequestHandler)
    logger.info("http_listen", ctx={"trace":"api"}, host=host, port=port)
    httpd.serve_forever()

