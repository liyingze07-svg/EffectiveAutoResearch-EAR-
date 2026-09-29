"""Rebuttal-quality verifier — DeepSeek V4 Pro reviewer simulator.

Given a review + author rebuttal (+ optional reviewer profile), predict how the
reviewer would revise their score: raise / same / lower. `raise` == the rebuttal
is strong enough to earn a score increase (high quality).

Usage
-----
Single case (JSON file or inline):
    python verify_rebuttal.py --case examples/example_case.json
    python verify_rebuttal.py --review "..." --rebuttal "..." --initial-rating 5

Batch (JSONL in -> JSONL out; one case per line):
    python verify_rebuttal.py --batch cases.jsonl --out preds.jsonl --workers 8

Importable:
    from verify_rebuttal import verify_one
    verify_one({"review": "...", "rebuttal": "...", "initial_rating": 5})
    # -> {"reaction": "raise", "reasoning": "...", "quality": "high"}

Config (env or a .env next to this file): DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
(default https://api.deepseek.com), DEEPSEEK_MODEL (default deepseek-v4-pro).
Only dependency: `openai` (the DeepSeek endpoint is OpenAI-compatible).
"""
import os
import re
import json
import importlib
import argparse
from concurrent.futures import ThreadPoolExecutor

from prompt_template import build_messages as default_build_messages

HERE = os.path.dirname(os.path.abspath(__file__))


def build_messages_auto(case):
    """Route by the reviewer's overall assessment: a borderline 3 goes to the OA=3
    raise-potential diagnoser; every other score uses the general EMNLP (v2) prompt."""
    import prompt_template_emnlp
    import prompt_template_emnlp_oa3
    if case.get("initial_overall") == 3:
        return prompt_template_emnlp_oa3.build_messages(case)
    return prompt_template_emnlp.build_messages(case)
QUALITY = {"raise": "high", "same": "neutral", "lower": "counterproductive"}


def _load_env():
    env = dict(os.environ)
    path = os.path.join(HERE, ".env")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip())
    return env


def _client_and_model():
    return get_backend("deepseek-v4-pro")


# --- multi-backend registry: routes different reviewer scores to different models ---
# OA=3 -> GPT-5.5 (best rebuttal-quality discrimination); everything else -> deepseek-v4-pro.
MODEL_BACKENDS = {
    "deepseek-v4-pro":   dict(provider="deepseek", model="deepseek-v4-pro"),
    "deepseek-v4-flash": dict(provider="deepseek", model="deepseek-v4-flash"),
    "gpt-5.5":           dict(provider="openai",   model="gpt-5.5"),
}
_PROVIDER = {
    "deepseek": dict(key="DEEPSEEK_API_KEY", base="https://api.deepseek.com", base_env="DEEPSEEK_BASE_URL"),
    "openai":   dict(key="OPENAI_API_KEY",   base="https://api.openai.com/v1", base_env="OPENAI_BASE_URL"),
}
_CLIENTS = {}


def get_backend(model_key):
    """Return (client, model_id) for a registry key; caches clients. Raises if the
    provider's API key is absent (caller can fall back)."""
    if model_key in _CLIENTS:
        return _CLIENTS[model_key]
    from openai import OpenAI
    env = _load_env()
    spec = MODEL_BACKENDS[model_key]
    prov = _PROVIDER[spec["provider"]]
    key = env.get(prov["key"])
    if not key:
        raise RuntimeError(f"missing {prov['key']} for model '{model_key}'")
    client = OpenAI(api_key=key, base_url=env.get(prov["base_env"], prov["base"]))
    _CLIENTS[model_key] = (client, spec["model"])
    return _CLIENTS[model_key]


def route(case):
    """Score-based routing -> (build_messages_fn, model_key). OA=3 uses the diagnoser
    on GPT-5.5; other EMNLP scores use v2 on deepseek-v4-pro. Falls back to
    deepseek-v4-pro if the OpenAI key is missing."""
    import prompt_template_emnlp
    import prompt_template_emnlp_oa3
    if case.get("initial_overall") == 3:
        try:
            get_backend("gpt-5.5")
            return prompt_template_emnlp_oa3.build_messages, "gpt-5.5"
        except RuntimeError:
            return prompt_template_emnlp_oa3.build_messages, "deepseek-v4-pro"
    return prompt_template_emnlp.build_messages, "deepseek-v4-pro"


