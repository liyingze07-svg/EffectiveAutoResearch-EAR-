#!/usr/bin/env python3
"""Text-only OpenAI API calls with JSON conversation files (standard library only)."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".gpt-thread-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="gpt-4o")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--thread", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--phase", default=os.environ.get("PHASE", "unknown"))
    ap.add_argument("--config", default="{}")
    ap.add_argument("--timeout", type=float, default=180)
    args = ap.parse_args()
    if not args.prompt or args.timeout <= 0:
        ap.error("a nonempty prompt and positive timeout are required")
    try:
        config = json.loads(args.config)
        if not isinstance(config, dict):
            raise ValueError("--config must be a JSON object")
        messages = []
        if args.thread and args.thread.exists():
            messages = json.loads(args.thread.read_text(encoding="utf-8"))
        if not isinstance(messages, list) or any(
            not isinstance(m, dict) or "role" not in m or "content" not in m for m in messages
        ):
            raise ValueError("--thread must contain a JSON messages array")
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        key_path = Path.home() / ".openai_key"
        if not key and key_path.is_file():
            key = key_path.read_text(encoding="utf-8").strip()
        if not key:
            raise ValueError("set OPENAI_API_KEY or save it in ~/.openai_key")
    except (OSError, ValueError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    messages.append({"role": "user", "content": args.prompt})
    body = {"model": args.model, "messages": messages, "max_completion_tokens": 16384}
    effort = config.get("model_reasoning_effort")
    if effort and any(m in args.model for m in ("o1", "o3", "o4")):
        body["reasoning_effort"] = effort
    request = Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    started = time.monotonic()
    print("DATA NOTICE: this prompt and conversation history are sent to OpenAI; successful turns are retained in the thread JSON.", file=sys.stderr)
    try:
        with urlopen(request, timeout=args.timeout) as response:
            result = json.load(response)
        content = result["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content:
            raise ValueError("API returned no text")
    except HTTPError as exc:
        print(f"API error: HTTP {exc.code}; thread unchanged", file=sys.stderr)
        return 1
    except (URLError, TimeoutError, OSError, ValueError, KeyError, IndexError, TypeError):
        print("API error: connection failed or invalid response; thread unchanged", file=sys.stderr)
        return 1

    try:
        thread = args.thread
        if thread is None:
            fd, name = tempfile.mkstemp(prefix="gpt_thread_", suffix=".json")
            os.close(fd)
            thread = Path(name)
        atomic_json(thread, messages + [{"role": "assistant", "content": content}])
        if args.output:
            args.output.write_text(content + "\n", encoding="utf-8")
        else:
            print(content)
        if args.thread is None:
            print(f"THREAD_FILE: {thread}", file=sys.stderr)
    except OSError as exc:
        print(f"Output error: {exc}", file=sys.stderr)
        return 1

    usage = result.get("usage") or {}
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "phase": args.phase, "model": args.model,
        "tokens_in": usage.get("prompt_tokens"), "tokens_out": usage.get("completion_tokens"),
        "tokens_total": usage.get("total_tokens"),
        "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens"),
        "wall_clock_s": int(time.monotonic() - started), "source": "gpt_call.sh",
    }
    try:
        log = Path(os.environ.get("COST_LOG", "outputs/COST_LOG.jsonl"))
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        print("Warning: response saved, but cost log could not be written", file=sys.stderr)
    return 0


if __name__ == "__main__":
    os.umask(0o077)
    raise SystemExit(main())
