"""CLI adapters; the research model owns tools and the complete scientific loop."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import shutil
import subprocess
import time

from .config import EngineConfig
from .state import atomic_json, terminate_tree


@dataclass
class CallResult:
    returncode: int
    text: str = ""
    session_id: str | None = None
    error_kind: str | None = None
    duration_sec: float = 0.0

    def as_dict(self) -> dict:
        return asdict(self)


def classify_error(text: str, returncode: int) -> str | None:
    if returncode == 0:
        return None
    low = text.lower()
    if any(word in low for word in ("rate limit", "usage limit", "quota", "insufficient_quota", "credits", "limit reached")):
        return "quota"
    if any(word in low for word in ("unauthorized", "authentication", "not logged in", "invalid api key", "login required")):
        return "authentication"
    return "infrastructure"


class CLIProvider:
    def __init__(self, config: EngineConfig):
        self.config = config

    def command(self, campaign_dir: Path, session_id: str | None = None) -> list[str]:
        c = self.config
        if c.backend == "codex":
            args = [c.codex_command, "exec"]
            if session_id:
                args += ["resume", "--skip-git-repo-check", "--json",
                         "-c", f'sandbox_mode="{c.sandbox}"']
            else:
                args += ["--skip-git-repo-check", "--color", "never", "--json", "-s", c.sandbox]
            args += ["-c", 'approval_policy="never"', "-c",
                     f"sandbox_workspace_write.network_access={'true' if c.network_access else 'false'}"]
            if c.model:
                args += ["--model", c.model]
            if c.effort:
                args += ["-c", f'model_reasoning_effort="{c.effort}"']
            args += ["--output-last-message", str(campaign_dir / "LAST_MESSAGE.md")]
            args += [session_id, "-"] if session_id else ["-"]
            return args
        args = [c.claude_command, "--print", "--output-format", "json",
                "--permission-mode", "acceptEdits", "--permission-prompts", "none",
                "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep,WebSearch,WebFetch,Agent,Skill"]
        if c.model:
            args += ["--model", c.model]
        if c.effort:
            args += ["--effort", c.effort]
        if session_id:
            args += ["--resume", session_id]
        return args

    def run(self, prompt: str, campaign_dir: Path, session_id: str | None = None) -> CallResult:
        start = time.monotonic()
        args = self.command(campaign_dir, session_id)
        if not shutil.which(args[0]):
            return CallResult(127, error_kind="missing_cli")
        process = None
        try:
            process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True, cwd=campaign_dir)
            stdout, stderr = process.communicate(prompt, timeout=self.config.timeout_sec)
        except subprocess.TimeoutExpired:
            if process is not None:
                terminate_tree(process)
                process.communicate()
            return CallResult(124, session_id=session_id, error_kind="timeout",
                              duration_sec=time.monotonic() - start)
        except OSError:
            return CallResult(127, session_id=session_id, error_kind="infrastructure")
        except BaseException:
            if process is not None:
                terminate_tree(process)
            raise
        sid = session_id
        text = ""
        model_error = False
        events = []
        try:
            envelope = json.loads(stdout)
            if isinstance(envelope, dict):
                events.append(envelope)
        except ValueError:
            pass
        for line in stdout.splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict):
                events.append(event)
        for event in events:
            if event.get("type") == "thread.started":
                sid = event.get("thread_id") or sid
            sid = event.get("session_id") or sid
            if event.get("type") == "result":
                text = event.get("result") or ""
                model_error = bool(event.get("is_error"))
            if event.get("type") in ("error", "turn.failed"):
                model_error = True
        last = campaign_dir / "LAST_MESSAGE.md"
        if last.exists():
            text = last.read_text(encoding="utf-8", errors="replace")
        returncode = process.returncode or (1 if model_error else 0)
        # Do not persist raw tool traces, environment values, or credential-bearing stderr.
        kind = classify_error(stderr + "\n" + stdout, returncode)
        return CallResult(returncode, text, sid, kind, time.monotonic() - start)


def _fixture_pdf(path: Path, message: str) -> None:
    """A valid small PDF without a TeX dependency, clearly labelled as a fixture."""
    content = f"BT /F1 12 Tf 36 720 Td ({message}) Tj ET".encode("ascii")
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>",
               b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
               b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream"]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{i} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    path.write_bytes(pdf)


class OfflineProvider:
    """Exercise the real artifact and review loop; never claim a scientific result."""
    def __init__(self, config: EngineConfig):
        self.config = config

    def run(self, prompt: str, campaign_dir: Path, session_id: str | None = None) -> CallResult:
        paper = campaign_dir / "paper"
        paper.mkdir(parents=True, exist_ok=True)
        refined = (campaign_dir / "REVIEW_FEEDBACK.md").exists()
        revision = 2 if refined else 1
        proof = ("OFFLINE FIXTURE — not a research result.\n\n"
                 + ("Claim: for every real x, x squared is nonnegative.\nProof: a square is the product of two equal-sign factors; x=0 is included.\n"
                    if refined else "Claim: x squared is positive for every real x.\nProof attempt: unresolved x=0 boundary case.\n"))
        (campaign_dir / "proof.md").write_text(proof, encoding="utf-8")
        tex = ("\\documentclass{article}\n\\begin{document}\n"
               "\\section*{Offline AutonomousMath demonstration}\n"
               f"Fixture revision {revision}. This is a simulated artifact, not a research result.\n"
               + ("For every real $x$, $x^2\\geq0$, including $x=0$.\n" if refined else "For every real $x$, $x^2>0$. Boundary case unresolved.\n")
               + "\\end{document}\n")
        (paper / "main.tex").write_text(tex, encoding="utf-8")
        _fixture_pdf(paper / "main.pdf", f"OFFLINE FIXTURE - revision {revision} - not a research result")
        atomic_json(campaign_dir / "CANDIDATE.json", {"state": "draft_ready", "offline": True, "revision": revision})
        return CallResult(0, f"Offline fixture revision {revision} submitted.", "offline-session")
