"""A portable, zero-model demo built from released evidence and actual offline runs.

The HTTP surface has only fixed demo actions. It never accepts research commands,
paths, provider settings, credentials, or uploaded papers from a browser.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "examples/studio/index.html"
REPOSITORY = "https://github.com/liyingze07-svg/EffectiveAutoResearch-EAR-"


def screening_rows(content: str) -> list[dict]:
    """Read displayed candidate scores from the released ranking, without inventing proposals."""
    rows = []
    for line in content.splitlines():
        cells = [cell.strip().replace("**", "") for cell in line.strip().strip("|").split("|")]
        if len(cells) != 8 or not cells[0].isdigit():
            continue
        candidate = re.fullmatch(r"(IDEA-\d+) (.+)", cells[1])
        if candidate is None:
            raise ValueError("Unexpected candidate in released screening ranking")
        rows.append({"rank": int(cells[0]), "id": candidate[1], "name": candidate[2],
                     "novelty": float(cells[2]), "venue": float(cells[3]),
                     "strategic": float(cells[4]), "feasibility": float(cells[5]),
                     "composite": float(cells[6]), "recommendation": cells[7]})
    if len(rows) != 6 or len({row["id"] for row in rows}) != 6:
        raise ValueError("Expected six distinct candidates in released screening ranking")
    return rows


def _run(arguments: list[str]) -> str:
    result = subprocess.run([sys.executable, "-B", *arguments], cwd=ROOT,
                            text=True, capture_output=True, timeout=45)
    if result.returncode:
        raise RuntimeError("Offline demo failed: " + result.stderr[-2000:])
    return result.stdout


def _relative(value, workspace: Path):
    """Keep shareable run records free of the generating machine's absolute paths."""
    if isinstance(value, dict):
        return {key: _relative(item, workspace) for key, item in value.items()}
    if isinstance(value, list):
        return [_relative(item, workspace) for item in value]
    if isinstance(value, str):
        return value.replace(str(workspace), "workspace")
    return value


