"""OpenReview authenticated client pool with token caching + rotation.

Login is rate-limited (few requests / short window) and so are general reads,
so we (a) cache each account's token to disk and reuse it, and (b) rotate across
multiple accounts round-robin, backing off + switching accounts on 429.
"""
import os
import json
import time
import itertools
import openreview

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_env():
    env = {}
    path = os.path.join(ROOT, ".env")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def _accounts(env):
    """Yield (username, password, token_file) for every configured account."""
    pairs = [("OPENREVIEW_USERNAME", "OPENREVIEW_PASSWORD")]
    i = 2
    while f"OPENREVIEW_USERNAME_{i}" in env:
        pairs.append((f"OPENREVIEW_USERNAME_{i}", f"OPENREVIEW_PASSWORD_{i}"))
        i += 1
    out = []
    for idx, (uk, pk) in enumerate(pairs):
        if env.get(uk):
            tokf = os.path.join(ROOT, f".or_token_{idx}.json")
            out.append((env[uk], env[pk], tokf))
    return out


def _login(base, user, pw, tokf):
    if os.path.exists(tokf):
        tok = json.load(open(tokf)).get("token")
        try:
            c = openreview.api.OpenReviewClient(baseurl=base, token=tok)
            c.get_notes(limit=1)
            return c
        except Exception:
            pass
    for _ in range(6):
        try:
            c = openreview.api.OpenReviewClient(baseurl=base)
            r = c.login_user(username=user, password=pw)
            json.dump({"token": r["token"]}, open(tokf, "w"))
            os.chmod(tokf, 0o600)
            return c
        except openreview.openreview.OpenReviewException as e:
            if any(s in str(e) for s in ("429", "RateLimit", "Too many")):
                time.sleep(35)
            else:
                raise
    raise RuntimeError(f"login failed for {user}")


class ClientPool:
    """Round-robin over authenticated clients; retry + rotate on rate limit."""

    def __init__(self, clients, throttle=0.12):
        self.clients = clients
        self.throttle = throttle
        self._rr = itertools.cycle(range(len(clients)))

    def _call(self, method, *a, **k):
        last = None
        for attempt in range(4 * len(self.clients)):
            c = self.clients[next(self._rr)]
            try:
                time.sleep(self.throttle)
                return getattr(c, method)(*a, **k)
            except Exception as e:
                last = e
                if any(s in str(e) for s in ("429", "RateLimit", "Too many")):
                    time.sleep(8)  # brief backoff, then next client
                else:
                    raise
        raise last

    def get_notes(self, *a, **k):
        return self._call("get_notes", *a, **k)

    def get_note_edits(self, *a, **k):
        return self._call("get_note_edits", *a, **k)


def get_pool():
    env = _load_env()
    base = env.get("OPENREVIEW_BASEURL", "https://api2.openreview.net")
    clients = [_login(base, u, p, t) for (u, p, t) in _accounts(env)]
    if not clients:
        raise RuntimeError("no OpenReview accounts configured in .env")
    return ClientPool(clients)
