#!/usr/bin/env python3
"""board-submit — 往游击战成果看板(9312)提交：新猜想 / 某靶结果 / 认领某靶。

人和 agent 都能用。零依赖（stdlib urllib）。默认打本机 127.0.0.1:9312。

用法：
  python3 submit_client.py claim      --slug <slug> --by <id> [--body "打算怎么打"]
  python3 submit_client.py result     --slug <slug> --by <id> [--url <链接>] [--body "结果摘要"]
  python3 submit_client.py conjecture --title "<一句话>" --by <id> [--url <链接>] [--statement "精确陈述"]
  # 通用可选： --host <h> --port <p>
退出码 0=成功。成功打印 {"ok":true,"id":...}。
"""
import argparse
import json
import sys
import urllib.request


def main():
    ap = argparse.ArgumentParser(description="submit to the guerrilla board")
    ap.add_argument("type", choices=["claim", "result", "conjecture"])
    ap.add_argument("--slug")
    ap.add_argument("--title")
    ap.add_argument("--oneLiner")
    ap.add_argument("--statement")
    ap.add_argument("--url")
    ap.add_argument("--body")
    ap.add_argument("--by", default="agent")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", default="9312")
    a = ap.parse_args()

    if a.type in ("claim", "result") and not a.slug:
        ap.error("--slug required for %s" % a.type)
    if a.type == "conjecture" and not a.title:
        ap.error("--title required for conjecture")

    payload = {"type": a.type}
    for k in ("slug", "title", "oneLiner", "statement", "url", "body", "by"):
        v = getattr(a, k)
        if v:
            payload[k] = v

    endpoint = "http://%s:%s/api/submit" % (a.host, a.port)
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        endpoint, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            out = resp.read().decode("utf-8")
            print(out)
            return 0
    except urllib.error.HTTPError as e:
        sys.stderr.write("HTTP %s: %s\n" % (e.code, e.read().decode("utf-8", "replace")[:300]))
        return 1
    except Exception as e:
        sys.stderr.write("submit failed: %s (看板没起？ curl http://%s:%s/healthz)\n" % (e, a.host, a.port))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
