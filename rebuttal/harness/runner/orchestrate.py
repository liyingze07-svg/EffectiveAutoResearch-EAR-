#!/usr/bin/env python3
"""Thin orchestrator for the AutoRebuttal harness (v0.2).

Claude Code CODED this driver; Codex is the EXECUTION ENGINE. Each stage runs in a
FRESH `codex exec` subprocess (new context — no single long context, no rot, no
laziness). The driver is deterministic: it fills the materialized stage prompt
(harness/stages/*.md), dispatches to Codex, verifies the receipt + declared output,
and runs the goal loop per GOAL.md / LOOP.md. All state lives on disk.

Engine primitive (verified): codex exec -s <sandbox> -C <cwd> -c model_reasoning_effort=<eff>
   --skip-git-repo-check -o <receipt> -   (prompt on stdin) -> final message in <receipt>.

Usage:
  orchestrate.py --paper 01-wdData [--from r0a] [--dry-run]
  orchestrate.py --all
Run it in the BACKGROUND (nohup/setsid) so it is not tied to any chat context.
"""
import os, sys, re, json, argparse, subprocess, time, hashlib

# Portable: by default, derive the repository root from this file's location (harness/runner/ → ../../),
# with AUTOREBUTTAL_ROOT available as an override. Previously this was a hard-coded absolute path, which prevented publication and deployment on another machine.
ROOT = os.environ.get("AUTOREBUTTAL_ROOT") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
HARNESS = os.path.join(ROOT, "harness")
STAGES = os.path.join(HARNESS, "stages")
for p in (os.path.join(HARNESS, "runner"), os.path.join(ROOT, "rebuttal_verifier")):
    if p not in sys.path:
        sys.path.insert(0, p)

