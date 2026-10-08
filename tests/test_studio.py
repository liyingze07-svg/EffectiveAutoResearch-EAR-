"""Verify demo provenance, actual offline execution and the bounded HTTP surface."""
import base64
import http.client
from http.server import HTTPServer
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import unittest

from ear import studio


class StudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="EAR studio tests ")
        cls.root = Path(cls.temp.name)
        cls.data = studio.build_data(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_artifacts_come_from_executed_engine_and_preserve_fixture_status(self):
        math = self.data["math"]
        self.assertFalse(math["accepted"])
        self.assertEqual(math["status"], "offline_demo")
        self.assertEqual(math["model_calls"], 0)
        self.assertEqual([r["result"]["status"] for r in math["rounds"]], ["rejected", "offline_demo"])
        self.assertNotEqual(math["rounds"][0]["result"]["content_hash"], math["rounds"][1]["result"]["content_hash"])
        self.assertIn("Boundary case unresolved", math["rounds"][0]["tex"])
        self.assertIn("including $x=0$", math["rounds"][1]["tex"])
        pdf = next(a for a in math["artifacts"] if a["name"] == "paper/main.pdf")
        self.assertTrue(base64.b64decode(pdf["content"]).startswith(b"%PDF-"))
        self.assertEqual(self.data["rebuttal"]["model_calls"], 0)
        self.assertFalse(self.data["rebuttal"]["quality_evaluated"])
        self.assertIn("DRY", self.data["rebuttal"]["plan"])

    def test_evidence_is_recomputed_and_snapshot_is_script_safe(self):
        expected = json.loads((studio.ROOT / "docs/technical-report/v6/data/derived_metrics.json").read_text())
        self.assertEqual(self.data["evidence"]["metrics"], expected)
        self.assertEqual(self.data["evidence"]["verified_files"], 48)
        malicious = {**self.data, "test": "</script><script>alert('example')</script>"}
        html = studio.render(malicious, live=False).decode()
        self.assertNotIn("__EAR_STUDIO_DATA__", html)
        self.assertNotIn(malicious["test"], html)
        self.assertIn('"live": false', html)
        self.assertNotIn(str(self.root), html)

    def test_case_ranking_preserves_released_scores_and_decisions(self):
        evidence = self.data["evidence"]
        rows = evidence["screening"]
        self.assertEqual([row["rank"] for row in rows], list(range(1, 7)))
        self.assertEqual(rows[0]["id"], "IDEA-04")
        self.assertEqual(rows[-1]["id"], "IDEA-06")
        self.assertEqual(rows[-1]["recommendation"], "ABANDON")
        for row in rows:
            score = .25 * row["novelty"] + .35 * row["venue"] + .20 * row["strategic"] + .20 * row["feasibility"]
            self.assertAlmostEqual(row["composite"], score, delta=.006)
        self.assertIn("3/16", evidence["files"][10]["content"])
        with self.assertRaises(ValueError):
            studio.screening_rows("| 1 | invented | 8 | 6 | 7 | 7 | 7 | PROCEED |")

    def test_export_from_external_directory_and_refuse_overwrite(self):
        path = self.root / "shareable demo.html"
        command = ["bash", str(studio.ROOT / "ear.sh"), "demo", "studio", "--export", str(path)]
        result = subprocess.run(command, cwd=self.root, text=True, capture_output=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stderr)
        before = path.read_bytes()
        result = subprocess.run(command, cwd=self.root, text=True, capture_output=True, timeout=45)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(path.read_bytes(), before)

    def test_http_only_runs_fixed_offline_actions(self):
        server = HTTPServer(("127.0.0.1", 0), studio.handler_for(self.data, self.root))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            origin = f"http://127.0.0.1:{server.server_port}"
            def request(method, path, headers=None, body=None):
                connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=45)
                connection.request(method, path, body=body, headers=headers or {})
                response = connection.getresponse()
                payload = response.read()
                connection.close()
                return response.status, payload
            status, page = request("GET", "/")
            self.assertEqual(status, 200)
            self.assertIn(b'"live": true', page)
            self.assertEqual(request("GET", "/../../ear/studio.py")[0], 404)
            self.assertEqual(request("POST", "/api/run/math")[0], 403)
            self.assertEqual(request("POST", "/api/run/math", {"Origin": "https://example.com"})[0], 403)
            self.assertEqual(request("POST", "/api/run/live", {"Origin": origin})[0], 404)
            self.assertEqual(request("POST", "/api/run/math", {"Origin": origin}, '{"command":"example"}')[0], 400)
            status, payload = request("POST", "/api/run/math", {"Origin": origin})
            self.assertEqual(status, 200)
            result = json.loads(payload)
            self.assertEqual(result["model_calls"], 0)
            self.assertFalse(result["accepted"])
            self.assertEqual(len(result["rounds"]), 2)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_incomplete_browser_connection_does_not_block_page_load(self):
        server = studio.ThreadingHTTPServer(("127.0.0.1", 0), studio.handler_for(self.data, self.root))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        idle = socket.create_connection(server.server_address, timeout=3)
        try:
            # A browser may establish a connection before completing its headers.
            idle.sendall(b"GET / HTTP/1.1\r\nHost: 127.0.0.1\r\n")
            connection = http.client.HTTPConnection(*server.server_address, timeout=3)
            try:
                connection.request("GET", "/?lang=zh")
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                self.assertIn(b'"live": true', response.read())
            finally:
                connection.close()
            # Complete the first request as well, avoiding an abandoned response.
            idle.sendall(b"\r\n")
            while idle.recv(65536):
                pass
        finally:
            idle.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
