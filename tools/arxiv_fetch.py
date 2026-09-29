#!/usr/bin/env python3
"""CLI helper for searching and downloading arXiv papers.

Used by the ``arxiv`` skill (skills/arxiv/SKILL.md).

Commands
--------
search    Search arXiv and print results as JSON.
download  Download a paper PDF by arXiv ID.

Examples
--------
python3 tools/arxiv_fetch.py search "attention mechanism" --max 10
python3 tools/arxiv_fetch.py search "id:2301.07041" --max 1
python3 tools/arxiv_fetch.py download 2301.07041 --dir papers
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

_ATOM_NS = "http://www.w3.org/2005/Atom"
_API_BASE = "https://export.arxiv.org/api/query"
_USER_AGENT = "EAR-arxiv/1.0 (arXiv API client; contact via repository issues)"
_MAX_RETRIES = 3
_BACKOFF_BASE = 10.0  # 秒；arXiv 建议请求间隔 >= 3s，实测被节流后需更长
_MIN_PDF_BYTES = 10_240
_NEW_STYLE_ID_RE = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")
_OLD_STYLE_ID_RE = re.compile(r"^[A-Za-z.-]+/\d{7}(v\d+)?$")


def _normalize_id(arxiv_id: str) -> str:
    """Strip URL/version noise and return a clean arXiv ID."""
    value = arxiv_id.strip()
    if "/abs/" in value:
        value = value.split("/abs/", 1)[1]
    if value.startswith("id:"):
        value = value[3:]
    if "v" in value.split(".")[-1]:
        value = value.rsplit("v", 1)[0]
    return value


def _looks_like_arxiv_id(value: str) -> bool:
    """Return True when the input resembles a modern or legacy arXiv ID."""
    value = value.strip()
    return bool(_NEW_STYLE_ID_RE.match(value) or _OLD_STYLE_ID_RE.match(value))


def _api_url(query: str, max_results: int, start: int) -> str:
    """Build the arXiv API URL for a search query or specific ID lookup."""
    query = query.strip()
    if query.startswith("id:"):
        params = {"id_list": _normalize_id(query)}
    elif _looks_like_arxiv_id(query):
        params = {"id_list": _normalize_id(query)}
    else:
        params = {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
    return f"{_API_BASE}?{urllib.parse.urlencode(params)}"


class ArxivFetchError(RuntimeError):
    """Raised when arXiv cannot be reached after retries."""


def _fetch_atom(url: str) -> ET.Element:
    """Fetch an arXiv Atom feed, retrying on throttling, and return the parsed root.

    arXiv 用 406 / 429 / 5xx 而非标准 rate-limit 头来节流，因此三者都视为可重试。

    实测注意：某些网络环境下 arXiv 会对**新查询**持续返回 406（同一 IP 下已成功过的
    URL 仍可返回 200），此时重试在数分钟内不会恢复。因此重试只是廉价的一次挽救，
    **不是可靠路径**——调用方必须准备好回退到 WebSearch。
    """
    headers = {"User-Agent": _USER_AGENT, "Accept": "application/atom+xml, application/xml, */*"}
    last = ""
    for attempt in range(1, _MAX_RETRIES + 1):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return ET.fromstring(resp.read())
        except urllib.error.HTTPError as exc:
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            last = f"HTTP {exc.code} {exc.reason}"
            retryable = exc.code in (406, 408, 429) or exc.code >= 500
        except urllib.error.URLError as exc:
            last = f"network error: {exc.reason}"
            retry_after, retryable = None, True
        except ET.ParseError as exc:
            last = f"malformed Atom response: {exc}"
            retry_after, retryable = None, True
        if not retryable or attempt == _MAX_RETRIES:
            break
        delay = float(retry_after) if (retry_after or "").isdigit() else _BACKOFF_BASE * (2 ** (attempt - 1))
        print(
            f"[arxiv_fetch] {last} — 第 {attempt}/{_MAX_RETRIES} 次尝试失败，{delay:.0f}s 后重试",
            file=sys.stderr,
        )
        time.sleep(delay)
    raise ArxivFetchError(
        f"arXiv 检索失败（{last}），已重试 {_MAX_RETRIES} 次。\n"
        "406/429 是 arXiv 的节流响应。注意：在部分网络环境下它会对新查询持续返回 406，"
        "等待数分钟也不会恢复，因此不要在此反复重试。\n"
        "→ 改用 WebSearch / 公开网页作为本轮检索来源，并把这次降级记入 "
        "outputs/PIPELINE_LOG.md。不要因此中止 pipeline。"
    )


def _parse_entry(entry: ET.Element) -> dict:
    """Extract structured fields from a single Atom <entry> element."""
    raw_id = entry.findtext(f"{{{_ATOM_NS}}}id", "")
    arxiv_id = _normalize_id(raw_id)
    title = (entry.findtext(f"{{{_ATOM_NS}}}title", "") or "").strip().replace("\n", " ")
    abstract = (entry.findtext(f"{{{_ATOM_NS}}}summary", "") or "").strip().replace("\n", " ")
    published = (entry.findtext(f"{{{_ATOM_NS}}}published", "") or "")[:10]
    updated = (entry.findtext(f"{{{_ATOM_NS}}}updated", "") or "")[:10]
    authors = [
        author.findtext(f"{{{_ATOM_NS}}}name", "")
        for author in entry.findall(f"{{{_ATOM_NS}}}author")
    ]
    categories = [
        category.get("term", "")
        for category in entry.findall(f"{{{_ATOM_NS}}}category")
        if category.get("term")
    ]
    return {
        "id": arxiv_id,
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "published": published,
        "updated": updated,
        "categories": categories,
        "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
        "abs_url": f"https://arxiv.org/abs/{arxiv_id}",
    }


def search(query: str, max_results: int = 10, start: int = 0) -> list[dict]:
    """Search arXiv and return a list of paper dictionaries."""
    url = _api_url(query, max_results=max_results, start=start)
    root = _fetch_atom(url)
    return [_parse_entry(entry) for entry in root.findall(f"{{{_ATOM_NS}}}entry")]


def download(arxiv_id: str, output_dir: str = "papers") -> dict:
    """Download a paper PDF and return metadata about the saved file."""
    clean_id = _normalize_id(arxiv_id)
    safe_id = clean_id.replace("/", "_")

    dest_dir = Path(output_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{safe_id}.pdf"

    if dest.exists():
        return {
            "id": clean_id,
            "path": str(dest),
            "size_kb": dest.stat().st_size // 1024,
            "skipped": True,
        }

    pdf_url = f"https://arxiv.org/pdf/{clean_id}.pdf"
    req = urllib.request.Request(pdf_url, headers={"User-Agent": _USER_AGENT})

    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt == 1:
                time.sleep(5)
                continue
            raise
    else:
        raise RuntimeError(f"Failed to download {pdf_url} after retries")

    if len(data) < _MIN_PDF_BYTES:
        raise ValueError(
            f"Downloaded file is only {len(data)} bytes - likely an error page, not a PDF"
        )

    dest.write_bytes(data)
    return {
        "id": clean_id,
        "path": str(dest),
        "size_kb": len(data) // 1024,
        "skipped": False,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search and download arXiv papers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Search arXiv papers")
    search_parser.add_argument(
        "query",
        help="Search query or arXiv ID (bare ID or id:ARXIV_ID).",
    )
    search_parser.add_argument(
        "--max",
        type=int,
        default=10,
        metavar="N",
        help="Maximum number of results (default: 10).",
    )
    search_parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Start offset for pagination (default: 0).",
    )

    download_parser = subparsers.add_parser("download", help="Download a paper PDF by arXiv ID")
    download_parser.add_argument(
        "id",
        help="arXiv paper ID, e.g. 2301.07041 or cs/0601001",
    )
    download_parser.add_argument(
        "--dir",
        default="papers",
        metavar="DIR",
        help="Output directory (default: papers).",
    )
    download_parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds to sleep after download (default: 1.0).",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command == "search":
        results = search(args.query, max_results=args.max, start=args.start)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    if args.command == "download":
        result = download(args.id, output_dir=args.dir)
        if result.get("skipped"):
            print(json.dumps({**result, "message": "already exists, skipped"}, ensure_ascii=False))
        else:
            time.sleep(args.delay)
            print(json.dumps(result, ensure_ascii=False))
        return 0

    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ArxivFetchError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        sys.exit(130)