# #27: load the FROZEN gate from its pinned path (not by ambiguous module-name precedence),
# register it as sys.modules['consensus_gate'] so coach_loop/moe_loop reuse the SAME instance,
# and record its content hash so a run manifest can prove which gate judged it.
import importlib.util  # noqa: E402
_CG_PATH = os.path.join(ROOT, "rebuttal_verifier", "consensus_gate.py")
GATE_SHA = hashlib.sha256(open(_CG_PATH, "rb").read()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location("consensus_gate", _CG_PATH)
cg = importlib.util.module_from_spec(_spec)
sys.modules["consensus_gate"] = cg
_spec.loader.exec_module(cg)
from coach_loop import ammo_hits     # noqa: E402  (imports the same frozen consensus_gate)
from moe_loop import load_strategies  # noqa: E402  (reads strategies/MANIFEST.json)
import cost                             # noqa: E402  M1 cost meter (independent module; never modify the frozen package)
_COST_PROBE = cost.install_deepseek_probe()   # Intercept DeepSeek token at the client factory; silently degrade on failure


MAX_ITER_OVERRIDE = None  # --max-iter: temporarily reduce goal-loop iterations (to save quota), without changing REBUTTAL_CARD.json
B3_REPEATS = 3           # --b3-repeats: number of consecutive B3 runs; take the **union** of hits. See the empirical basis in ammo_gate.
FANOUT_ALL = False       # --fanout-all: restore the old behavior of "writing all N strategies every round" (use only for strategy-comparison evaluations).
                         # The default is a strategy-level lazy ladder; see the cost basis in reviewer_loop.
NO_DEEPSEEK = False      # --no-deepseek: single-family degraded mode. Fallback when DeepSeek is unavailable (balance/network).
                         # ⚠ This **drops GOAL.md inviolable rule #4 (cross-family consensus gate)** — only the OpenAI family remains,
                         # the judge and writer are in the same family, and the core anti-Goodhart safeguard fails. H1 is still preserved (judge model ≠ writer model).
                         # Therefore, in this mode: ① mark every gate record with cross_family=false + degraded
                         # ② the loop status is PASS_SINGLE_FAMILY, not PASS — never let degraded output be mistaken for a genuine ACQUIT.
MODEL = None            # WRITER engine model override (--model); None = codex config default
JUDGE_MODEL = "gpt-5.6-sol"  # authoritative Codex JUDGE model -- MUST differ from writer MODEL
                             # so family-B independence survives (anti-Goodhart; H1). --judge-model overrides.
WRITE_EFFORT = "high"   # r6_write reasoning
JUDGE_EFFORT = "xhigh"  # r7 gate reasoning (README-validated best for OA=3 judge)


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---- Codex engine primitive -------------------------------------------------

def codex_exec(prompt, cwd=ROOT, sandbox="workspace-write", effort="medium", timeout=1800, model=None,
               stage=None, slug=None, unit=None, role="DRIVE", strategy=None):
    """Run one stage in a FRESH codex context. Returns the final message (receipt).

    M1: `--json` makes codex emit events as JSONL to stdout (previously DEVNULL, so token was discarded),
    and records token from turn.completed.usage in the cost ledger. `-o <rc>` remains the sole receipt source,
    so adding --json does not change return-value semantics (empirically verified). stage/slug/unit/role are used only for accounting."""
    rc = f"/tmp/codex_receipt_{os.getpid()}_{int(time.time()*1000)%100000}.txt"
    cmd = ["codex", "exec", "-s", sandbox, "-C", cwd,
           "-c", f"model_reasoning_effort={effort}", "-c", "approval_policy=\"never\"",
           "--json", "--skip-git-repo-check", "-o", rc, "-"]
    m = model or MODEL
    if m:
        cmd[2:2] = ["-m", m]
    _rec = lambda **kw: cost.record(slug=slug, unit=unit, stage=stage, model=(m or "codex-default"),
                                   role=role, strategy=strategy, prompt_chars=len(prompt), **kw)
    t0 = time.time()
    try:
        p = subprocess.run(cmd, input=prompt, text=True, timeout=timeout,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.TimeoutExpired:
        _rec(wall_s=time.time() - t0, err="TIMEOUT")
        return "__TIMEOUT__"
    wall = time.time() - t0
    usage = cost.parse_codex_usage(p.stdout)
    out = open(rc).read().strip() if os.path.exists(rc) else ""
    if os.path.exists(rc):
        os.remove(rc)
    if p.returncode != 0 or not out:            # H9: surface engine failures, don't swallow them
        err = (p.stderr or "").strip().replace(chr(10), " ")[:200]
        log(f"    codex_exec FAILED (rc={p.returncode}, out={len(out)}B){' :: ' + err if err else ''}")
        if not out:
            _rec(wall_s=wall, err=f"rc={p.returncode}", **usage)
            return f"__CODEX_ERROR__ rc={p.returncode} {err}"
    _rec(wall_s=wall, **usage)
    return out


def cheap_judge(case, slug, unit, stage):
    """Cheap-tier judge. Returns (judgment, bar_met).

    Under NO_DEEPSEEK, returns (None, None) — local codex is logged in with a ChatGPT account,
    `gpt-5.3-codex-spark` returns 400 "not supported when using Codex with a ChatGPT account",
    leaving only gpt-5.5 (writer) / gpt-5.6-sol (judge) available, with **no cheaper tier**,
    so the cheap layer of the cascade disappears outright; substituting another model cannot restore it. Callers must follow the degraded path."""
    if NO_DEEPSEEK:
        return (None, None)
    with cost.timed() as _t:
        j = cg.deepseek_judge(case, template="auto")
    ok, _ = cg.bar_met(j, case)
    _rec_ds(_t, slug, unit, stage, j, cheap_reject=not ok)
    return (j, ok)


def _rec_ds(t, slug, unit, stage, ds, cheap_reject=None):
    """Record one DeepSeek judge call. token comes from the cost probe (None if installation fails, retaining only wall)."""
    u = cost.last_deepseek_usage() or {}
    cost.record(slug=slug, unit=unit, stage=stage, role="ACQUIT",
                model=os.environ.get("DEEPSEEK_MODEL", "deepseek"),
                wall_s=getattr(t, "s", None), cheap_reject=cheap_reject,
                verdict=str((ds or {}).get("reaction") or (ds or {}).get("veto") or ""),
                in_tok=u.get("in_tok"), out_tok=u.get("out_tok"),
                cached_in_tok=u.get("cached_in_tok"))


def fill(text, slots):
    for k, v in slots.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def _stage_sig(prompt, model):
    """H10 cache key: filled prompt + engine model + harness version. If any changes,
    the cached output is stale and the stage re-runs."""
    hv = ""
    hvp = os.path.join(HARNESS, "HARNESS_VERSION")
    if os.path.exists(hvp):
        hv = open(hvp).read().strip()
    h = hashlib.sha256()
    h.update(prompt.encode()); h.update(str(model or MODEL or "").encode()); h.update(hv.encode())
    return h.hexdigest()[:16]


def run_stage(stage, slots, output_path, sandbox="workspace-write", effort="medium",
              timeout=1800, dry=False, model=None):
    """Dispatch a materialized stage prompt to Codex; verify its declared output exists.
    H10: skip only when the output is present AND its stage signature is unchanged."""
    stage_path = os.path.join(STAGES, stage)
    if not os.path.exists(stage_path):           # missing stage file -> degrade, don't abort the paper
        log(f"  MISSING stage file: {stage} (skipping this stage)")
        return False
    prompt = fill(open(stage_path).read(), slots)
    sig = _stage_sig(prompt, None)
    # M1 accounting attribution: the slots already contain SLUG/REVIEWER, so callers need no changes
    _slug = slots.get("SLUG") or slots.get("PAPER")
    _unit = slots.get("REVIEWER") or slots.get("EXPID") or slots.get("RID")
    _strat = slots.get("STRATEGY_ID")        # MoE: multiple strategies for the same reviewer must be accounted for separately
    _role = "ACQUIT" if model else "DRIVE"   # model is specified explicitly only at judge stages (b2/b3)
    meta_path = output_path + ".stagemeta"
    if os.path.exists(output_path):
        old = open(meta_path).read().strip() if os.path.exists(meta_path) else None
        if old is None:                          # legacy real output -> adopt, never clobber
            if not dry:
                open(meta_path, "w").write(sig)
            log(f"  skip {stage} (adopt existing: {os.path.basename(output_path)})")
            if not dry:                          # H11: dry-run has zero side effects; even the ledger must not be written
                cost.record(slug=_slug, unit=_unit, stage=stage, role=_role, strategy=_strat,
                            cache_hit=True, wall_s=0.0, verdict="adopt_existing")
            return True
        if old == sig:
            log(f"  skip {stage} (up-to-date: {os.path.basename(output_path)})")
            if not dry:                          # H11
                cost.record(slug=_slug, unit=_unit, stage=stage, role=_role, strategy=_strat,
                            cache_hit=True, wall_s=0.0, verdict="up_to_date")   # an entire engine call saved
            return True
        log(f"  stale {stage} (prompt/model/version changed) -> re-run")
    if dry:
        log(f"  DRY {stage} -> {output_path}")
        return True
    log(f"  run {stage} (effort={effort}{', judge='+model if model else ''}) ...")
    receipt = codex_exec(prompt, sandbox=sandbox, effort=effort, timeout=timeout, model=model,
                         stage=stage, slug=_slug, unit=_unit, role=_role, strategy=_strat)
    ok = os.path.exists(output_path)
    if ok:
        open(meta_path, "w").write(sig)
    log(f"    receipt: {receipt[:160].replace(chr(10),' ')}")
    log(f"    output {'OK' if ok else 'MISSING'}: {output_path}")
    return ok


# ---- gate (DeepSeek in-process + Codex via codex exec) ----------------------

REVIEW_CHAR_BUDGET = 12000               # #24: explicit, logged truncation (was a silent [:6000])


def review_text(slug, rid):
    """#24: fail-closed reviewer extraction. Missing reviewer -> loud warning + empty (not a
    silent ''); IDs may contain '-'; truncation is explicit and logged, not silent."""
    t = open(f"{ROOT}/papers/{slug}/review.md").read()
    parts = re.split(r"Official Review of Submission\d+ by Reviewer ([\w-]+)", t)
    m = {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}
    txt = m.get(rid, "")
    if not txt.strip():
        log(f"  WARNING: reviewer {rid} not found in papers/{slug}/review.md "
            f"(heading regex miss; found {sorted(m)}) -> empty review, judgment will be weak")
        return ""
    if len(txt) > REVIEW_CHAR_BUDGET:
        log(f"  note: review {rid} truncated {len(txt)}->{REVIEW_CHAR_BUDGET} chars")
        txt = txt[:REVIEW_CHAR_BUDGET]
    return txt


def build_case(slug, rev, rebuttal):
    oa = int(rev["initial_overall"])
    prof = (f"You are an ACL/EMNLP (ARR) reviewer. Before the rebuttal your overall "
            f"assessment was {oa}/5. Confidence {rev.get('confidence')}/5. Soundness {rev.get('soundness')}/5.")
    return {"review": review_text(slug, rev["id"]), "reviewer_profile": prof,
            "initial_overall": oa, "rebuttal": rebuttal}


def gate(slug, rev, rebuttal, effort="high"):
    """Cross-family consensus per GOAL.md. DeepSeek in-process; Codex via codex exec.
    NOTE: ammunition is NO LONGER a hard gate here -- the regex is only a cheap RANKING hint
    (it can't tell 'we will revise X' from 'the revised X reads: ...'). The AUTHORITATIVE
    anti-self-harm check is the SEMANTIC B3 gate (ammo_gate), run just before PASS."""
    case = build_case(slug, rev, rebuttal)
    ds, ds_ok = cheap_judge(case, slug, rev, "r7_gate.deepseek")
    ammo = ammo_hits(rebuttal)                  # cheap hint only, not a gate (B3 is the gate)
    if ds is not None and not ds_ok:            # cheap gate rejects -> skip Codex
        return {"stop": False, "ds": ds, "codex": None, "ammo": ammo, "cheap_reject": True}
    codex_raw = codex_exec("Act strictly as the judge in this content; reply with ONLY the JSON it asks for.\n\n"
                           + cg.codex_prompt(case, "auto"),
                           sandbox="read-only", effort=JUDGE_EFFORT, timeout=400,
                           model=JUDGE_MODEL,   # H1: judge on a DISTINCT model, never the writer's
                           stage="r7_gate.codex", slug=slug, unit=rev, role="ACQUIT")
    if codex_raw.startswith(("__CODEX_ERROR__", "__TIMEOUT__")):   # H9: engine failure != a passing judge
        return {"stop": False, "ds": ds, "codex": None, "ammo": ammo,
                "cheap_reject": False, "judge_error": codex_raw[:120]}
    cx = cg.parse_codex(codex_raw)
    if ds is None:
        # Single-family degradation: with only one family, the cross-family semantics of cg.consensus do not hold — do not fabricate them;
        # instead, explicitly construct a judgment marked cross_family=false, so downstream can immediately see that this is not genuine consensus.
        cx_ok, _ = cg.bar_met(cx, case)
        con = {"stop": bool(cx_ok), "kind": "single_family_degraded", "mode": "degraded",
               "primary": "codex", "codex_ok": bool(cx_ok), "deepseek_ok": None,
               "cross_family": False, "degraded": "no-deepseek"}
    else:
        con = cg.consensus(ds, cx, case)
        con["cross_family"] = True
    return {"stop": bool(con["stop"]), "ds": ds, "codex": cx,   # ammo no longer blocks stop (B3 does)
            "consensus": con, "ammo": ammo, "cheap_reject": False}


# ---- per-reviewer MoE goal loop (LOOP.md) -----------------------------------

def cheap_eval(slug, rev, draft):
    """Cheap, Codex-free scoring of one draft (DeepSeek diagnoser + ammo grep). Used to
    RANK drafts before spending the authoritative Codex judge (H14). Higher rank = better."""
    case = build_case(slug, rev, draft)
    ds, ds_ok = cheap_judge(case, slug, rev, "cheap_eval.deepseek")
    ammo = ammo_hits(draft)
    if ds is None:
        # Degradation: no cheap-tier judge → ranking retains only the free ammunition regex, and every draft is admitted to the expensive judge
        # (the cheap gate disappears = the cheap-first savings mechanism fails, so costs rise. This is the cost of degradation; do not conceal it.)
        return {"ds": None, "ammo": ammo, "ds_ok": True, "degraded": "no-deepseek",
                "rank": (1 if not ammo else 0, 1 if not ammo else 0, 0, 0.0)}
    rp_high = str(ds.get("raise_potential", "")).lower() == "high"
    q = float(ds.get("quality", 0) or 0)
    rank = (1 if (ds_ok and not ammo) else 0, 1 if not ammo else 0, 1 if rp_high else 0, q)
    return {"ds": ds, "ammo": ammo, "ds_ok": ds_ok, "rank": rank}


def b2_faithfulness(slug, rev_id, draft_path, dry=False):
    """H5: run the B2 no-fabrication hard gate on a draft that already cleared the raise/
    strength gate. Returns the verdict dict; FAIL (any unsupported number/citation) BLOCKS
    the PASS -- this enforces GOAL.md's no_fabrication predicate, not a rewrite suggestion."""
    out = f"{ROOT}/campaigns/{slug}/ledger/B2_{rev_id}_faithfulness.json"
    if dry:
        return {"verdict": "PASS", "dry": True}
    run_stage("b2_faithfulness_gate.md",
              {"SLUG": slug, "REVIEWER": rev_id, "DRAFT_PATH": draft_path},
              out, sandbox="workspace-write", effort="high", timeout=600, dry=dry,
              model=JUDGE_MODEL)                 # judge on a DISTINCT model from the writer
    try:
        return json.load(open(out))
    except Exception:
        return {"verdict": "FAIL", "reasons": ["B2 gate produced no parseable output"]}


# The explicit rule in b3_ammunition_gate.md §2/§6: A–E hits block PASS (E is additionally marked red_line);
# deletable / not_direct are advisory only and do not block. Compute the verdict **in code**, no longer relying on the judge's self-reported verdict —
# when the judge misses a hit it will also report CLEAN, while the union may already contain blocking-category hits caught by another trial.
B3_BLOCKING = {"A", "B", "B2", "C", "C2", "D", "E"}
B3_ADVISORY = {"deletable", "not_direct"}


def _b3_key(h):
    """Hit deduplication key: category + the first 120 characters of the quote (the same sentence may be truncated slightly differently across trials)."""
    return (str(h.get("category", "")).strip(),
            " ".join(str(h.get("quote", "")).split())[:120].lower())


def ammo_gate(slug, rev_id, draft_path, dry=False, repeats=None):
    """B3 semantic anti-self-harm gate -- the AUTHORITATIVE ammunition check, replacing the
    static regex. An independent judge (distinct model) READS the draft and finds self-exposure /
    empty promises / over-concession / performative honesty / fabrication by MEANING, not pattern
    (regex can't tell 'we will revise X' from 'the revised X reads: ...'). HAS_AMMO blocks PASS.

    ★ union-of-N (after the 2026-09-29 reproducibility measurement). Empirical results from judging the same draft (unchanged sha) 10 times:
      · **The verdict is stable**: the judge faithfully follows §2/§6 — all 10/10 returned "HAS_AMMO whenever there is a blocking-category hit."
      · **Detection is unstable**: the same substantive over-claiming (category D) was found 3/5 times at medium,
        and 4/5 times at xhigh; n_hits ranged from 1–7. The faster runs were exactly the runs that missed it.
      ⇒ This is purely a recall problem, not a decision-standard problem. Run N times and take the **union**: miss rate 0.2^N
        (N=3 → 0.8%). A single B3 costs only ≈88k token; 3 runs are still cheaper than one 780k-token B2 run.
      The gate should favor recall: the cost of missing ammunition (sending a draft containing exaggeration) is far greater than one false positive (editing one extra sentence).
    """
    out = f"{ROOT}/campaigns/{slug}/ledger/B3_{rev_id}_ammunition.json"
    if dry:
        return {"verdict": "CLEAN", "dry": True}
    n = int(repeats or B3_REPEATS)
    merged, trials = {}, []
    for i in range(1, n + 1):
        for p in (out, out + ".stagemeta"):      # Every run must actually execute (the draft changes each round + repeated sampling is itself required)
            if os.path.exists(p):
                os.remove(p)
        _b3_run_once(slug, rev_id, draft_path)
        try:
            r = json.load(open(out))
        except Exception:
            r = {"verdict": "HAS_AMMO", "hits": [{"category": "A",
                 "why": "B3 gate produced no parseable output"}]}
        hits = r.get("hits") or []
        trials.append({"trial": i, "judge_verdict": r.get("verdict"), "n_hits": len(hits),
                       "cats": sorted({str(h.get("category")) for h in hits})})
        for h in hits:
            merged.setdefault(_b3_key(h), h)     # union deduplication
    hits = list(merged.values())
    blocking = [h for h in hits if str(h.get("category", "")).strip() in B3_BLOCKING]
    res = {"verdict": "HAS_AMMO" if blocking else "CLEAN",
           "red_line": any(str(h.get("category", "")).strip() == "E" for h in hits),
           "hits": hits, "n_hits": len(hits), "n_blocking": len(blocking),
           # Audit trail: make a miss in a particular run inspectable afterward and make the union's benefit measurable
           "union_of": n, "effort": "xhigh", "judge_model": JUDGE_MODEL, "trials": trials}
    disagree = {t["judge_verdict"] for t in trials}
    if len(disagree) > 1:
        log(f"    B3 union-of-{n}: judges' self-reports disagree across runs {sorted(disagree)} "
            f"(n_hits={[t['n_hits'] for t in trials]}) → verdict by union: {res['verdict']}")
    json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
    return res


def _b3_run_once(slug, rev_id, draft_path):
    out = f"{ROOT}/campaigns/{slug}/ledger/B3_{rev_id}_ammunition.json"
    run_stage("b3_ammunition_gate.md",
              {"SLUG": slug, "REVIEWER": rev_id, "DRAFT_PATH": draft_path},
              # effort: medium → xhigh (after the 2026-09-29 reproducibility measurement). B3 is the only gate that must **read the entire text sentence by sentence
              # to find semantic ammunition** — a pure recall task, it consumes the most reasoning budget, yet previously had the lowest allocation of the three gates
              # (r7 xhigh / B2 high / B3 medium). Across 7 judgments of the same draft, empirical results were 3 CLEAN / 4 HAS_AMMO,
              # with detection counts varying between 1–6, and **the faster runs were exactly the runs that missed hits** (55s→found 1-2,
              # 74-110s→found 6). All three gates use the same model (gpt-5.6-sol), so effort is the only adjustable independent variable.
              # Increase timeout in parallel from 400→900: deep review at medium already took 110s; if xhigh exceeds 400s, that would create a self-inflicted timeout failure.
              out, sandbox="workspace-write", effort="xhigh", timeout=900,
              model=JUDGE_MODEL)                 # semantic judge, distinct from the writer


def join_budget(items, budget, what="feedback", logger=None):
    """Join the judge's findings into the carry-forward seed; **budget overflow must be reported**.

    Root cause (same class as #24): fab[:300] / ammo_fix[:400] previously truncated directly — one B3 run yields 5-6
    hits, each containing a quote (~95 characters) + rewrite advice, so 400 characters can hold only 1-2 hits; **the remainder
    never reaches the writer in the next round**, making it impossible for the loop to clear them all. It also fails silently: this appears as "the loop performs poorly,"
    not "an error occurred." DESIGN_LOGIC §4 principle 2: truncation must be reported.

    This is lifted to module scope for unit testing — it was previously a closure inside reviewer_loop, so changes could not be verified.
    The unit test immediately caught that after B3 changed to union-of-3, hits rose from 5-6 to **12 hits / 4305 characters**,
    while a budget of 2500 could hold only 7 hits — the two changes interact, so merely increasing the budget is insufficient.
    Therefore callers must **sort by importance first** (blocking categories first; advisory categories may be dropped); this function handles only packing and warnings.
    """
    out, used, dropped = [], 0, 0
    for it in items:
        t = str(it).strip()
        if not t:
            continue
        if used + len(t) + 2 > budget:
            dropped += 1
            continue
        out.append(t)
        used += len(t) + 2
    if dropped:
        msg = (f"    note: {what} feedback exceeds budget; dropped {dropped}/{len(items)} items"
               f"(budget={budget}) — these will not reach the next round; consider increasing the budget")
        (logger or log)(msg)
    return "; ".join(out)


MT_ROUNDS = 3            # --mt-rounds: maximum number of rounds in the multi-turn exchange
MT_NOVELTY_SIM = 0.5     # Upper bound on follow-up similarity across rounds; exceeding it counts as repetition → stop at saturation


def _rejected_expids(slug):
    """Experiments judged REJECT in ACCEPTANCE.json — the author turn must not cite them as evidence."""
    out = set()
    d = f"{ROOT}/campaigns/{slug}/experiments"
    if not os.path.isdir(d):
        return out
    for eid in os.listdir(d):
        a = f"{d}/{eid}/ACCEPTANCE.json"
        if os.path.exists(a):
            try:
                if str(json.load(open(a)).get("verdict", "")).upper() == "REJECT":
                    out.add(eid)
            except Exception:
                pass
    return out


def multiturn_exchange(slug, rev, draft_path, rounds=None, dry=False):
    """② Multi-turn exchange simulation: reviewer follow-up → author response → another follow-up, for at most N rounds.

    The existing pipeline simulates only a **single turn** (the judge reads once and issues a judgment); this simulates actual back-and-forth during the discussion period.
    It tests not "whether the first impression passes," but "**whether the draft withstands follow-up questions**."

    ★ Not a gate. It does not prevent r7 from judging PASS; its output identifies "which claim collapses under follow-up,"
      for narrowing in r6 or inclusion in the honest-concede list.

    The minimal premise has been empirically verified (01-wdData/37ch): the round 2 follow-up had similarity 0.03 to round 1 and anchored to a different sentence,
    while round 2 was more consequential (advancing from "what is the quality screen" to "whether recalibration used labels from the same round" = data leakage).
    Control group: the approach of changing persona priors yielded similarity 0.74-0.80 and was falsified.

    Invariants enforced in code (not dependent on engine compliance):
      · reviewer = JUDGE_MODEL(ACQUIT), author = writer MODEL(DRIVE); refuse to run if they are the same model
      · refuse to run if evidence_pool is missing (otherwise the author turn falls back to unfiltered evidence)
      · compute the novelty criterion in code (similarity + anchor sentence); do not ask the engine "whether this is novel"
      · red-line detection: the author introduces new numbers / cites a REJECT experiment
    """
    import difflib
    rid = rev["id"]
    camp = f"{ROOT}/campaigns/{slug}"
    n = int(rounds or MT_ROUNDS)
    if MODEL and JUDGE_MODEL and MODEL == JUDGE_MODEL:
        log(f"  mt {rid}: writer and judge use the same model ({MODEL}) → refusing to run. Self-questioning and self-answering inevitably converge on agreement.")
        return {"status": "BLOCKED", "reason": "writer == judge"}
    if not dry and not os.path.exists(f"{camp}/ledger/evidence_pool.json"):
        log(f"  mt {rid}: evidence_pool.json missing → refusing to run (the author turn would fall back to unfiltered evidence)")
        return {"status": "BLOCKED", "reason": "no evidence_pool"}
    rejected = _rejected_expids(slug)
    hist_path = f"{camp}/ledger/mt_{rid}_history.md"
    if not dry:
        open(hist_path, "w").write("")
    exchange, red_flags, prev = [], [], []
    for r in range(1, n + 1):
        slots = {"SLUG": slug, "REVIEWER": rid, "ROUND": r, "OA": rev.get("initial_overall"),
                 "DRAFT_PATH": draft_path, "HISTORY_PATH": hist_path}
        rv_out = f"{camp}/ledger/mt_{rid}_r{r}_reviewer.json"
        for q in (rv_out, rv_out + ".stagemeta"):
            if not dry and os.path.exists(q):
                os.remove(q)
        # sandbox must be workspace-write: this stage **declares an output file**, which a read-only sandbox cannot write.
        # (Copying the r7 judge's read-only setting would be wrong — the r7 judge writes no file; its judgment is parsed from the receipt.
        #  Judges such as B2/B3 that "must write a judgment file" use workspace-write.)
        run_stage("mt_reviewer_turn.md", slots, rv_out, sandbox="workspace-write", effort=JUDGE_EFFORT,
                  timeout=600, dry=dry, model=JUDGE_MODEL)
        if dry:
            continue
        try:
            rv = json.load(open(rv_out))
        except Exception:
            log(f"    mt r{r}: reviewer turn produced no parseable output → stop"); break

        # ★ Compute the novelty criterion in code (DESIGN_LOGIC §4 principle 3: decisions belong in code)
        fu = str(rv.get("followup", ""))
        qt = str(rv.get("quote", "")).strip()[:80].lower()
        sims = [difflib.SequenceMatcher(None, str(p["followup"]), fu).ratio() for p in prev]
        dup_quote = any(str(p["quote"]).strip()[:80].lower() == qt for p in prev)
        if prev and (max(sims) >= MT_NOVELTY_SIM or dup_quote):
            log(f"    mt r{r}: follow-up is not novel (sim={max(sims):.2f} dup_quote={dup_quote}) → saturated, stop")
            exchange.append({"round": r, "saturated": True, "similarity": round(max(sims), 3)})
            break

        au_out = f"{camp}/ledger/mt_{rid}_r{r}_author.json"
        for q in (au_out, au_out + ".stagemeta"):
            if os.path.exists(q):
                os.remove(q)
        slots["FOLLOWUP_PATH"] = rv_out
        run_stage("mt_author_turn.md", slots, au_out, sandbox="workspace-write",
                  effort=WRITE_EFFORT, timeout=900, dry=dry, model=MODEL)
        try:
            au = json.load(open(au_out))
        except Exception:
            log(f"    mt r{r}: author turn produced no parseable output → stop"); break

        # Red-line detection (judge in code; do not ask the engine)
        newnums = [x for x in (au.get("new_numbers_introduced") or []) if str(x).strip()]
        badev = [e for e in (au.get("evidence_used") or []) if any(rj in str(e) for rj in rejected)]
        if newnums:
            red_flags.append({"round": r, "kind": "fabricated_numbers", "detail": newnums})
            log(f"    🔴 mt r{r}: under pressure, the author introduced numbers absent from the evidence pool {newnums}")
        if badev:
            red_flags.append({"round": r, "kind": "cited_rejected_experiment", "detail": badev})
            log(f"    🔴 mt r{r}: the author cited REJECT experiments as evidence {badev}")

        exchange.append({"round": r, "quote": rv.get("quote"), "followup": fu,
                         "targets_concern": rv.get("targets_concern"),
                         "similarity_to_prior": round(max(sims), 3) if sims else None,
                         "answer": au.get("answer"), "conceded": bool(au.get("conceded")),
                         "concession_scope": au.get("concession_scope"),
                         "narrowed_claim": au.get("narrowed_claim"),
                         "evidence_used": au.get("evidence_used")})
        prev.append({"followup": fu, "quote": rv.get("quote")})
        with open(hist_path, "a") as f:
            f.write(f"\n[Reviewer Q{r}] {fu}\n[Authors A{r}] {au.get('answer')}\n")
        log(f"    mt r{r}: conceded={au.get('conceded')} "
            f"sim={round(max(sims),3) if sims else '-'} anchor sentence \"{str(rv.get('quote'))[:40]}…\"")

    # Collapsed claim = where the author concedes or narrows — this is the real output of this stage
    collapsed = [e for e in exchange if e.get("conceded") or e.get("narrowed_claim")]
    res = {"reviewer": rid, "rounds_run": len([e for e in exchange if not e.get("saturated")]),
           "max_rounds": n, "saturated": any(e.get("saturated") for e in exchange),
           "collapsed_claims": collapsed, "red_flags": red_flags,
           "reviewer_model": JUDGE_MODEL, "author_model": MODEL or "codex-default",
           "exchange": exchange}
    if not dry:
        json.dump(res, open(f"{camp}/ledger/mt_{rid}_exchange.json", "w"),
                  ensure_ascii=False, indent=1)
    log(f"  mt {rid}: ran {res['rounds_run']} rounds, {len(collapsed)} collapses, "
        f"{len(red_flags)} red lines{' (stopped early at saturation)' if res['saturated'] else ''}")
    return res


def route_back(g):
    """H13: type the failure so the loop routes to the RIGHT stage, not always r6-rewrite.
    evidence shortage -> r4 (run an experiment); concern misdiagnosed -> r2 (re-diagnose);
    else a text-level gap -> r6 (rewrite). Returns (stage, reason)."""
    ds = g.get("ds") or {}
    txt = " ".join(str(ds.get(k, "")) for k in ("blocker", "advice", "reasoning", "veto")).lower()
    if any(w in txt for w in ("need experiment", "needs experiment", "missing data", "no data",
                              "empirical evidence", "run an experiment", "additional experiment",
                              "ablation", "experiment required", "add an experiment", "data missing", "evidence missing")):
        return ("r4", "evidence shortage -> needs an experiment (r4), not a rewrite")
    if any(w in txt for w in ("misdiagnos", "wrong concern", "mischaracter", "misread",
                              "actually about", "the real concern", "misjudged", "incorrect diagnosis")):
        return ("r2", "concern misdiagnosed -> re-run diagnosis (r2)")
    return ("r6", "text-level gap -> rewrite (r6)")


# ---- experiment persuasion gate (POST): the S bar, shifted-left, per-served-concern ----
# X1-X6 (r4_accept) proves an experiment is HONEST. This proves it is PERSUASIVE: does the real,
# accepted result actually RESOLVE the concern it serves, at the strength that reviewer's zone bar
# needs? It REUSES the FROZEN consensus machinery (cg.deepseek_judge + Codex + cg.bar_met/consensus)
# on a per-concern stub built ONLY from real numbers -- structurally identical to gate() (the S bar),
# just concern-scoped and applied to the experiment BEFORE r5 merges it. An honest-but-unpersuasive
# result (null / double-edged / off-target) is reframed (LOWER_BOUND) or conceded (CONCEDE) here, so
# r6 never writes it as strength (= B3 ammunition C/D). NOT a new bar -- a new CONSUMER of bar_met.

_PERSUADE_FRAMING = {
    "STRENGTH": "Present as a DIRECT answer to this concern: state the result in past / present-perfect "
                "tense ('we ran X and observed Y') and mirror the concern's subject-verb-object in the "
                "first clause; do not hedge.",
    "LOWER_BOUND": "Evidence supports only a BOUNDED claim. Write an honest lower-bound answer to the "
                   "concern's specific clause; do NOT generalize to 'stable'/'robust'/'in general' "
                   "(overclaim = B3 ammunition; cf. 02-judgeswap). Past tense for what ran; any manuscript "
                   "change uses 'In the camera-ready we will ...'.",
    "CONCEDE": "This result does NOT resolve the concern; do NOT present it as strength (= B3 ammunition "
               "C/D). Answer via the warrant ladder (warrant ladder move 6): state the limitation once "
               "as a POSITIVE technical scope condition, then stop; add 'In the camera-ready we will ...' "
               "only for a legitimate edit.",
}


def _parse_serves(entry, reviewer_ids):
    """'vCzF-W4 (long free-form CoT generalization)' -> (reviewer, label, desc). Robust to reviewer
    ids that contain digits (37ch) and to a missing parenthetical. Reviewer = longest card id that
    prefixes the entry (never a substring guess)."""
    s = str(entry).strip()
    rid = next((r for r in sorted(reviewer_ids, key=len, reverse=True)
                if s == r or s.startswith(r + "-") or s.startswith(r + " ") or s.startswith(r + "_")), None)
    m = re.search(r"\(([^)]*)\)", s)
    desc = m.group(1).strip() if m else (re.sub(r"^\S+\s*", "", s).strip() or s)
    lm = re.match(r"[^\s(]*?-(\w+)", s)
    return rid, (lm.group(1) if lm else ""), desc


def _render_derived(derived):
    """Honest, compact rendering of results.json.derived for the stub -- REAL numbers only, no LLM."""
    if not isinstance(derived, dict):
        return str(derived)[:900]
    head = derived.get("headline") or derived.get("interpretation") or ""
    if not isinstance(head, str):                    # headline can be a dict/list -> render it
        head = json.dumps(head, ensure_ascii=False)[:600]
    nums = {k: v for k, v in derived.items() if k not in ("headline", "interpretation")}
    body = json.dumps(nums, ensure_ascii=False)[:1300] if nums else ""
    return ((head + "\n") if head else "") + body


def _judge_why(j):
    """The primary judge's reason it did NOT clear -- drives the redesign 'why + how'."""
    j = j or {}
    return (j.get("blocker") or j.get("veto") or j.get("advice") or j.get("reasoning") or "")


def _persuade_verdict(con):
    """ZONE-ROUTED verdict, mirroring r7's consensus (fixes the OA=3 bug where a weak DeepSeek could
    unilaterally CONCEDE). STRENGTH iff the zone's stop fires; CONCEDE iff the zone's PRIMARY
    (authoritative) family itself doesn't clear (Codex at the OA=3 border); LOWER_BOUND in between
    (primary clears but the other family vetoes, or a strict zone only half-clears)."""
    if not con:
        return "CONCEDE"
    if con.get("stop"):
        return "STRENGTH"
    prim_ok = con.get("codex_ok") if con.get("primary") == "codex" else con.get("deepseek_ok")
    return "LOWER_BOUND" if prim_ok else "CONCEDE"


def _persuade_judge(rid, oa, concern_desc, stub, dry=False):
    """One (reviewer, concern) adjudication -- ZONE-ROUTED exactly like r7's consensus. At the OA=3
    border Codex is the authoritative primary, so we ALWAYS ask it (never let a weak DeepSeek cheap-
    reject decide CONCEDE there); off-border (strict) DeepSeek is a co-equal family, so a DeepSeek bar
    miss is a legitimate cheap-reject. Case scoped to THIS concern; judge model != writer (anti-Goodhart)."""
    if dry:
        return {"verdict": "STRENGTH", "dry": True, "why": "", "advice": ""}
    prof = (f"You are an ACL/EMNLP (ARR) reviewer whose overall assessment is {oa}/5. Judge ONLY "
            f"whether the response adequately resolves the specific concern quoted.")
    case = {"review": f"Reviewer {rid}'s specific concern under adjudication:\n{concern_desc}",
            "reviewer_profile": prof, "initial_overall": oa, "rebuttal": stub}
    ds, ds_ok = cheap_judge(case, None, rid, "s_exp.deepseek")
    primary = "codex" if ds is None else cg.primary_judge(case)   # Degradation: only the codex family remains, so it is the primary judge
    if ds is None:
        ds_ok = True                                 # No cheap tier → do not cheap-reject; go directly to the authoritative judge
    if not ds_ok and primary != "codex":             # strict zone: DeepSeek is co-equal -> valid cheap-reject
        rp = str(ds.get("raise_potential", "")).lower()
        return {"verdict": "LOWER_BOUND" if rp == "high" else "CONCEDE", "ds": ds, "codex": None,
                "consensus": None, "cheap_reject": True, "why": _judge_why(ds),
                "advice": ds.get("advice") or ds.get("reasoning") or ""}
    codex_raw = codex_exec("Act strictly as the judge in this content; reply with ONLY the JSON it asks for.\n\n"
                           + cg.codex_prompt(case, "auto"),
                           sandbox="read-only", effort=JUDGE_EFFORT, timeout=400, model=JUDGE_MODEL,
                           stage="s_exp.codex", unit=rid, role="ACQUIT")
    if codex_raw.startswith(("__CODEX_ERROR__", "__TIMEOUT__")):   # engine fail != a free STRENGTH
        return {"verdict": "LOWER_BOUND", "ds": ds, "codex": None, "consensus": None,
                "judge_error": codex_raw[:120], "why": _judge_why(ds),
                "advice": ds.get("advice") or ds.get("reasoning") or ""}
    cx = cg.parse_codex(codex_raw)
    con = cg.consensus(ds, cx, case)
    prim_j = cx if primary == "codex" else ds
    return {"verdict": _persuade_verdict(con), "ds": ds, "codex": cx, "consensus": con,
            "why": _judge_why(prim_j), "advice": con.get("advice") or ""}


def _rollup(verdicts):
    if not verdicts:
        return "NONE"
    if all(v == "STRENGTH" for v in verdicts):
        return "STRENGTH"
    if any(v in ("STRENGTH", "LOWER_BOUND") for v in verdicts):
        return "PARTIAL"
    return "CONCEDE"


def _driver_sha(edir):
    """sha256 prefix of the experiment's driver.py -- the 'is the code unchanged' key (v0.7)."""
    dp = f"{edir}/driver.py"
    return hashlib.sha256(open(dp, "rb").read()).hexdigest()[:16] if os.path.exists(dp) else None


def accept_experiment(slug, expid, data_source, dry=False, model=None):
    """v0.7 TWO-PHASE acceptance -- kills the 're-run the whole experiment on every verify' redundancy.
    The expensive ORIGIN AUDIT (static code audit + one X6 independent rerun) runs ONCE. Later verifies
    are CHEAP: if a prior ACCEPTANCE's origin_audit matches the current driver_sha256 AND data_fingerprint,
    the experiment is provably unchanged -> reuse the origin audit, do NOT re-execute. Re-audit only when
    the driver or data changed, or no prior audit exists (or the prior verdict was not ACCEPT/PARTIAL)."""
    edir = f"{ROOT}/campaigns/{slug}/experiments/{expid}"
    out = f"{edir}/ACCEPTANCE.json"
    if dry:
        return {"verdict": "ACCEPT", "dry": True}
    dsha = _driver_sha(edir)
    dfp = None
    man = f"{edir}/manifest.json"
    if os.path.exists(man):
        try:
            dfp = json.load(open(man)).get("data_fingerprint") or {}
        except Exception:
            dfp = None
    if os.path.exists(out):                          # CHEAP re-check: unchanged driver+data -> reuse origin
        try:
            prev = json.load(open(out))
            oa = prev.get("origin_audit") or {}
            if (dsha and oa.get("driver_sha256") == dsha and oa.get("data_fingerprint") == dfp
                    and str(prev.get("verdict", "")).upper() in ("ACCEPT", "PARTIAL")):
                log(f"  accept {expid}: CHEAP re-check (driver+data unchanged; origin audit valid, no re-run)")
                return prev
        except Exception:
            pass
    run_stage("r4_experiment_accept.md",             # full ORIGIN AUDIT (X1-X6, incl. one X6 rerun)
              {"SLUG": slug, "EXPID": expid, "DATA_SOURCE": data_source, "DRIVER_SHA": dsha or "unknown"},
              out, sandbox="danger-full-access", effort="high", timeout=1800, dry=dry, model=model)
    if os.path.exists(out):                          # stamp origin provenance so future runs cheap-skip
        try:
            a = json.load(open(out))
            oa = a.setdefault("origin_audit", {})
            oa.setdefault("driver_sha256", dsha)
            oa.setdefault("data_fingerprint", dfp)
            json.dump(a, open(out, "w"), ensure_ascii=False, indent=1)
            return a
        except Exception:
            pass
    return {}


def experiment_persuasion(slug, expid, card, dry=False):
    """POST gate for ONE accepted experiment. Writes experiments/<expid>/PERSUASION.json with a
    per-(reviewer,concern) verdict. r5 reads it: STRENGTH->met, LOWER_BOUND->partial(+framing),
    CONCEDE->unmet (even when X1-X6 = ACCEPT)."""
    edir = f"{ROOT}/campaigns/{slug}/experiments/{expid}"
    acc_p, res_p, out = f"{edir}/ACCEPTANCE.json", f"{edir}/results.json", f"{edir}/PERSUASION.json"
    if os.path.exists(out):                          # experiments are immutable once accepted
        try:
            return json.load(open(out))
        except Exception:
            pass
    if not (os.path.exists(acc_p) and os.path.exists(res_p)):
        return None
    try:
        acc, res = json.load(open(acc_p)), json.load(open(res_p))
    except Exception as e:
        log(f"  persuasion {expid}: unreadable ACCEPTANCE/results ({e}) -> skip")
        return None
    if str(acc.get("verdict", "")).upper() not in ("ACCEPT", "PARTIAL"):
        return None                                  # not honest -> r5 already excludes; no persuasion
    rev_oa = {r["id"]: int(r["initial_overall"]) for r in card.get("reviewers", [])
              if r.get("id") and r.get("initial_overall") is not None}
    serves = acc.get("serves") or []
    if not serves:                                   # fall back to the queue if ACCEPTANCE has none
        qp = f"{ROOT}/campaigns/{slug}/ledger/experiment_queue.json"
        if os.path.exists(qp):
            try:
                q = json.load(open(qp))
                for req in (q if isinstance(q, list) else q.get("experiments", [])):
                    if (req.get("expid") or req.get("id")) == expid:
                        serves = req.get("serves") or []
            except Exception:
                pass
    stub_result = _render_derived(res.get("derived"))
    targets = []
    for entry in serves:
        rid, label, desc = _parse_serves(entry, list(rev_oa))
        if rid is None or rid not in rev_oa:
            log(f"  persuasion {expid}: cannot resolve reviewer/OA for serves='{entry}' -> skip target")
            continue
        oa = rev_oa[rid]
        stub = (f"Reviewer concern: {desc or entry}\n\nWe ran an experiment and observed: {stub_result}\n"
                f"(Acceptance: X1-X6 {acc.get('verdict')}.)")
        j = _persuade_judge(rid, oa, desc or entry, stub, dry=dry)
        con = j.get("consensus") or {}
        targets.append({"reviewer": rid, "concern": label or entry, "serves": entry, "oa": oa,
                        "verdict": j["verdict"], "framing_hint": _PERSUADE_FRAMING.get(j["verdict"], ""),
                        "deepseek_ok": bool(con.get("deepseek_ok", not j.get("cheap_reject", False))),
                        "codex_verdict": (j.get("codex") or {}).get("reaction"),
                        "why_not_persuasive": (j.get("why") or "")[:600] if j["verdict"] != "STRENGTH" else "",
                        "judge_advice": (j.get("advice") or "")[:600] if j["verdict"] != "STRENGTH" else "",
                        "judge_error": j.get("judge_error")})
    result = {"expid": expid, "acceptance": acc.get("verdict"),
              "overall": _rollup([t["verdict"] for t in targets]), "targets": targets, "gate": GATE_SHA}
    if not dry:
        json.dump(result, open(out, "w"), ensure_ascii=False, indent=1)
    return result


# ---- experiment GOAL LOOP: ANTE guard -> (run -> accept -> persuade -> redesign)* -> STRENGTH|concede
# The persuasion gate is the STOP PREDICATE, exactly as r7 is reviewer_loop's. ANTE guards the entrance
# (is a cheaper warrant already enough? would best-case even persuade?); every non-STRENGTH result emits
# WHY it fails + HOW to redesign, and the loop re-runs the STRONGER experiment. Only STRENGTH stops
# (user policy); when redesign is infeasible or max_iter hits, it exits HONEST_CONCEDE carrying the best
# REAL result -- NEVER relabeled STRENGTH. That is how "only STRENGTH counts" and "never fabricate"
# both hold: STRENGTH is reached by a genuinely stronger experiment, not by dressing up a weak result.

def _served_targets(serves, rev_oa):
    out = []
    for entry in serves or []:
        rid, label, desc = _parse_serves(entry, list(rev_oa))
        if rid in rev_oa:
            out.append((rid, rev_oa[rid], label or entry, desc or entry, entry))
    return out


def _bestcase_stub(req, desc):
    """A hypothetical BEST-CASE result for ANTE (does the experiment even have a persuasive ceiling?).
    Uses the pre-registered success criterion -- clearly hypothetical, gates a decision to RUN, not a claim."""
    crit = (req.get("expected_or_falsifier") or req.get("hypothesis") or req.get("goal")
            or "the hypothesized effect holds with a clear, statistically significant margin")
    return (f"Reviewer concern: {desc}\n\nWe will run an experiment; in the BEST case the real result "
            f"shows: {crit} (paper's real data, a real baseline, sufficient scale/seeds).")


def _cheaper_warrant_for(concern_label, desc, evidence_map):
    """Best EXISTING non-experiment warrant for this concern (paper location / existing asset / lit),
    used to test 'is a new experiment even necessary?'. Best-effort over a loose schema; None if unsure
    (conservative -> never wrongly drops an experiment)."""
    if not evidence_map:
        return None
    items = evidence_map if isinstance(evidence_map, list) else \
        (evidence_map.get("evidence") or evidence_map.get("items") or evidence_map.get("concerns") or [])
    words = {w.lower() for w in re.findall(r"\w+", desc or "") if len(w) > 4}
    best = None
    for it in items if isinstance(items, list) else []:
        if not isinstance(it, dict):
            continue
        src = str(it.get("source") or it.get("type") or "").lower()
        if not any(k in src for k in ("paper", "existing", "asset", "literature", "cite")):
            continue
        text = " ".join(str(it.get(k, "")) for k in ("interpretation", "text", "note", "warrant", "desc"))
        key = str(it.get("concern_id") or it.get("concern") or it.get("id") or "")
        hit = (concern_label and concern_label in key) or (words & {w.lower() for w in re.findall(r"\w+", text)})
        if hit and text.strip():
            best = text.strip()[:500]
    return best


def experiment_ante(slug, req, card, dry=False):
    """ANTE guard (before any GPU run), 'block only by consensus' (conservative): per served concern, judge (a) the best
    cheaper warrant and (b) the experiment's best-case, via the SAME frozen consensus. NOT_NEEDED iff a
    cheaper warrant already clears the bar for every served concern; GREENLIGHT iff best-case clears for
    >=1; else REDESIGN (even the best possible result won't get consensus -> don't burn the run)."""
    if dry:
        return {"decision": "GREENLIGHT", "dry": True, "per_concern": []}
    emap_p = f"{ROOT}/campaigns/{slug}/ledger/evidence_map.json"
    evidence_map = json.load(open(emap_p)) if os.path.exists(emap_p) else None
    rev_oa = {r["id"]: int(r["initial_overall"]) for r in card.get("reviewers", [])
              if r.get("id") and r.get("initial_overall") is not None}
    per = []
    for rid, oa, label, desc, entry in _served_targets(req.get("serves"), rev_oa):
        w = _cheaper_warrant_for(label, desc, evidence_map)
        cheaper = (_persuade_judge(rid, oa, desc, f"Reviewer concern: {desc}\n\nResponse (no new experiment): {w}",
                                   dry)["verdict"] == "STRENGTH") if w else False
        best = _persuade_judge(rid, oa, desc, _bestcase_stub(req, desc), dry)["verdict"] == "STRENGTH"
        per.append({"reviewer": rid, "concern": label, "cheaper_clears": cheaper, "bestcase_clears": best})
    if per and all(p["cheaper_clears"] for p in per):
        decision = "NOT_NEEDED"
    elif any(p["bestcase_clears"] for p in per):
        decision = "GREENLIGHT"
    else:
        decision = "REDESIGN"
    return {"decision": decision, "per_concern": per, "gate": GATE_SHA}


def _queue_upsert(slug, req, dry=False):
    """Make a (possibly redesigned) experiment_request visible to r4_experiment_run, which reads the
    request from experiment_queue.json by expid."""
    if dry:
        return
    qp = f"{ROOT}/campaigns/{slug}/ledger/experiment_queue.json"
    q = []
    if os.path.exists(qp):
        try:
            raw = json.load(open(qp))
            q = raw if isinstance(raw, list) else (raw.get("experiments") or [])
        except Exception:
            q = []
    eid = req.get("expid") or req.get("id")
    q = [r for r in q if (r.get("expid") or r.get("id")) != eid] + [req]
    json.dump(q, open(qp, "w"), ensure_ascii=False, indent=1)


def experiment_redesign(slug, req, expid, basis, iteration, dry=False):
    """DRIVE-side planner (NOT the judge; runs on the writer/default engine, not JUDGE_MODEL). Reads the
    real concern + the failing result (or best-case) + the judge's WHY, emits WHY it cannot persuade + a
    concrete stronger experiment_request + a feasibility verdict. Infeasible -> honest concession."""
    edir = f"{ROOT}/campaigns/{slug}/experiments/{expid}"
    out = f"{edir}/redesign_iter{iteration}.json"
    base_id = re.sub(r"-r\d+$", "", req.get("expid") or expid)   # clean chain: base-r2, base-r3 (not -r2-r3)
    if dry:
        return {"feasible": True, "dry": True,
                "new_experiment_request": {**req, "expid": f"{base_id}-r{iteration+1}"}}
    for p in (out, out + ".stagemeta"):              # result changes each iter -> always re-plan
        if os.path.exists(p):
            os.remove(p)
    run_stage("r4_experiment_redesign.md",
              {"SLUG": slug, "EXPID": expid, "BASIS": basis, "ITER": iteration},
              out, sandbox="workspace-write", effort="high", timeout=900, dry=dry)   # planner = DRIVE engine
    try:
        rd = json.load(open(out))
    except Exception:
        return {"feasible": False, "why_cannot_persuade": "redesign planner produced no parseable output"}
    nr = rd.get("new_experiment_request")
    if rd.get("feasible") and isinstance(nr, dict) and not (nr.get("expid") or nr.get("id")):
        nr["expid"] = f"{base_id}-r{iteration+1}"   # ensure a fresh, cleanly-chained id
    return rd


def _write_exploop(slug, base, obj, dry=False):
    if not dry:
        json.dump(obj, open(f"{ROOT}/campaigns/{slug}/experiments/{base}/loop.json", "w"),
                  ensure_ascii=False, indent=1)


def experiment_loop(slug, req, card, dry=False):
    """Drive ONE experiment to STRENGTH or honest concession. Writes experiments/<base>/loop.json."""
    max_iter = int(card.get("max_experiment_iter", 3))
    base = req.get("expid") or req.get("id")
    edir0 = f"{ROOT}/campaigns/{slug}/experiments/{base}"
    if not dry:
        os.makedirs(edir0, exist_ok=True)
    log(f"-- experiment {base} (serves {req.get('serves')}) --")
    chain = []

    # ANTE is a BEFORE-you-run necessity guard. If the experiment ALREADY has results, that question is
    # moot (it ran) and a retrospective best-case judgment can false-negative a result that actually passes
    # (e.g. a 'proves no harm' null result reads weak in the abstract but its real numbers clear S-exp).
    # So skip ANTE for already-run experiments -> go straight to accept + persuade.
    already_ran = os.path.exists(f"{edir0}/results.json")
    if already_ran:
        ante = {"decision": "GREENLIGHT", "skipped": "experiment already has results -> necessity moot"}
        log(f"  ANTE {base}: SKIPPED (already ran -> accept+persuade)")
    else:
        ante = experiment_ante(slug, req, card, dry=dry)
        log(f"  ANTE {base}: {ante['decision']}")
    chain.append({"phase": "ANTE", "decision": ante["decision"], "skipped": ante.get("skipped")})
    if ante["decision"] == "NOT_NEEDED":
        _write_exploop(slug, base, {"expid": base, "status": "NOT_NEEDED", "chain": chain, "ante": ante}, dry)
        return {"expid": base, "status": "NOT_NEEDED"}

    cur = dict(req)
    if ante["decision"] == "REDESIGN":               # best-case can't pass -> redesign BEFORE burning a run
        rd = experiment_redesign(slug, cur, base, "ante_bestcase", 0, dry=dry)
        if not rd.get("feasible"):
            _write_exploop(slug, base, {"expid": base, "status": "HONEST_CONCEDE",
                                        "reason": "ante_insufficient_infeasible", "chain": chain,
                                        "why": rd.get("why_cannot_persuade")}, dry)
            return {"expid": base, "status": "HONEST_CONCEDE", "reason": "ante_insufficient_infeasible"}
        cur = rd["new_experiment_request"]

    best = None
    for it in range(1, max_iter + 1):
        eid = cur.get("expid") or cur.get("id") or base
        _queue_upsert(slug, cur, dry)                # so r4_run reads the (possibly redesigned) request
        edir = f"{ROOT}/campaigns/{slug}/experiments/{eid}"
        run_stage("r4_experiment_run.md", {"SLUG": slug, "EXPID": eid},
                  f"{edir}/results.json", sandbox="danger-full-access", effort="high", timeout=3000, dry=dry)
        data_source = cur.get("data_source") or cur.get("data_source_path") or ""
        man = f"{edir}/manifest.json"
        if os.path.exists(man):
            try:
                data_source = json.load(open(man)).get("data_source_path", data_source)
            except Exception:
                pass
        acc = accept_experiment(slug, eid, data_source or "(see manifest.data_source_path)", dry=dry)
        # v0.7: two-phase -- expensive origin audit once, then cheap re-check when driver+data unchanged
        if str(acc.get("verdict", "")).upper() == "REJECT":   # honesty/run failure, not a persuasion miss
            chain.append({"iter": it, "expid": eid, "accept": "REJECT"})
            _write_exploop(slug, base, {"expid": base, "status": "HONEST_CONCEDE",
                                        "reason": "accept_reject", "final": eid, "chain": chain}, dry)
            return {"expid": base, "status": "HONEST_CONCEDE", "reason": "accept_reject", "final": eid}

        pers = experiment_persuasion(slug, eid, card, dry=dry)
        overall = (pers or {}).get("overall", "NONE")
        chain.append({"iter": it, "expid": eid, "accept": acc.get("verdict"), "persuasion": overall})
        log(f"  iter{it} {eid}: accept={acc.get('verdict')} persuasion={overall}")
        best = eid
        if overall == "STRENGTH":                    # ONLY STRENGTH stops (user policy)
            _write_exploop(slug, base, {"expid": base, "status": "WON", "final": eid, "chain": chain}, dry)
            return {"expid": base, "status": "WON", "final": eid}
        if it == max_iter:
            break
        rd = experiment_redesign(slug, cur, eid, "post_result", it, dry=dry)   # WHY + HOW -> stronger design
        if not rd.get("feasible"):
            _write_exploop(slug, base, {"expid": base, "status": "HONEST_CONCEDE",
                                        "reason": "redesign_infeasible", "final": eid, "chain": chain,
                                        "why": rd.get("why_cannot_persuade")}, dry)
            return {"expid": base, "status": "HONEST_CONCEDE", "reason": "redesign_infeasible", "final": eid}
        cur = rd["new_experiment_request"]

    _write_exploop(slug, base, {"expid": base, "status": "HONEST_CONCEDE", "reason": "max_iter",
                                "final": best, "chain": chain}, dry)
    return {"expid": base, "status": "HONEST_CONCEDE", "reason": "max_iter", "final": best}


def route_strategies(strategies, rev):
    """Return an **ordered ladder** from the route section of MANIFEST (which one writes first, and which writes next if it fails).

    Why a ladder rather than "pick one": empirical results cannot identify the best by either quality or cost
    (see the evidence in reviewer_loop), so do not pretend selection is possible — use a defensible default order,
    stop once the gate clears, and proceed down the ladder only after failure. The gain comes from "writing fewer," not from "picking correctly."
    """
    by_id = {s["id"]: s for s in strategies}
    mf = {}
    try:
        mf = json.load(open(os.path.join(HARNESS, "strategies", "MANIFEST.json"))).get("route") or {}
    except Exception:
        pass
    oa = rev.get("initial_overall")
    order = (mf.get("by_zone") or {}).get(str(oa)) or mf.get("default_ladder") or []
    ladder = [by_id[i] for i in order if i in by_id]
    ladder += [s for s in strategies if s["id"] not in {x["id"] for x in ladder}]   # Fallback: append all unlisted strategies
    return ladder


def reviewer_loop(slug, rev, max_iter, dry=False, want_strategies=None):
    strategies = load_strategies()
    # #20: validate the MoE roster up front -- missing prompt files or a count mismatch vs the
    # card's n_strategies must be surfaced, not silently tolerated.
    for s in strategies:
        pf = os.path.join(HARNESS, "strategies", s["prompt_file"])
        if not os.path.exists(pf):
            log(f"  MoE WARNING: strategy {s['id']} prompt file missing: {pf}")
    if want_strategies and len(strategies) != int(want_strategies):
        log(f"  MoE WARNING: card.n_strategies={want_strategies} but {len(strategies)} enabled in MANIFEST")
    expected = len(strategies)
    dd = f"{ROOT}/campaigns/{slug}/drafts"
    if not dry:
        os.makedirs(dd, exist_ok=True)
    seed = "None"
    best_ever = None                              # (rank, sid, draft) -- GLOBAL best across rounds (H15)
    for rnd in range(1, max_iter + 1):
        rdir = f"{dd}/round{rnd}"
        if not dry:
            os.makedirs(rdir, exist_ok=True)
        # ★ Strategy-level lazy ladder (③ routing + ④ cost optimization, combined into the same problem)
        # Previously: write **all N strategies** every round, then select the best. Based on empirical cost.jsonl data (01-wdData):
        #   · Writing 447k in/call vs judge 16k in/call → **writing accounts for 94% of token**, judge 6%.
        #     Thus "write all N" is the sole dominant cost; the judge cascade optimizes only a fraction of that 6%.
        #   · 9/9 cleared the zone bar (criterion saturation) → quality cannot distinguish the strategies.
        #   · Strategy costs differ by only 8% → cost cannot distinguish them either.
        #   ⇒ There is no evidence for "which one to pick," but the benefit of "writing fewer" is certain: N 3→1 saves 63% of total token.
        # Therefore: write the first on the ladder → stop immediately if it clears the gate; write the next only if it fails. The unwritten strategies are the savings.
        # `--fanout-all` restores the old behavior (write all strategies only for strategy-comparison evaluations).
        ladder = strategies if FANOUT_ALL else route_strategies(strategies, rev)
        log(f"  strategy ladder{' (FANOUT_ALL writes all)' if FANOUT_ALL else ''}: "
            f"{' → '.join(s['id'] for s in ladder)}")
        drafts, cand, records, picked = [], [], {}, None
        for s in ladder:
            out = f"{rdir}/{rev['id']}__{s['id']}.md"
            run_stage("r6_write.md",
                      {"SLUG": slug, "REVIEWER": rev["id"], "STRATEGY_FILE": f"strategies/{s['prompt_file']}",
                       "STRATEGY_ID": s["id"], "N": rnd, "SEED": seed},
                      out, effort=WRITE_EFFORT, timeout=1200, dry=dry)
            if dry:
                continue
            if not os.path.exists(out):          # #20: failure to write even the first ladder entry must be surfaced, never silent
                log(f"  MoE WARNING: round{rnd} {rev['id']} strategy {s['id']} produced no draft")
                continue
            d = open(out).read()
            drafts.append((s["id"], d))
            ce = cheap_eval(slug, rev, d)
            cand.append((s["id"], d, ce))
            if best_ever is None or ce["rank"] > best_ever[0]:      # H15 global best-so-far
                best_ever = (ce["rank"], s["id"], d)
            # H17: retain a judgment for every strategy **actually written**; unwritten strategies farther down the ladder have no record — this is by design,
            # not data loss (the ladder field in the gate ledger records the complete ladder and how many levels were actually traversed).
            records[s["id"]] = {"strategy": s["id"], "ammo_hits": ce["ammo"], "deepseek": ce["ds"],
                                "ds_ok": ce["ds_ok"], "codex": None, "consensus": None,
                                "codex_run": False, "stop": False}
            if not ce["ds_ok"]:
                continue                         # Cheap gate rejects → write the next strategy directly, without spending an authoritative-judge call
            g = gate(slug, rev, d)
            records[s["id"]].update(codex=g.get("codex"), consensus=g.get("consensus") or None,
                                    codex_run=True, stop=bool(g.get("stop")))
            if g.get("judge_error"):
                records[s["id"]]["judge_error"] = g["judge_error"]
            if picked is None or g.get("stop"):
                picked = (s["id"], d, g)
            if g.get("stop"):
                saved = len(ladder) - len(drafts)
                if saved > 0:
                    log(f"    cost routing: {s['id']} cleared the gate → saved {saved} writing calls (≈447k in token each)")
                break                            # ← This line is where the 2/3 savings occur
        if dry or not drafts:
            return {"reviewer": rev["id"], "status": "DRY" if dry else "NO_DRAFT", "round": rnd}
        if picked is None:                       # None qualified for the authoritative judge → take the highest-ranked by the cheap gate
            sid0, d0, ce0 = max(cand, key=lambda x: x[2]["rank"])
            picked = (sid0, d0, {"stop": False, "ds": ce0["ds"], "ammo": ce0["ammo"], "consensus": {}})

        sid, best, g = picked
        route, route_reason = route_back(g)      # H13: typed route-back
        json.dump({"round": rnd, "reviewer": rev["id"], "oa": rev.get("initial_overall"),
                   "picked": sid, "stop": bool(g.get("stop")), "ammo": len(g.get("ammo") or []),
                   # ★ M2 lesson: the old gate ledger recorded only {round,picked,stop,ammo}, without per-strategy scores,
                   # and did not record the criterion version — causing NAFY's old bar judgment to become unidentifiable stale data.
                   # Now persist family identity together with the harness version, so every record carries a traceable criterion identity.
                   # Ladder audit trail: complete order + number of levels actually written — this distinguishes "unwritten strategy has no record" from "data loss"
                   "ladder": [x["id"] for x in ladder], "written": [d[0] for d in drafts],
                   "fanout_all": FANOUT_ALL,
                   "cross_family": (not NO_DEEPSEEK),
                   "degraded": ("no-deepseek:single-family" if NO_DEEPSEEK else None),
                   "gate_sha": GATE_SHA,
                   "route_back": {"stage": route, "reason": route_reason},
                   "candidates": records},
                  open(f"{ROOT}/campaigns/{slug}/ledger/round{rnd}-{rev['id']}-gate.json", "w"),
                  ensure_ascii=False, indent=1)
        if g["stop"]:
            wpath = f"{rdir}/{rev['id']}__{sid}.md"
            b2 = b2_faithfulness(slug, rev["id"], wpath, dry)   # H5: no-fabrication semantic gate
            amm = ammo_gate(slug, rev["id"], wpath, dry)        # B3: anti-self-harm semantic gate
            b2_ok = str(b2.get("verdict", "")).upper() == "PASS"
            amm_ok = str(amm.get("verdict", "")).upper() == "CLEAN"
            if b2_ok and amm_ok:
                open(f"{dd}/{rev['id']}.md", "w").write(best)
                return {"reviewer": rev["id"], "round": rnd, "strategy": sid,
                        # Degraded mode must never report PASS: that would let a single-family result be mistaken for a genuine cross-family ACQUIT
                        "status": ("PASS_SINGLE_FAMILY" if NO_DEEPSEEK else "PASS"),
                        "cross_family": (not NO_DEEPSEEK)}
            # Cleared raise/strength but blocked before PASS by fabrication (B2) and/or ammunition (B3).
            # Fix in the same class as #24 (silent truncation): fab[:300] / ammo_fix[:400] previously removed
            # most judge findings silently — one B3 run yields 5 hits, each with a quote (~95 characters) + rewrite advice;
            # 400 characters can hold only 1-2 hits, and the remainder never reaches the writer in the next round, guaranteeing a wasted loop.
            # Now: enlarge the budget enough to hold complete feedback, and truncation must be **logged explicitly** (never silently).
            fab = join_budget((b2.get("unsupported_claims") or []) + (b2.get("invented_citations") or [])
                               + (b2.get("reasons") or []), 3000, "B2") if not b2_ok else ""
            # ★ Sort before packing: blocking categories (B3_BLOCKING) must enter the seed first; only advisory categories
            # (not_direct/deletable) may be dropped. The unit test found 12 hits
            # /4305 characters after union-of-3; increasing the budget alone cannot fit them all — important items must come first.
            _hits = sorted((amm.get("hits") or []),
                           key=lambda h: 0 if str(h.get("category", "")).strip() in B3_BLOCKING else 1)
            ammo_fix = join_budget([f"\"{h.get('quote','')}\" -> {h.get('rewrite','')}"
                                    for h in _hits], 6000, "B3") if not amm_ok else ""
            log(f"    PASS BLOCKED on {sid}: {'B2-fabrication ' if not b2_ok else ''}"
                f"{'B3-ammunition('+str(len(amm.get('hits') or []))+')' if not amm_ok else ''}")
            adv = (f"[B2 FABRICATION] Remove/ground: {fab}. " if fab else "") + \
                  (f"[B3 AMMUNITION] Rewrite these, keep the facts: {ammo_fix}" if ammo_fix else "")
            seed = json.dumps({"prior_best_rebuttal": best, "apply_advice": adv,
                               "avoid_phrases": [], "route_back": "r6",
                               "route_reason": "B2/B3 pre-PASS gate"}, ensure_ascii=False)
            continue
        if route != "r6":                         # H13: an evidence/diagnosis gap won't be fixed by rewriting
            log(f"    route-back: {route_reason} (loop still re-rolls r6 with best-so-far; flagged for {route})")
        adv = (g.get("consensus", {}) or {}).get("advice") or g["ds"].get("advice") or ""
        seed = json.dumps({"prior_best_rebuttal": best_ever[2],   # carry the GLOBAL best forward
                           "apply_advice": adv, "avoid_phrases": g["ammo"],
                           "route_back": route, "route_reason": route_reason}, ensure_ascii=False)
    # max_iter reached -> honest concede with the GLOBAL best-so-far (H15)
    if best_ever and not dry:
        open(f"{dd}/{rev['id']}.md", "w").write(best_ever[2])
    return {"reviewer": rev["id"], "status": "HONEST_CONCEDE", "round": max_iter,
            "best_strategy": best_ever[1] if best_ever else None}


# ---- paper driver -----------------------------------------------------------

def run_paper(slug, from_stage="r0a", dry=False):
    camp = f"{ROOT}/campaigns/{slug}"
    if not dry:                                   # H11: dry-run must not touch the filesystem
        for d in ("ledger", "drafts", "evidence", "experiments"):
            os.makedirs(f"{camp}/{d}", exist_ok=True)
    order = ["r0a", "r1", "r2", "r3", "r4", "r5", "r6r7", "mt", "ac"]
    do = order[order.index(from_stage):] if from_stage in order else order
    log(f"=== paper {slug} (stages: {do}) ===")

    if "r0a" in do:
        run_stage("r0a_extract_card.md", {"SLUG": slug}, f"{camp}/REBUTTAL_CARD.json",
                  effort="high", dry=dry)
    if "r1" in do:
        run_stage("r1_evidence_map.md", {"SLUG": slug}, f"{camp}/ledger/evidence_map.json", dry=dry)
    if "r2" in do:
        run_stage("r2_diagnose.md", {"SLUG": slug}, f"{camp}/ledger/concern_ledger.json", dry=dry)
        # H6: B1 concern-diagnosis gate -- a bad concern map must not reach writing.
        run_stage("b1_concern_gate.md", {"SLUG": slug}, f"{camp}/ledger/B1_concern_gate.json",
                  sandbox="read-only", effort="high", dry=dry)
        b1p = f"{camp}/ledger/B1_concern_gate.json"
        if not dry and os.path.exists(b1p):
            try:
                b1 = json.load(open(b1p))
                if str(b1.get("verdict", "")).upper() == "FAIL":
                    log(f"  B1 FAIL: concern map deficient -> re-diagnose r2. reasons={b1.get('reasons')}")
            except Exception:
                pass
    if "r3" in do:
        run_stage("r3_triage_feasibility.md", {"SLUG": slug}, f"{camp}/ledger/experiment_queue.json", dry=dry)

    card = json.load(open(f"{camp}/REBUTTAL_CARD.json")) if os.path.exists(f"{camp}/REBUTTAL_CARD.json") else {}
    allow_exp = bool(card.get("allow_new_experiments", True))   # #21: card can forbid new experiments
    if "r4" in do and not allow_exp:
        log("  r4 skipped: card.allow_new_experiments is false (no new experiments this campaign)")
    # EXPERIMENT GOAL LOOP: drive each queued request to STRENGTH or honest concession. Each request
    # goes ANTE guard (needed? best-case persuasive?) -> (run -> X1-X6 accept -> S-exp persuade ->
    # redesign)* until the persuasion gate says STRENGTH, or redesign is infeasible / max_iter hits ->
    # HONEST_CONCEDE with the best REAL result (never relabeled). See EXPERIMENT_LOOP.md.
    exp_results = []
    if "r4" in do and allow_exp:
        reqs = []
        qp = f"{camp}/ledger/experiment_queue.json"
        if os.path.exists(qp):
            try:
                raw = json.load(open(qp))
                reqs = raw if isinstance(raw, list) else (raw.get("experiments") or [])
            except Exception:
                reqs = []
        for req in reqs:
            exp_results.append(experiment_loop(slug, req, card, dry=dry))
        if exp_results and not dry:
            json.dump(exp_results, open(f"{camp}/ledger/experiment_loop_results.json", "w"),
                      ensure_ascii=False, indent=1)

    # Seeded experiments (ACCEPTANCE on disk, no queue request -> can't auto-rerun): still run the
    # S-exp persuasion gate once so r5 gets a verdict. The loop above covers queued/redesignable ones.
    if ("r4" in do or "r5" in do) and allow_exp and os.path.isdir(f"{camp}/experiments"):
        looped = {r.get("expid") for r in exp_results} | {r.get("final") for r in exp_results}
        for eid in sorted(os.listdir(f"{camp}/experiments")):
            ed = f"{camp}/experiments/{eid}"
            if (os.path.exists(f"{ed}/ACCEPTANCE.json") and eid not in looped
                    and not os.path.exists(f"{ed}/PERSUASION.json")):
                p = experiment_persuasion(slug, eid, card, dry=dry)
                if p:
                    log(f"  persuasion(seeded) {eid}: {p['overall']} {[t['verdict'] for t in p['targets']]}")

    # H12: r5 merges ONLY accepted experiments into a single evidence pool that r6 reads.
    if "r5" in do and os.path.exists(f"{camp}/ledger/evidence_map.json"):
        run_stage("r5_evidence_merge.md", {"SLUG": slug}, f"{camp}/ledger/evidence_pool.json",
                  sandbox="workspace-write", effort="high", dry=dry)

    # ★ Driver-level hard gate (added after the 2026-09-29, 01-wdData/37ch failure): r6 must never write without evidence_pool.
    # The fail-closed language in the stage prompt is only an **instruction to the engine**, which the engine may disobey;
    # the only reliable enforcement is here.
    # Root cause: r6_write.md / b2 both said "fall back to evidence_map.json if evidence_pool is absent," but
    # evidence_map is the **unfiltered** evidence base produced by r1 (no evidence_status, REJECT experiments not removed).
    # Empirical consequence: the 37ch draft wrote "our overlap stress test measured" for 01-E-overlap,
    # but that experiment had ACCEPTANCE=REJECT → B2 judged FAIL, and the entire round ended in HONEST_CONCEDE.
    if "r6r7" in do:
        pool = f"{camp}/ledger/evidence_pool.json"
        if not os.path.exists(pool):
            emap = f"{camp}/ledger/evidence_map.json"
            if os.path.exists(emap):
                log(f"  evidence_pool.json missing → backfill with r5_evidence_merge (r6 must not write from unfiltered evidence)")
                run_stage("r5_evidence_merge.md", {"SLUG": slug}, pool,
                          sandbox="workspace-write", effort="high", dry=dry)
            if not os.path.exists(pool) and not dry:
                log(f"FATAL: {slug} has no evidence_pool.json and backfill failed — refusing to run r6r7."
                    f" Unfiltered evidence would present a REJECT experiment as completed evidence (see the 37ch empirical result)."
                    f" Fix r5_evidence_merge before retrying.")
                return []

    results = []
    if "r6r7" in do:
        targets = card.get("target", {})
        want = set(targets.get("require_raise_on", [])) | set(targets.get("maintain", []))
        max_iter = int(MAX_ITER_OVERRIDE or card.get("max_iter", 4))   # --max-iter: cost control, without changing the contract file
        n_strat = card.get("n_strategies")           # #20: reconcile card roster with MANIFEST
        for rev in card.get("reviewers", []):
            if rev["id"] in want or not want:
                log(f"-- reviewer {rev['id']} (OA={rev.get('initial_overall')}) --")
                results.append(reviewer_loop(slug, rev, max_iter, dry=dry, want_strategies=n_strat))
        if not dry:                               # H11: never clobber real loop_results.json on a dry run
            json.dump(results, open(f"{camp}/ledger/loop_results.json", "w"), ensure_ascii=False, indent=1)
    # ② Multi-turn exchange: pre-delivery stress test. **Not a gate** — does not affect the r6r7 PASS judgment;
    # outputs "which claim collapses under follow-up," for narrowing in r6 or inclusion in the honest-concede list.
    # Run only for reviewer entries with a completed final draft (there is nothing to stress-test without a draft).
    if "mt" in do:
        targets = card.get("target", {})
        want = set(targets.get("require_raise_on", [])) | set(targets.get("maintain", []))
        for rev in card.get("reviewers", []):
            if want and rev["id"] not in want:
                continue
            final = f"{camp}/drafts/{rev['id']}.md"
            if not os.path.exists(final) and not dry:
                log(f"  mt {rev['id']}: no final draft ({final}), skipping")
                continue
            multiturn_exchange(slug, rev, final, dry=dry)

    # H18: AC meta-comment + package (was in `order` but had no branch -> silent no-op)
    if "ac" in do and os.path.exists(f"{camp}/ledger/loop_results.json"):
        run_stage("ac_package.md", {"SLUG": slug}, f"{camp}/AC_COMMENT.md",
                  sandbox="workspace-write", effort="high", dry=dry)
    log(f"=== {slug} done: {results} ===")
    return results


def main():
    global MODEL, JUDGE_MODEL, WRITE_EFFORT, JUDGE_EFFORT, MAX_ITER_OVERRIDE, NO_DEEPSEEK, FANOUT_ALL, B3_REPEATS, MT_ROUNDS
    # SPEC<->IMPL guard: bar_met/consensus must still implement GOAL.md's zone predicate.
    # Fail CLOSED at startup on drift (e.g. someone edits GOAL.md but not the gate, or vice-versa)
    # rather than mis-judging a whole overnight run. gate content is pinned via GATE_SHA (#27).
    try:
        cg._selfcheck()
        log(f"GOAL.md<->gate consistency OK (gate {GATE_SHA})")
    except AssertionError as e:
        log(f"FATAL: {e}")
        log("Refusing to run: consensus_gate no longer matches GOAL.md's zone table. "
            "Re-align bar_met/consensus with harness/GOAL.md (and update the self-check).")
        sys.exit(2)
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--from", dest="from_stage", default="r0a")
    ap.add_argument("--model", default=None, help="WRITER engine model override, e.g. gpt-5.5")
    ap.add_argument("--judge-model", default=JUDGE_MODEL,
                    help="authoritative Codex JUDGE model (must differ from --model; anti-Goodhart)")
    ap.add_argument("--write-effort", default="high")
    ap.add_argument("--judge-effort", default="xhigh")
    ap.add_argument("--mt-rounds", type=int, default=None,
                    help="② maximum number of rounds in the multi-turn exchange (default 3; stop early at saturation when a follow-up is not novel)")
    ap.add_argument("--b3-repeats", type=int, default=None,
                    help="number of consecutive B3 runs whose hit union is taken (default 3; empirically measured single-run miss rate ~20%%)")
    ap.add_argument("--fanout-all", action="store_true",
                    help="restore old behavior: write all N strategies every round (3× more expensive; use only for strategy-comparison evaluations)")
    ap.add_argument("--no-deepseek", action="store_true",
                    help="single-family degradation: use only the codex judge when DeepSeek is unavailable (loses the cross-family consensus gate; output marked degraded)")
    ap.add_argument("--max-iter", type=int, default=None,
                    help="override the card's max_iter (cost control; 1-2 recommended for validation runs)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    MODEL, JUDGE_MODEL = a.model, a.judge_model
    WRITE_EFFORT, JUDGE_EFFORT = a.write_effort, a.judge_effort
    MAX_ITER_OVERRIDE = a.max_iter
    NO_DEEPSEEK = a.no_deepseek
    FANOUT_ALL = a.fanout_all
    if a.b3_repeats:
        B3_REPEATS = a.b3_repeats
    if a.mt_rounds:
        MT_ROUNDS = a.mt_rounds
    if FANOUT_ALL:
        log("⚠️ --fanout-all: write all N strategies every round; writing cost ×N (empirically ≈447k in token per call).")
    if NO_DEEPSEEK:
        log("⚠️ Single-family degraded mode (--no-deepseek): the cross-family consensus gate does not hold; GOAL.md inviolable rule #4 is abandoned."
            "The judge still ≠ the writer (H1 preserved). All output is marked cross_family=false / status=PASS_SINGLE_FAMILY,"
            "and must not be used as a genuine ACQUIT.")
    if MODEL and JUDGE_MODEL and MODEL == JUDGE_MODEL:
        log(f"WARNING: writer MODEL == JUDGE_MODEL ({MODEL}); family-B independence collapses "
            f"(anti-Goodhart weakened). DeepSeek is still cross-family, but pin a distinct --judge-model.")
    log(f"writer={MODEL or 'codex-default'} judge={JUDGE_MODEL} | write={WRITE_EFFORT} judge={JUDGE_EFFORT}")
    papers = _runnable_campaigns() if a.all else [a.paper]
    for slug in papers:
        if slug:
            run_paper(slug, a.from_stage, dry=a.dry_run)


def _runnable_campaigns():
    """#26: --all runs only campaigns that have BOTH a REBUTTAL_CARD.json and a matching
    papers/<slug> input. Demo/archive dirs (e.g. demo-argument-compiler) are excluded, with
    the reason logged -- never silently swept into a real run."""
    runnable = []
    for d in sorted(os.listdir(f"{ROOT}/campaigns")):
        cdir = f"{ROOT}/campaigns/{d}"
        if not os.path.isdir(cdir):
            continue
        has_card = os.path.exists(f"{cdir}/REBUTTAL_CARD.json")
        has_paper = os.path.isdir(f"{ROOT}/papers/{d}")
        if has_card and has_paper:
            runnable.append(d)
        else:
            missing = [m for m, ok in (("REBUTTAL_CARD.json", has_card), (f"papers/{d}", has_paper)) if not ok]
            log(f"  --all skip campaign '{d}': missing {', '.join(missing)}")
    return runnable


if __name__ == "__main__":
    main()
