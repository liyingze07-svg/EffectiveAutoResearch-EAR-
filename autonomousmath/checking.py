"""Optional final checking after terminal review; Lean is not a research-loop dependency."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import subprocess

from .referee import content_hash
from .engine.state import terminate_tree


def final_check(campaign_dir: Path, config: dict, report_dir: Path) -> dict:
    """Invoke an explicitly configured checker with an argv list, never a shell string.

An external autoformalizer can implement this contract using LeanSearch-v2.
It receives the accepted source version and must report which claims it covers.
Absence of a checker means deferred formalization, never a verification pass.
"""
    command = config.get("final_check_command")
    report = Path(report_dir)
    report.mkdir(parents=True, exist_ok=True)
    result = {"status": "deferred", "coverage": [], "paper_content_hash": content_hash(Path(campaign_dir)),
              "reason": "No final checker configured; the proof remains informal."}
    if command:
        if not isinstance(command, list) or any(not isinstance(x, str) for x in command):
            raise ValueError("final_check_command must be an argv list")
        manifest = report / "request.json"
        manifest.write_text(json.dumps({"campaign_dir": str(Path(campaign_dir).resolve()),
                                       "paper_content_hash": result["paper_content_hash"],
                                       "output_file": str((report / "checker.json").resolve())}, indent=2))
        argv = [arg.replace("{request}", str(manifest.resolve())) for arg in command]
        proc = None
        try:
            proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                    cwd=campaign_dir)
            proc.communicate(timeout=float(config.get("final_check_timeout_sec", 600)))
            output = report / "checker.json"
            if proc.returncode or not output.is_file():
                raise ValueError("checker did not produce a result")
            checked = json.loads(output.read_text())
            if checked.get("paper_content_hash") != result["paper_content_hash"]:
                raise ValueError("checker result does not bind to the accepted paper version")
            if checked.get("status") not in {"verified", "partial", "failed", "blocked"} or not isinstance(checked.get("coverage"), list):
                raise ValueError("checker status and explicit claim coverage are required")
            if content_hash(Path(campaign_dir)) != result["paper_content_hash"]:
                raise ValueError("paper changed while final checking ran")
            result = checked
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            if proc is not None and proc.poll() is None:
                terminate_tree(proc)
            result.update(status="blocked", reason=str(exc))
        except BaseException:
            if proc is not None:
                terminate_tree(proc)
            raise
    (report / "final_check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


async def leansearch_check(code: Path, project: Path, timeout: int = 600) -> dict:
    """Check an already formalized Lean file through the upstream verifier.

This verifies the supplied Lean statement. Translating and matching informal
paper claims is the separate autoformalizer's responsibility.
"""
    try:
        from leansearchv2.prove.verifier import LeanInteractVerifier
    except ImportError:
        return {"status": "blocked", "reason": "Install LeanSearch-v2's [lean] extra and a Lean/Mathlib project first."}
    verifier = LeanInteractVerifier(project_dir=str(project.resolve()))
    try:
        text = code.read_text(encoding="utf-8")
        result = await verifier.verify(text, timeout_s=timeout)
        return {"status": "verified" if result.success else "failed", "has_sorry": result.has_sorry,
                "error": result.error_msg, "scope": "supplied Lean file only",
                "lean_code_hash": hashlib.sha256(text.encode()).hexdigest()}
    except (OSError, RuntimeError, asyncio.TimeoutError) as exc:
        return {"status": "blocked", "reason": str(exc), "scope": "supplied Lean file only"}
    finally:
        await verifier.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", required=True, type=Path)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    result = asyncio.run(leansearch_check(args.code, args.project, args.timeout))
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "verified" else 2


if __name__ == "__main__":
    raise SystemExit(main())
