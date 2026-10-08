#!/usr/bin/env python3
"""Compile the EAR v10 Chinese report with the local XeLaTeX toolchain."""
from pathlib import Path
import argparse
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "reports/EAR_Technical_Report_CN.pdf")
    parser.add_argument("--log", type=Path, help="Save the final compiler log for inspection")
    args = parser.parse_args()
    if not shutil.which("xelatex"):
        raise SystemExit("XeLaTeX is required (TeX Live / MacTeX).")
    target = args.output.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ear-v10-cn-") as work:
        command = ["xelatex", "-interaction=nonstopmode", "-halt-on-error",
                   "-file-line-error", f"-output-directory={work}", "main.tex"]
        for _ in range(3):
            result = subprocess.run(command, cwd=ROOT / "source/cn", capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError("Compilation failed:\n" + (result.stdout + result.stderr)[-11000:])
        log = (Path(work) / "main.log").read_text(encoding="utf-8", errors="replace")
        if "There were undefined references" in log or "Undefined control sequence" in log:
            raise RuntimeError("Unresolved references or commands in final pass")
        if args.log:
            args.log.parent.mkdir(parents=True, exist_ok=True)
            args.log.write_text(log, encoding="utf-8")
        shutil.copy2(Path(work) / "main.pdf", target)
    print(target)
    for line in log.splitlines():
        if line.startswith("EAR CJK") or "Overfull" in line or "Underfull" in line:
            print(line)


if __name__ == "__main__":
    main()
