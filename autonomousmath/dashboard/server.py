"""Stdlib dashboard with workspace-scoped control and request-origin protection."""

from __future__ import annotations

import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
from pathlib import Path
import secrets
import threading
from urllib.parse import urlsplit

from autonomousmath.optimizer.evolution import Evolution, EvolutionBusy


class Dashboard:
    def __init__(self, optimizer: Evolution):
        self.optimizer = optimizer
        self.token = secrets.token_urlsafe(32)
        self._lock = threading.Lock()
        self.thread: threading.Thread | None = None

    def start(self):
        with self._lock:
            if (self.thread and self.thread.is_alive()) or self.optimizer.active():
                return {"started": False, "active": True}
            def run():
                try:
                    self.optimizer.run()
                except EvolutionBusy:
                    pass  # A concurrent CLI start owns the writer; never create a second run.
                except Exception as error:
                    self.optimizer._change_state(lambda state: state.update(status="error", error=str(error)))
            self.thread = threading.Thread(target=run, name="autonomousmath-evolution", daemon=True)
            self.thread.start()
            return {"started": True, "active": True}


def make_server(workspace, host="127.0.0.1", port=8765, *, optimizer=None):
    if host == "localhost":
        host = "127.0.0.1"
    if not ipaddress.ip_address(host).is_loopback:
        raise ValueError("dashboard binds only to loopback")
    controller = Dashboard(optimizer or Evolution(workspace))
    controller.optimizer.initialize()
    template = (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")

    class Handler(BaseHTTPRequestHandler):
        def _json(self, value, status=200):
            body = json.dumps(value, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _trusted_host(self):
            try:
                parsed = urlsplit("http://" + self.headers.get("Host", ""))
                return parsed.hostname in ("localhost", "127.0.0.1", "::1") and parsed.port == self.server.server_port
            except ValueError:
                return False

        def do_GET(self):
            if not self._trusted_host():
                return self._json({"error": "invalid local host"}, 403)
            if self.path == "/api/state":
                return self._json(controller.optimizer.snapshot())
            if self.path != "/":
                return self._json({"error": "not found"}, 404)
            body = template.replace("__CONTROL_TOKEN__", controller.token).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if not self._trusted_host():
                return self._json({"error": "invalid local host"}, 403)
            token = self.headers.get("X-Control-Token", "")
            origin = self.headers.get("Origin")
            expected_origin = "http://" + self.headers.get("Host", "")
            if not hmac.compare_digest(token, controller.token) or (origin and origin != expected_origin):
                return self._json({"error": "control token or origin rejected"}, 403)
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size > 8192:
                    return self._json({"error": "request too large"}, 413)
                body = json.loads(self.rfile.read(size) or b"{}")
                if not isinstance(body, dict):
                    raise ValueError("JSON object required")
                if self.path == "/api/start":
                    return self._json(controller.start())
                if self.path == "/api/pause":
                    return self._json(controller.optimizer.set_control({"enabled": False}))
                if self.path == "/api/panic":
                    controller.optimizer.emergency_stop()
                    return self._json({"status": "stopping"})
                if self.path == "/api/control":
                    # The browser cannot silently switch an offline session into model spending.
                    allowed = {"parallelism", "generations", "continuous", "interval_seconds", "population_size"}
                    if set(body) - allowed:
                        raise ValueError("dashboard changes only scheduling controls")
                    return self._json(controller.optimizer.set_control(body))
                return self._json({"error": "not found"}, 404)
            except (ValueError, TypeError) as error:
                return self._json({"error": str(error)}, 400)

        def log_message(self, *args):
            pass

    class LocalServer(ThreadingHTTPServer):
        daemon_threads = True
    if ":" in host:
        import socket
        LocalServer.address_family = socket.AF_INET6
    server = LocalServer((host, port), Handler)
    server.controller = controller
    return server


def serve(workspace, host="127.0.0.1", port=8765):
    server = make_server(workspace, host, port)
    address = server.server_address
    printable_host = f"[{address[0]}]" if ":" in address[0] else address[0]
    print(f"AutonomousMath dashboard: http://{printable_host}:{address[1]}/", flush=True)
    print("Opening the dashboard does not start evolution. Start uses this workspace's existing mode.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.controller.optimizer.set_control({"enabled": False})
        worker = server.controller.thread
        if worker and worker.is_alive():
            print("Paused new episodes; waiting for in-flight work to finish.", flush=True)
            worker.join()
    finally:
        server.server_close()
    return 0
