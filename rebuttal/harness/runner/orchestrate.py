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

# 可移植:默认由本文件位置推出仓库根(harness/runner/ → ../../),
# 可用 AUTOREBUTTAL_ROOT 覆盖。此前是硬编码的绝对路径,无法发布也无法换机部署。
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
import cost                             # noqa: E402  M1 成本仪表(独立模块;绝不改冻结包)
_COST_PROBE = cost.install_deepseek_probe()   # DeepSeek token 在客户端工厂上拦截;失败静默降级


MAX_ITER_OVERRIDE = None  # --max-iter:临时压低 goal 循环轮数(省额度),不改 REBUTTAL_CARD.json
B3_REPEATS = 3           # --b3-repeats:B3 连跑次数,取命中**并集**。见 ammo_gate 的实测依据。
FANOUT_ALL = False       # --fanout-all:恢复旧的"每轮把 N 个策略全写一遍"(只在做策略对比评测时用)。
                         # 默认走策略级惰性阶梯,见 reviewer_loop 里的成本依据。
NO_DEEPSEEK = False      # --no-deepseek:单家族降级模式。DeepSeek 不可用(余额/网络)时的退路。
                         # ⚠ 这会**丢掉 GOAL.md 不可违反 #4(跨家族合议)** —— 只剩 OpenAI 一家,
                         # 判官与写手同家族,反 Goodhart 的核心保险失效。仍保住 H1(判官模型 ≠ 写手模型)。
                         # 因此该模式下:① 每条 gate 记录打 cross_family=false + degraded
                         # ② 循环状态是 PASS_SINGLE_FAMILY,不是 PASS —— 绝不让降级产物被当成真 ACQUIT。
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

    M1: `--json` 让 codex 把事件以 JSONL 打到 stdout(此前是 DEVNULL,token 被丢掉),
    从 turn.completed.usage 取 token 记进成本账本。`-o <rc>` 仍是唯一的 receipt 来源,
    所以加 --json 不改变返回值语义(已实测)。stage/slug/unit/role 只用于记账。"""
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
    """便宜档判官。返回 (judgment, bar_met)。

    NO_DEEPSEEK 下返回 (None, None) —— 本机 codex 用 ChatGPT 账号登录,
    `gpt-5.3-codex-spark` 报 400 "not supported when using Codex with a ChatGPT account",
    可用模型只剩 gpt-5.5(写手)/ gpt-5.6-sol(判官),**没有更便宜的档**,
    所以级联的便宜层直接消失,不是换个模型就能补上。调用方须按降级路径处理。"""
    if NO_DEEPSEEK:
        return (None, None)
    with cost.timed() as _t:
        j = cg.deepseek_judge(case, template="auto")
    ok, _ = cg.bar_met(j, case)
    _rec_ds(_t, slug, unit, stage, j, cheap_reject=not ok)
    return (j, ok)


def _rec_ds(t, slug, unit, stage, ds, cheap_reject=None):
    """记一次 DeepSeek 判官调用。token 来自 cost 探针(装不上则为 None,只留 wall)。"""
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
    # M1 记账归属:槽位里已有 SLUG/REVIEWER,无需改调用方
    _slug = slots.get("SLUG") or slots.get("PAPER")
    _unit = slots.get("REVIEWER") or slots.get("EXPID") or slots.get("RID")
    _strat = slots.get("STRATEGY_ID")        # MoE:同 reviewer 多策略,必须分开记账
    _role = "ACQUIT" if model else "DRIVE"   # model 只在判官阶段(b2/b3)被显式指定
    meta_path = output_path + ".stagemeta"
    if os.path.exists(output_path):
        old = open(meta_path).read().strip() if os.path.exists(meta_path) else None
        if old is None:                          # legacy real output -> adopt, never clobber
            if not dry:
                open(meta_path, "w").write(sig)
            log(f"  skip {stage} (adopt existing: {os.path.basename(output_path)})")
            if not dry:                          # H11: dry-run 零副作用,账本也不许写
                cost.record(slug=_slug, unit=_unit, stage=stage, role=_role, strategy=_strat,
                            cache_hit=True, wall_s=0.0, verdict="adopt_existing")
            return True
        if old == sig:
            log(f"  skip {stage} (up-to-date: {os.path.basename(output_path)})")
            if not dry:                          # H11
                cost.record(slug=_slug, unit=_unit, stage=stage, role=_role, strategy=_strat,
                            cache_hit=True, wall_s=0.0, verdict="up_to_date")   # 省下的整次引擎调用
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
        # 单家族降级:只有一个家族,cg.consensus 的跨家族语义不成立 —— 不去伪造它,
        # 而是显式构造一个标着 cross_family=false 的判定,下游一眼能看出这不是真合议。
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
        # 降级:没有便宜档判官 → 排序只剩免费的弹药正则,且所有稿都对贵判官开放
        # (便宜门消失 = cheap-first 省钱机制失效,成本会上升。这是降级的代价,不掩盖。)
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


# b3_ammunition_gate.md §2/§6 的明文规则:A–E 命中拦 PASS(E 另标 red_line);
# deletable / not_direct 仅为建议,不拦。裁决在**代码里**算,不再依赖判官自报 verdict ——
# 判官漏检时它会连带报出 CLEAN,而并集里可能已有别的 trial 抓到的拦截类命中。
B3_BLOCKING = {"A", "B", "B2", "C", "C2", "D", "E"}
B3_ADVISORY = {"deletable", "not_direct"}


def _b3_key(h):
    """命中去重键:类别 + 引文前 120 字(同一句在不同 trial 里可能被截得略有出入)。"""
    return (str(h.get("category", "")).strip(),
            " ".join(str(h.get("quote", "")).split())[:120].lower())


def ammo_gate(slug, rev_id, draft_path, dry=False, repeats=None):
    """B3 semantic anti-self-harm gate -- the AUTHORITATIVE ammunition check, replacing the
    static regex. An independent judge (distinct model) READS the draft and finds self-exposure /
    empty promises / over-concession / performative honesty / fabrication by MEANING, not pattern
    (regex can't tell 'we will revise X' from 'the revised X reads: ...'). HAS_AMMO blocks PASS.

    ★ union-of-N(2026-09-29 复现性测量后)。同一份稿(sha 不变)判 10 次的实测:
      · **裁决不飘**:判官忠实执行 §2/§6 —— 10/10 都是"有拦截类命中就 HAS_AMMO"。
      · **飘的是检出**:同一处实质过度声称(D 类),medium 档 3/5 次被发现、
        xhigh 档 4/5 次;n_hits 在 1–7 之间。跑得快的那几次就是漏掉的那几次。
      ⇒ 这是纯 recall 问题,不是判准问题。连跑 N 次取**并集**:漏检率 0.2^N
        (N=3 → 0.8%)。B3 单次仅 ≈88k token,跑 3 次仍比 B2 单次 780k 便宜。
      门本应偏向 recall:漏掉弹药(稿子带着夸大发出去)的代价远大于误报一条(多改一句)。
    """
    out = f"{ROOT}/campaigns/{slug}/ledger/B3_{rev_id}_ammunition.json"
    if dry:
        return {"verdict": "CLEAN", "dry": True}
    n = int(repeats or B3_REPEATS)
    merged, trials = {}, []
    for i in range(1, n + 1):
        for p in (out, out + ".stagemeta"):      # 每次都必须真跑(draft 每轮会变 + 本身要重复采样)
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
            merged.setdefault(_b3_key(h), h)     # 并集去重
    hits = list(merged.values())
    blocking = [h for h in hits if str(h.get("category", "")).strip() in B3_BLOCKING]
    res = {"verdict": "HAS_AMMO" if blocking else "CLEAN",
           "red_line": any(str(h.get("category", "")).strip() == "E" for h in hits),
           "hits": hits, "n_hits": len(hits), "n_blocking": len(blocking),
           # 留痕:让"某次漏检"事后可查,也让 union 的收益可度量
           "union_of": n, "effort": "xhigh", "judge_model": JUDGE_MODEL, "trials": trials}
    disagree = {t["judge_verdict"] for t in trials}
    if len(disagree) > 1:
        log(f"    B3 union-of-{n}: 各次判官自报不一致 {sorted(disagree)} "
            f"(n_hits={[t['n_hits'] for t in trials]}) → 按并集裁决 {res['verdict']}")
    json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
    return res


def _b3_run_once(slug, rev_id, draft_path):
    out = f"{ROOT}/campaigns/{slug}/ledger/B3_{rev_id}_ammunition.json"
    run_stage("b3_ammunition_gate.md",
              {"SLUG": slug, "REVIEWER": rev_id, "DRAFT_PATH": draft_path},
              # effort: medium → xhigh(2026-09-29 复现性测量后)。B3 是唯一需要**逐句通读全文
              # 找语义弹药**的门 —— 纯 recall 任务,最吃推理预算,却曾是三道门里配额最低的
              # (r7 xhigh / B2 high / B3 medium)。实测同一份稿 7 次判定 3 CLEAN / 4 HAS_AMMO,
              # 检出数在 1–6 之间飘,且**跑得快的那几次就是漏掉的那几次**(55s→找到1-2条,
              # 74-110s→找到6条)。模型三门相同(gpt-5.6-sol),故 effort 是唯一可动的自变量。
              # timeout 同步 400→900:medium 下深审已用 110s,xhigh 超 400s 会变成自制的超时失败。
              out, sandbox="workspace-write", effort="xhigh", timeout=900,
              model=JUDGE_MODEL)                 # semantic judge, distinct from the writer


def join_budget(items, budget, what="feedback", logger=None):
    """把判官的发现拼进 carry-forward seed,**超预算必须出声**。

    病根(#24 同类):原先 fab[:300] / ammo_fix[:400] 直接截断 —— B3 一次给 5-6 条
    命中,每条含引文(~95 字符)+ 改写建议,400 字符只装得下 1-2 条,**剩下的在
    下一轮根本传不到写手手里**,循环注定清不完。而且静默失效:表现为"循环效果不好",
    不是"出错了"。DESIGN_LOGIC §4 原则 2:截断必须出声。

    提到模块级是为了可单测 —— 原先是 reviewer_loop 里的闭包,改了也没法验。
    单测立刻抓到:B3 改 union-of-3 后命中从 5-6 涨到 **12 条 / 4305 字符**,
    2500 的预算只装得下 7 条 —— 两个改动相互作用,光加大预算不够。
    故调用方须**先按重要性排序**(拦截类在前,建议类可丢),本函数只负责装箱与告警。
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
        msg = (f"    note: {what} 反馈超预算,丢弃 {dropped}/{len(items)} 条"
               f"(budget={budget}) —— 下一轮收不到这些,考虑调大预算")
        (logger or log)(msg)
    return "; ".join(out)


MT_ROUNDS = 3            # --mt-rounds:多轮交锋的最大轮数
MT_NOVELTY_SIM = 0.5     # 轮间追问相似度上限;超过视为重问 → 饱和停机


def _rejected_expids(slug):
    """ACCEPTANCE.json 判定为 REJECT 的实验 —— 作者轮不得把它们列为证据。"""
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
    """② 多轮交锋模拟:审稿人追问 → 作者应答 → 再追问,最多 N 轮。

    现有产线只模拟**单轮**(判官读一遍给判定),这里模拟真实 discussion 期的往返。
    验证的不是"第一印象能不能过",而是"**稿子扛不扛得住追问**"。

    ★ 不是拦门。它不阻止 r7 判 PASS,产出的是"哪些 claim 在追问下塌掉",
      供回 r6 收窄、或进 honest-concede 清单。

    最小前提已实测(01-wdData/37ch):轮 2 追问与轮 1 相似度 0.03、锚在不同句,
    且轮 2 更要害(从"quality screen 是什么"推进到"重标定是否用了同轮标签"=数据泄漏)。
    对照组:换 persona 先验的做法相似度 0.74-0.80,已证伪。

    代码里强制的不变量(不依赖引擎自觉):
      · 审稿人 = JUDGE_MODEL(ACQUIT),作者 = 写手 MODEL(DRIVE),同模型则拒跑
      · evidence_pool 缺失则拒跑(否则作者轮会退回未过滤证据)
      · 新意判据在代码里算(相似度 + 锚句),不问引擎"这条新不新"
      · 红线检出:作者引入新数字 / 引用 REJECT 实验
    """
    import difflib
    rid = rev["id"]
    camp = f"{ROOT}/campaigns/{slug}"
    n = int(rounds or MT_ROUNDS)
    if MODEL and JUDGE_MODEL and MODEL == JUDGE_MODEL:
        log(f"  mt {rid}: 写手与判官同模型({MODEL}) → 拒跑。自问自答必然收敛到同意。")
        return {"status": "BLOCKED", "reason": "writer == judge"}
    if not dry and not os.path.exists(f"{camp}/ledger/evidence_pool.json"):
        log(f"  mt {rid}: evidence_pool.json 缺失 → 拒跑(作者轮会退回未过滤证据)")
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
        # sandbox 必须是 workspace-write:本 stage **声明了输出文件**,只读沙箱写不了。
        # (照抄 r7 判官的 read-only 是错的 —— r7 判官不写文件,判定从 receipt 解析。
        #  B2/B3 这类"要写判定文件的判官"用的就是 workspace-write。)
        run_stage("mt_reviewer_turn.md", slots, rv_out, sandbox="workspace-write", effort=JUDGE_EFFORT,
                  timeout=600, dry=dry, model=JUDGE_MODEL)
        if dry:
            continue
        try:
            rv = json.load(open(rv_out))
        except Exception:
            log(f"    mt r{r}: 审稿人轮无可解析输出 → 停"); break

        # ★ 新意判据在代码里算(DESIGN_LOGIC §4 原则 3:裁决归代码)
        fu = str(rv.get("followup", ""))
        qt = str(rv.get("quote", "")).strip()[:80].lower()
        sims = [difflib.SequenceMatcher(None, str(p["followup"]), fu).ratio() for p in prev]
        dup_quote = any(str(p["quote"]).strip()[:80].lower() == qt for p in prev)
        if prev and (max(sims) >= MT_NOVELTY_SIM or dup_quote):
            log(f"    mt r{r}: 追问不新(sim={max(sims):.2f} dup_quote={dup_quote}) → 饱和,停止")
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
            log(f"    mt r{r}: 作者轮无可解析输出 → 停"); break

        # 红线检出(代码判,不问引擎)
        newnums = [x for x in (au.get("new_numbers_introduced") or []) if str(x).strip()]
        badev = [e for e in (au.get("evidence_used") or []) if any(rj in str(e) for rj in rejected)]
        if newnums:
            red_flags.append({"round": r, "kind": "fabricated_numbers", "detail": newnums})
            log(f"    🔴 mt r{r}: 作者在压力下引入了不在证据池的数字 {newnums}")
        if badev:
            red_flags.append({"round": r, "kind": "cited_rejected_experiment", "detail": badev})
            log(f"    🔴 mt r{r}: 作者把 REJECT 的实验列为证据 {badev}")

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
            f"sim={round(max(sims),3) if sims else '-'} 锚句「{str(rv.get('quote'))[:40]}…」")

    # 塌掉的 claim = 作者让步或收窄之处 —— 这是本 stage 的真正产出
    collapsed = [e for e in exchange if e.get("conceded") or e.get("narrowed_claim")]
    res = {"reviewer": rid, "rounds_run": len([e for e in exchange if not e.get("saturated")]),
           "max_rounds": n, "saturated": any(e.get("saturated") for e in exchange),
           "collapsed_claims": collapsed, "red_flags": red_flags,
           "reviewer_model": JUDGE_MODEL, "author_model": MODEL or "codex-default",
           "exchange": exchange}
    if not dry:
        json.dump(res, open(f"{camp}/ledger/mt_{rid}_exchange.json", "w"),
                  ensure_ascii=False, indent=1)
    log(f"  mt {rid}: 跑了 {res['rounds_run']} 轮,{len(collapsed)} 处塌陷,"
        f"{len(red_flags)} 条红线{'(饱和提前停)' if res['saturated'] else ''}")
    return res


def route_back(g):
    """H13: type the failure so the loop routes to the RIGHT stage, not always r6-rewrite.
    evidence shortage -> r4 (run an experiment); concern misdiagnosed -> r2 (re-diagnose);
    else a text-level gap -> r6 (rewrite). Returns (stage, reason)."""
    ds = g.get("ds") or {}
    txt = " ".join(str(ds.get(k, "")) for k in ("blocker", "advice", "reasoning", "veto")).lower()
    if any(w in txt for w in ("need experiment", "needs experiment", "missing data", "no data",
                              "empirical evidence", "run an experiment", "additional experiment",
                              "ablation", "需要实验", "补实验", "缺数据", "缺证据")):
        return ("r4", "evidence shortage -> needs an experiment (r4), not a rewrite")
    if any(w in txt for w in ("misdiagnos", "wrong concern", "mischaracter", "misread",
                              "actually about", "真正的心结", "误判", "诊断错")):
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
    primary = "codex" if ds is None else cg.primary_judge(case)   # 降级:只剩 codex 一家,它就是主判
    if ds is None:
        ds_ok = True                                 # 无便宜档 → 不做便宜拒,直接上权威判官
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
    """ANTE guard (before any GPU run), '合议才拦' (conservative): per served concern, judge (a) the best
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
    concern 心结 + the failing result (or best-case) + the judge's WHY, emits WHY it cannot persuade + a
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
    """按 MANIFEST 的 route 段给出**有序阶梯**(先写谁、不过再写谁)。

    为什么是阶梯而不是"挑一个":实测既无法按质量也无法按成本挑出最优
    (见 reviewer_loop 的依据),所以不假装能挑 —— 用一个可辩护的默认顺序,
    过门就停,不过再往下走。收益来自"少写",不来自"挑对"。
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
    ladder += [s for s in strategies if s["id"] not in {x["id"] for x in ladder}]   # 兜底:补齐未列出的
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
        # ★ 策略级惰性阶梯(③ 路由 + ④ 成本优化,合并为同一个问题)
        # 此前:每轮把 N 个策略**全写一遍**再选最优。依据实测 cost.jsonl(01-wdData):
        #   · 写作 447k in/次 vs 判官 16k in/次 → **写作占 94% 的 token**,判官占 6%。
        #     所以"全写 N 个"是唯一的大头;级联判官优化的是那 6% 里的零头。
        #   · 9/9 全清分区 bar(判据饱和)→ 质量挑不出策略高下。
        #   · 策略间成本只差 8% → 成本也挑不出高下。
        #   ⇒ "挑哪个"无据可依,但"少写几个"收益确定:N 3→1 省 63% 的总 token。
        # 故:按阶梯写第一个 → 过门即停;不过才写下一个。省下的就是没写的那些。
        # `--fanout-all` 恢复旧行为(做策略对比评测时才需要全写)。
        ladder = strategies if FANOUT_ALL else route_strategies(strategies, rev)
        log(f"  策略阶梯{'(FANOUT_ALL 全写)' if FANOUT_ALL else ''}: "
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
            if not os.path.exists(out):          # #20: 阶梯首个就写不出来必须暴露,不静默
                log(f"  MoE WARNING: round{rnd} {rev['id']} 策略 {s['id']} 未产出 draft")
                continue
            d = open(out).read()
            drafts.append((s["id"], d))
            ce = cheap_eval(slug, rev, d)
            cand.append((s["id"], d, ce))
            if best_ever is None or ce["rank"] > best_ever[0]:      # H15 全局 best-so-far
                best_ever = (ce["rank"], s["id"], d)
            # H17: 每个**实际写出来**的策略都留判定;阶梯下未写的策略没有记录 —— 这是设计,
            # 不是丢数据(gate ledger 的 ladder 字段记下了完整阶梯与实际走到第几层)。
            records[s["id"]] = {"strategy": s["id"], "ammo_hits": ce["ammo"], "deepseek": ce["ds"],
                                "ds_ok": ce["ds_ok"], "codex": None, "consensus": None,
                                "codex_run": False, "stop": False}
            if not ce["ds_ok"]:
                continue                         # 便宜门拒 → 直接写下一个策略,不花权威判官
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
                    log(f"    成本路由:{s['id']} 过门 → 省下 {saved} 次写作(每次 ≈447k in token)")
                break                            # ← 省下的 2/3 就在这一行
        if dry or not drafts:
            return {"reviewer": rev["id"], "status": "DRY" if dry else "NO_DRAFT", "round": rnd}
        if picked is None:                       # 没有一个够格上权威判官 → 取便宜门排名最高的
            sid0, d0, ce0 = max(cand, key=lambda x: x[2]["rank"])
            picked = (sid0, d0, {"stop": False, "ds": ce0["ds"], "ammo": ce0["ammo"], "consensus": {}})

        sid, best, g = picked
        route, route_reason = route_back(g)      # H13: typed route-back
        json.dump({"round": rnd, "reviewer": rev["id"], "oa": rev.get("initial_overall"),
                   "picked": sid, "stop": bool(g.get("stop")), "ammo": len(g.get("ammo") or []),
                   # ★ M2 教训:旧 gate ledger 只记 {round,picked,stop,ammo},没有每策略分数,
                   # 也没记判据版本 —— 以致 NAFY 的旧 bar 判定成了无法识别的过期数据。
                   # 现在把家族性与 harness 版本一起落盘,让每条记录自带可追溯的判据身份。
                   # 阶梯留痕:完整顺序 + 实际写了几层 —— 这样"未写的策略没记录"可被区分于"丢数据"
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
                        # 降级模式绝不报 PASS:那会让单家族结果被误当成真的跨家族 ACQUIT
                        "status": ("PASS_SINGLE_FAMILY" if NO_DEEPSEEK else "PASS"),
                        "cross_family": (not NO_DEEPSEEK)}
            # Cleared raise/strength but blocked before PASS by fabrication (B2) and/or ammunition (B3).
            # #24 同类修正(静默截断):原先 fab[:300] / ammo_fix[:400] 会把判官的发现
            # 悄悄砍掉大半 —— B3 一次给 5 条命中,每条含引文(~95 字符)+ 改写建议,
            # 400 字符只塞得下 1-2 条,剩下的在下一轮根本传不到写手手里,循环必然白跑。
            # 现在:预算放大到能装完整反馈,且截断必须**显式记日志**(不许静默)。
            fab = join_budget((b2.get("unsupported_claims") or []) + (b2.get("invented_citations") or [])
                               + (b2.get("reasons") or []), 3000, "B2") if not b2_ok else ""
            # ★ 先排序再装箱:拦截类(B3_BLOCKING)必须先进 seed,建议类
            # (not_direct/deletable)才是可丢的。单测发现 union-of-3 后命中达 12 条
            # /4305 字符,只靠加大预算装不下 —— 重要的必须优先。
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

    # ★ 驱动级硬闸(2026-09-29,01-wdData/37ch 踩坑后加):r6 绝不在没有 evidence_pool
    # 的情况下写作。stage prompt 里的 fail-closed 只是**给引擎的指令**,引擎可能不遵守;
    # 唯一可靠的强制在这里。
    # 病根:r6_write.md / b2 都写过"evidence_pool 若无则退回 evidence_map.json",而
    # evidence_map 是 r1 产的**未过滤**证据底(无 evidence_status、未剔除 REJECT 实验)。
    # 后果实测:37ch 的稿把 01-E-overlap 写成 "our overlap stress test measured",
    # 而该实验 ACCEPTANCE=REJECT → B2 判 FAIL,整轮 HONEST_CONCEDE。
    if "r6r7" in do:
        pool = f"{camp}/ledger/evidence_pool.json"
        if not os.path.exists(pool):
            emap = f"{camp}/ledger/evidence_map.json"
            if os.path.exists(emap):
                log(f"  evidence_pool.json 缺失 → 回填 r5_evidence_merge(r6 不得用未过滤证据写作)")
                run_stage("r5_evidence_merge.md", {"SLUG": slug}, pool,
                          sandbox="workspace-write", effort="high", dry=dry)
            if not os.path.exists(pool) and not dry:
                log(f"FATAL: {slug} 无 evidence_pool.json 且回填失败 —— 拒绝跑 r6r7。"
                    f" 未过滤证据会把 REJECT 的实验写成已完成证据(见 37ch 实测)。"
                    f" 先修好 r5_evidence_merge 再来。")
                return []

    results = []
    if "r6r7" in do:
        targets = card.get("target", {})
        want = set(targets.get("require_raise_on", [])) | set(targets.get("maintain", []))
        max_iter = int(MAX_ITER_OVERRIDE or card.get("max_iter", 4))   # --max-iter:成本旋钮,不改契约文件
        n_strat = card.get("n_strategies")           # #20: reconcile card roster with MANIFEST
        for rev in card.get("reviewers", []):
            if rev["id"] in want or not want:
                log(f"-- reviewer {rev['id']} (OA={rev.get('initial_overall')}) --")
                results.append(reviewer_loop(slug, rev, max_iter, dry=dry, want_strategies=n_strat))
        if not dry:                               # H11: never clobber real loop_results.json on a dry run
            json.dump(results, open(f"{camp}/ledger/loop_results.json", "w"), ensure_ascii=False, indent=1)
    # ② 多轮交锋:交付前压力测试。**不是拦门** —— 不影响 r6r7 的 PASS 判定,
    # 产出"哪些 claim 在追问下塌掉",供回 r6 收窄或进 honest-concede 清单。
    # 只对已产出终稿的 reviewer 跑(拿不到稿就没得压)。
    if "mt" in do:
        targets = card.get("target", {})
        want = set(targets.get("require_raise_on", [])) | set(targets.get("maintain", []))
        for rev in card.get("reviewers", []):
            if want and rev["id"] not in want:
                continue
            final = f"{camp}/drafts/{rev['id']}.md"
            if not os.path.exists(final) and not dry:
                log(f"  mt {rev['id']}: 无终稿({final}),跳过")
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
                    help="② 多轮交锋的最大轮数(默认 3;追问不新即提前饱和停止)")
    ap.add_argument("--b3-repeats", type=int, default=None,
                    help="B3 连跑次数取命中并集(默认 3;实测单次漏检率 ~20%%)")
    ap.add_argument("--fanout-all", action="store_true",
                    help="恢复旧行为:每轮把 N 个策略全写一遍(贵 3×,仅策略对比评测用)")
    ap.add_argument("--no-deepseek", action="store_true",
                    help="单家族降级:DeepSeek 不可用时用纯 codex 判官(丢跨家族合议,产物标 degraded)")
    ap.add_argument("--max-iter", type=int, default=None,
                    help="覆盖 card 的 max_iter(成本旋钮;验证跑建议 1-2)")
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
        log("⚠️ --fanout-all:每轮全写 N 个策略,写作成本 ×N(实测每次 ≈447k in token)。")
    if NO_DEEPSEEK:
        log("⚠️ 单家族降级模式(--no-deepseek):跨家族合议不成立,GOAL.md 不可违反 #4 被放弃。"
            "判官仍 ≠ 写手(H1 保住)。产物一律标 cross_family=false / status=PASS_SINGLE_FAMILY,"
            "不得当作真 ACQUIT 使用。")
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
