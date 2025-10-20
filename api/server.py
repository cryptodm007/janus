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
from .handlers import handle_health, handle_state, handle_metrics

HandlerFn = Callable[..., Tuple[int, bytes, str]]

class _Context:
    def __init__(self, state: StateManager):
        self.state = state
        self.routes: Dict[str, HandlerFn] = {
            ("GET", "/health"): lambda scopes: handle_health(self.state, scopes=scopes),
            ("GET", "/state"):  lambda scopes: handle_state(self.state, scopes=scopes),
            ("GET", "/metrics"):lambda scopes: handle_metrics(scopes=scopes),
        }

class JanusHTTPRequestHandler(BaseHTTPRequestHandler):
    server_version = "JanusHTTP/1.0"
    protocol_version = "HTTP/1.1"

    # context é injetado pela fábrica de server
    context: _Context = None  # type: ignore

    def _write(self, status: int, body: bytes, ctype: str):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try:
            with span("http.get") as sp:
                route = (self.command, self.path.split("?")[0])
                handler = self.context.routes.get(route)
                if not handler:
                    self._write(404, b'{"error":"not_found"}', "application/json")
                    return

                # auth
                token = parse_auth_header(self.headers.get("Authorization"))
                scopes = scopes_for_key(token)

                status, body, ctype = handler(scopes=scopes)
                self._write(status, body, ctype)
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