def _parse(text):
    """Extract {reasoning, reaction} from the model's reply, robustly."""
    try:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            d = json.loads(m.group(0))
            r = str(d.get("reaction", "")).strip().lower()
            if r in QUALITY:
                return r, d.get("reasoning", "")
    except Exception:
        pass
    # fallback: last mention of a label word
    found = re.findall(r"\b(raise|same|lower)\b", text.lower())
    r = found[-1] if found else "same"
    return r, text.strip()[:500]


_EXTRA_FIELDS = ("blocker", "veto", "raise_potential", "advice")


def verify_one(case, client=None, model=None, max_tokens=2048, build_messages=None):
    """Return {reaction, reasoning, quality, ...} — plus any diagnostic fields the
    template emits (blocker / veto / raise_potential / advice for the OA=3 diagnoser)."""
    build_messages = build_messages or default_build_messages
    if client is None:
        client, model = _client_and_model()
    resp = client.chat.completions.create(
        model=model,
        messages=build_messages(case),
        temperature=0.0,
        max_tokens=max_tokens,
    )
    text = resp.choices[0].message.content or ""
    reaction, reasoning = _parse(text)
    out = {"reaction": reaction, "reasoning": reasoning, "quality": QUALITY[reaction]}
    try:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            d = json.loads(m.group(0))
            for k in _EXTRA_FIELDS:
                if k in d:
                    out[k] = d[k]
    except Exception:
        pass
    return out


def verify_batch_routed(cases, workers=8):
    """Per-case model+prompt routing (OA=3 -> GPT-5.5, else -> deepseek-v4-pro)."""
    def one(c):
        build_fn, model_key = route(c)
        try:
            client, model = get_backend(model_key)
            out = verify_one(c, client=client, model=model, build_messages=build_fn)
        except Exception as e:
            out = {"reaction": "same", "reasoning": f"ERROR: {e}", "quality": "neutral"}
        out["model_used"] = model_key
        return {**{k: c[k] for k in ("note_id", "paper_id") if k in c}, **out}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(one, cases))


def verify_batch(cases, workers=8, build_messages=None):
    client, model = _client_and_model()

    def one(c):
        try:
            out = verify_one(c, client=client, model=model, build_messages=build_messages)
        except Exception as e:
            out = {"reaction": "same", "reasoning": f"ERROR: {e}", "quality": "neutral"}
        return {**{k: c[k] for k in ("note_id", "paper_id") if k in c}, **out}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(one, cases))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", help="path to a single-case JSON file")
    ap.add_argument("--review")
    ap.add_argument("--rebuttal")
    ap.add_argument("--initial-rating", type=int)
    ap.add_argument("--batch", help="JSONL of cases, one per line")
    ap.add_argument("--out", help="JSONL predictions output (batch mode)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--template", default="prompt_template",
                    help="template module: prompt_template (ICLR), prompt_template_emnlp, "
                         "prompt_template_emnlp_oa3, or 'auto' (route emnlp by OA=3)")
    args = ap.parse_args()

    routed = args.template == "route"
    build_fn = (build_messages_auto if args.template == "auto"
                else None if routed
                else importlib.import_module(args.template).build_messages)

    if args.batch:
        cases = [json.loads(l) for l in open(args.batch) if l.strip()]
        preds = (verify_batch_routed(cases, workers=args.workers) if routed
                 else verify_batch(cases, workers=args.workers, build_messages=build_fn))
        out = args.out or (args.batch + ".preds.jsonl")
        with open(out, "w") as f:
            for p in preds:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")
        from collections import Counter
        print("wrote", len(preds), "->", out,
              "| dist:", dict(Counter(p["reaction"] for p in preds)))
        return

    if args.case:
        case = json.load(open(args.case))
    else:
        case = {"review": args.review or "", "rebuttal": args.rebuttal or ""}
        if args.initial_rating is not None:
            case["initial_rating"] = args.initial_rating
    print(json.dumps(verify_one(case, build_messages=build_fn), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