def math_demo(parent: Path) -> dict:
    workspace = (parent / "math").resolve()
    _run(["-m", "ear", "math", "run", "--offline", "--workspace", str(workspace), "--episodes", "1"])
    state = json.loads((workspace / "state.json").read_text(encoding="utf-8"))
    episode = state["episodes"][0]
    rounds = []
    artifacts = []
    for report_path in sorted((workspace / "reviews").glob("*/round-*/result.json")):
        report = _relative(json.loads(report_path.read_text(encoding="utf-8")), workspace)
        source = report_path.parent / "source"
        rounds.append({"round": len(rounds) + 1, "result": report,
                       "proof": (source / "proof.md").read_text(encoding="utf-8"),
                       "tex": (source / "paper/main.tex").read_text(encoding="utf-8")})
        for name in ("proof.md", "paper/main.tex"):
            artifacts.append({"name": f"round-{len(rounds)}/{name}", "encoding": "text",
                              "content": (source / name).read_text(encoding="utf-8")})
        artifacts.append({"name": f"round-{len(rounds)}/review.json", "encoding": "text",
                          "content": json.dumps(report, ensure_ascii=False, indent=2)})
    pdf = Path(episode["campaign_dir"]) / "paper/main.pdf"
    artifacts.append({"name": "paper/main.pdf", "encoding": "base64",
                      "content": base64.b64encode(pdf.read_bytes()).decode("ascii")})
    events = [_relative(json.loads(line), workspace) for line in
              (workspace / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    clean_state = _relative(state, workspace)
    artifacts.extend([
        {"name": "state.json", "encoding": "text", "content": json.dumps(clean_state, ensure_ascii=False, indent=2)},
        {"name": "events.jsonl", "encoding": "text", "content": "\n".join(json.dumps(row) for row in events)},
    ])
    return {"kind": "executed_synthetic_fixture", "model_calls": 0,
            "accepted": episode["accepted"], "status": episode["status"],
            "worker_calls": episode["worker_calls"], "review_calls": episode["review_calls"],
            "rounds": rounds, "events": events, "artifacts": artifacts}


def rebuttal_demo(parent: Path) -> dict:
    workspace = (parent / "wiring").resolve()
    _run(["scripts/offline_demo.py", "--output", str(workspace)])
    campaign = workspace / "rebuttal/campaigns/synthetic-demo"
    card = json.loads((campaign / "REBUTTAL_CARD.json").read_text(encoding="utf-8"))
    plan = _relative((workspace / "rebuttal/DRY_RUN.txt").read_text(encoding="utf-8"), workspace)
    artifacts = [{"name": f"{name}.md", "encoding": "text",
                  "content": _relative((campaign / f"{name}.md").read_text(encoding="utf-8"), workspace)}
                 for name in ("CLAUDE", "GOAL", "SPEC", "VERIFY", "RESOURCE")]
    artifacts.extend([
        {"name": "REBUTTAL_CARD.json", "encoding": "text", "content": json.dumps(card, ensure_ascii=False, indent=2)},
        {"name": "DRY_RUN.txt", "encoding": "text", "content": plan},
    ])
    return {"kind": "executed_synthetic_dry_run", "model_calls": 0,
            "quality_evaluated": False, "card": card, "plan": plan, "artifacts": artifacts}


def evidence() -> dict:
    spec = importlib.util.spec_from_file_location("ear_studio_report_check", ROOT / "scripts/check_report.py")
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    verified = checker.verify_report(ROOT / "docs/technical-report/v6")
    paths = [
        "autovibeidea/examples/judge-run/README.md",
        "autovibeidea/examples/judge-run/SCREENING_RANKED.excerpt.md",
        "autovibeidea/examples/judge-run/PIPELINE_LOG.excerpt.md",
        "docs/technical-report/v6/data/idea_process.json",
        "docs/technical-report/v6/data/protocol.json",
        "docs/technical-report/v6/data/round_aggregates.csv",
        "docs/technical-report/v6/data/generation_comparison.csv",
        "docs/technical-report/v6/data/generation_population.csv",
        "docs/technical-report/v6/data/selected_cost.csv",
        "docs/technical-report/v6/data/derived_metrics.json",
        "autovibeidea/examples/judge-run/CRITICAL_ANALYSIS.excerpt.md",
    ]
    files = [{"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
              "content": (ROOT / path).read_text(encoding="utf-8")} for path in paths]
    return {"metrics": verified["metrics"], "verified_files": verified["verified_files"],
            "idea": json.loads((ROOT / paths[3]).read_text(encoding="utf-8")),
            "protocol": json.loads((ROOT / paths[4]).read_text(encoding="utf-8")),
            "screening": screening_rows(files[1]["content"]),
            "files": files}


def build_data(parent: Path) -> dict:
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                           text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.SubprocessError):
        revision = "main"
    design = {kind: {language: (TEMPLATE.parent / "assets" / f"{kind}-architecture.{language}.svg").read_text(encoding="utf-8")
                     for language in ("en", "zh")}
              for kind in ("math", "idea", "rebuttal")}
    reference = json.loads((TEMPLATE.parent / "reference.json").read_text(encoding="utf-8"))
    return {"repository": REPOSITORY, "revision": revision, "evidence": evidence(),
            "math": math_demo(parent), "rebuttal": rebuttal_demo(parent),
            "design": design, "reference": reference}


def render(data: dict, *, live: bool) -> bytes:
    # Escape HTML script termination even if source excerpts contain markup.
    payload = json.dumps({**data, "live": live}, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return TEMPLATE.read_text(encoding="utf-8").replace("__EAR_STUDIO_DATA__", payload).encode("utf-8")


def handler_for(data: dict, runtime: Path):
    class Handler(BaseHTTPRequestHandler):
        # Browsers can preconnect without sending a request. Keep those sockets
        # from blocking page loads or remaining open indefinitely.
        timeout = 10

        def log_message(self, format, *args):
            pass

        def send(self, status: int, content: bytes, mime: str):
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self):
            if urlsplit(self.path).path == "/":
                self.send(200, render(data, live=True), "text/html; charset=utf-8")
            else:
                self.send(404, b"Not found", "text/plain")

        def do_POST(self):
            origin = f"http://127.0.0.1:{self.server.server_port}"
            if self.headers.get("Origin") != origin or self.headers.get("Host") != origin.removeprefix("http://"):
                self.send(403, b"Use the local demo page", "text/plain")
                return
            if self.path not in {"/api/run/math", "/api/run/rebuttal"}:
                self.send(404, b"Not found", "text/plain")
                return
            # No browser-supplied inputs are accepted or interpreted.
            if self.headers.get("Content-Length", "0") != "0" or self.headers.get("Transfer-Encoding"):
                self.send(400, b"Demo actions take no inputs", "text/plain")
                return
            try:
                with tempfile.TemporaryDirectory(prefix="rerun-", dir=runtime) as folder:
                    value = (math_demo if self.path.endswith("/math") else rebuttal_demo)(Path(folder))
                self.send(200, json.dumps(value, ensure_ascii=False).encode(), "application/json; charset=utf-8")
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
                self.send(500, b'{"error":"Offline execution failed. Rerun the CLI demo to inspect the failure."}', "application/json")
    return Handler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ear demo studio", description=__doc__)
    parser.add_argument("--port", type=int, default=8765, help="loopback port; 0 chooses an available port")
    parser.add_argument("--no-open", action="store_true", help="do not open your default browser")
    parser.add_argument("--export", type=Path, metavar="HTML", help="new standalone English project page, reference workflow and recorded offline artifacts")
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    if args.export:
        args.export = args.export.expanduser().resolve()
    if args.export and args.export.exists():
        parser.error("--export already exists; choose a new file (nothing is overwritten)")
    with tempfile.TemporaryDirectory(prefix="ear-studio-") as folder:
        runtime = Path(folder).resolve()
        print("Verifying released evidence and running synthetic offline fixtures…", flush=True)
        data = build_data(runtime)
        if args.export:
            path = args.export.expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(render(data, live=False))
            print(f"Saved portable demo: {path}")
            print("Interactive reference workflow and recorded fixtures; no models called. Open this file directly in a browser.")
            return 0
        with ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(data, runtime)) as server:
            url = f"http://127.0.0.1:{server.server_port}/"
            print(f"EAR Research Studio: {url}", flush=True)
            print("0 model calls. Ctrl-C stops the server and removes temporary fixture workspaces.", flush=True)
            if not args.no_open:
                webbrowser.open(url)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                return 0
    return 0
