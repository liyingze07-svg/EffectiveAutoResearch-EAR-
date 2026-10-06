#!/usr/bin/env python3
"""Build the English and Chinese reports from the public source package."""
from pathlib import Path
import argparse
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def build(language):
    source = ROOT / "source" / language
    target = ROOT / "reports" / f"EAR_Technical_Report_{language.upper()}.pdf"
    target.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"ear-{language}-") as work:
        command = [
            "xelatex", "-interaction=nonstopmode", "-halt-on-error",
            "-file-line-error", f"-output-directory={work}", "main.tex",
        ]
        last_output = ""
        for _ in range(3):
            result = subprocess.run(command, cwd=source, capture_output=True, text=True)
            last_output = result.stdout + result.stderr
            if result.returncode:
                raise RuntimeError(f"{language.upper()} compilation failed:\n{last_output[-9000:]}")
        if "Undefined control sequence" in last_output or "There were undefined references" in last_output:
            raise RuntimeError(f"{language.upper()} contains unresolved references")
        shutil.copy2(Path(work) / "main.pdf", target)
    print(target.relative_to(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("language", nargs="?", choices=("en", "cn", "all"), default="all")
    args = parser.parse_args()
    if not shutil.which("xelatex"):
        raise SystemExit("XeLaTeX is required. See README.txt for fonts and TeX packages.")
    for language in (("en", "cn") if args.language == "all" else (args.language,)):
        build(language)


if __name__ == "__main__":
    main()
