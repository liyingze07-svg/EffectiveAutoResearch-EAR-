#!/usr/bin/env python3
"""Read-only local prerequisites check. No model calls or credential values printed."""
import argparse
import importlib.util
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true", help="check only the zero-cost demo prerequisites")
    ap.add_argument("--component", choices=("all", "autovibeidea", "autonomousmath", "rebuttal"), default="all")
    ap.add_argument("--backend", choices=("codex", "claude"), default="codex",
                    help="AutonomousMath coordinator backend")
    args = ap.parse_args()
    failures = []

    def check(ok, label, hint=""):
        print(f"{'OK' if ok else 'MISSING'}: {label}" + (f" — {hint}" if not ok and hint else ""))
        if not ok:
            failures.append(label)

    check(sys.version_info >= (3, 10), "Python 3.10+")
    check((ROOT / "rebuttal/harness/templates/CLAUDE.tmpl.md").is_file(), "complete EAR checkout")
    if args.offline:
        print("Offline demo: standard library only; no CLI login or API key needed.")
        return int(bool(failures))

    check(platform.system() == "Linux", "supported shell environment: Linux / WSL2",
          "other systems are not validated; use Linux or run the Python-only offline demo")
    driver = args.backend if args.component == "autonomousmath" else "codex"
    binary = shutil.which(driver) or shutil.which(driver + ".exe")
    check(bool(binary), f"{driver.title()} CLI", f"install and authenticate {driver}")
    if binary:
        try:
            result = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=10)
            check(result.returncode == 0, f"{driver.title()} executable starts")
            if result.returncode == 0:
                print(f"CLI: {result.stdout.strip()}")
        except (OSError, subprocess.TimeoutExpired):
            check(False, f"{driver.title()} executable starts")
    if args.component in ("all", "autonomousmath"):
        for command in ("pdflatex", "bibtex", "pdfinfo", "pdftotext"):
            check(bool(shutil.which(command)), f"autonomousmath: {command}")
        if args.backend == "claude":
            check(bool(shutil.which("claude")), "autonomousmath: Claude CLI")
            check(bool(shutil.which("codex")), "autonomousmath: Codex terminal reviewer")
    if args.component in ("all", "autovibeidea"):
        for command in ("bash", "flock", "nohup", "tee"):
            check(bool(shutil.which(command)), f"autovibeidea: {command}")
        handles = hasattr(os, "pidfd_open") and hasattr(signal, "pidfd_send_signal")
        if handles:
            try:
                fd = os.pidfd_open(os.getpid())
                os.close(fd)
            except OSError:
                handles = False
        check(handles, "autovibeidea: identity-safe background process control",
              "Linux/WSL2 with pidfd support (Linux 5.3+) is required for background mode")
        print("autovibeidea: --gpt-only still requires Codex; API calls also need OPENAI_API_KEY.")
    if args.component in ("all", "rebuttal"):
        check(importlib.util.find_spec("openai") is not None, "rebuttal: openai SDK",
              "python3 -m pip install -r rebuttal/requirements.txt")
        key_present = bool(os.environ.get("DEEPSEEK_API_KEY"))
        env_path = ROOT / "rebuttal/rebuttal_verifier/.env"
        if env_path.is_file():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("DEEPSEEK_API_KEY="):
                    value = line.split("=", 1)[1].strip()
                    key_present |= bool(value) and not any(s in value.lower() for s in ("xxxxx", "your", "placeholder"))
        check(key_present, "rebuttal: DeepSeek key configured",
              "set DEEPSEEK_API_KEY; single-family fallback must be explicitly chosen at runtime")
    print("No authentication, model availability or network requests were tested.")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
