#!/usr/bin/env python3
"""Mechanical (re)instantiation of a rebuttal campaign from its REBUTTAL_CARD.json.

Renders CLAUDE/GOAL/SPEC/VERIFY/RESOURCE from the harness templates, filling BOTH
the mechanical placeholders (slug/paths/limits) AND the content placeholders
(title/venue/paper_claims/reviewers/target) straight from REBUTTAL_CARD.json --
no per-case judgment, all values come from the card. Also copies the case inputs
into the campaign folder (`inputs/`) and stamps the harness version into the
ledger so every campaign records which harness produced it.

Mirrors ExpAuto/NewInfra/instantiate.py. Idempotent: only creates files/dirs that
are missing, never overwrites an existing draft/ledger.

Usage:
  instantiate.py --slug <slug>   |   instantiate.py --all
"""
import argparse, json, os, shutil

ROOT_DEFAULT = "$AUTOREBUTTAL_ROOT"
TEMPLATES = {"CLAUDE.md": "CLAUDE.tmpl.md", "GOAL.md": "GOAL.tmpl.md",
             "SPEC.md": "SPEC.tmpl.md", "VERIFY.md": "VERIFY.tmpl.md",
             "RESOURCE.md": "RESOURCE.tmpl.md"}


def reviewers_table(revs):
    if not revs:
        return "- (REBUTTAL_CARD.reviewers is empty — instantiation failed)"
    head = "| id | OA | conf | sound | present | contrib | review |\n|---|---|---|---|---|---|---|"
    rows = [head]
    for r in revs:
        oa = r.get("initial_overall", r.get("initial_rating", "?"))   # #25: EMNLP OA (/5); legacy rating fallback
        rows.append(f"| {r.get('id','')} | {oa} | "
                    f"{r.get('confidence','?')} | {r.get('soundness','?')} | "
                    f"{r.get('presentation','?')} | {r.get('contribution','?')} | "
                    f"{r.get('review_ref','')} |")
    return "\n".join(rows)


def bullets(items, empty):
    return "\n".join(f"- {x}" for x in items) if items else empty


def target_sentence(t):
    if not t:
        return "clear the cross-family consensus gate for every P0 reviewer"
    p0 = ", ".join(t.get("require_raise_on", []))
    keep = ", ".join(t.get("maintain", []))                         # #25: maintain zone (OA>=4)
    s = f"clear the DeepSeek+Codex consensus gate for P0 reviewer [{p0}] (zone bar,min_delta={t.get('min_delta',1)})"
    if keep:
        s += f"; keep [{keep}] (do not let it drop)"
    return s


def harness_version(harness):
    try:
        return open(os.path.join(harness, "HARNESS_VERSION")).read().strip()
    except Exception:
        return "unknown"


def build_values(card, slug, harness):
    return {
        "SLUG": slug,
        "HARNESS_DIR": harness,
        "PAPER_TITLE": card.get("title", slug),
        "VENUE": card.get("venue", "(venue not provided)"),
        "WORD_LIMIT": str(card.get("word_limit", "(not provided,follow venue rules)")),
        "N_STRATEGIES": str(card.get("n_strategies", 3)),
        "MAX_ITER": str(card.get("max_iter", 4)),
        "ALLOW_NEW_EXPERIMENTS": ("New experiments are allowed (use ExpAuto compute)"
                                  if card.get("allow_new_experiments") else "No new experiments for this case (writing-only mode)"),
        "PAPER_CLAIMS": bullets(card.get("paper_claims"), "- (no paper_claims)"),
        "REVIEWERS_TABLE": reviewers_table(card.get("reviewers")),
        "CONCERN_SEEDS": bullets(card.get("concern_seeds"), "- (no pre-extracted concern,r2 must atomize them itself)"),
        "TARGET": target_sentence(card.get("target")),
    }


def render(text, values):
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def instantiate(slug, harness, campaigns):
    camp = os.path.join(campaigns, slug)
    card_path = os.path.join(camp, "REBUTTAL_CARD.json")
    if not os.path.isfile(card_path):
        return f"SKIP {slug}: no REBUTTAL_CARD.json (run r0a auto-extract first)"
    card = json.load(open(card_path))
    values = build_values(card, slug, harness)

    for out_name, tmpl_name in TEMPLATES.items():
        tmpl = open(os.path.join(harness, "templates", tmpl_name)).read()
        open(os.path.join(camp, out_name), "w").write(render(tmpl, values))

    for d in ("inputs", "evidence", "ledger", "drafts"):
        os.makedirs(os.path.join(camp, d), exist_ok=True)

    with open(os.path.join(camp, "ledger", "harness-version.txt"), "w") as f:
        f.write(harness_version(harness) + "\n")

    left = sum(open(os.path.join(camp, o)).read().count("{{") for o in TEMPLATES)
    return f"OK   {slug}: harness={harness_version(harness)} braces_left={left}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--harness", default=os.path.join(ROOT_DEFAULT, "harness"))
    ap.add_argument("--campaigns", default=os.path.join(ROOT_DEFAULT, "campaigns"))
    a = ap.parse_args()
    harness = os.path.abspath(a.harness)
    if a.all:
        slugs = sorted(d for d in os.listdir(a.campaigns)
                       if os.path.isfile(os.path.join(a.campaigns, d, "REBUTTAL_CARD.json")))
    elif a.slug:
        slugs = [a.slug]
    else:
        ap.error("need --slug or --all")
    for s in slugs:
        print(instantiate(s, harness, a.campaigns))


if __name__ == "__main__":
    main()
