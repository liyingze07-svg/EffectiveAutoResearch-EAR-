"""Extract labelled review threads by joining ProReviewer (initial ratings) with
OpenReview (final rating + rebuttal text), keyed on the review note id.

Why this design: OpenReview only reliably exposes the CURRENT (final) rating; the
initial rating lives in edit history that is hidden for ~64% of notes. ProReviewer
scraped the ratings BEFORE the discussion phase, so it supplies the initial rating
(and the review text / sub-scores). We join the two on the review note id, which
ProReviewer stores verbatim -> clean raise/same/lower labels with no hidden-history
dependence.

Per-forum OpenReview data is cached to data/cache/<forum>.json.
"""
import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(ROOT, "data", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def _val(content, key):
    v = (content or {}).get(key)
    return v.get("value") if isinstance(v, dict) else v


def _short_invs(note):
    return [iv.split("/")[-1] for iv in note.invitations]


def _label(init, final):
    if init is None or final is None:
        return None
    if final > init:
        return "raise"
    if final < init:
        return "lower"
    return "same"


def _forum_finals_and_rebuttals(client, forum_id, use_cache=True):
    """Return {note_id: {'final': rating, 'rebuttal': text}} for a forum.

    Cached per forum so re-runs need no API calls.
    """
    cache_path = os.path.join(CACHE_DIR, f"{forum_id}.json")
    if use_cache and os.path.exists(cache_path):
        return json.load(open(cache_path))

    notes = client.get_notes(forum=forum_id, details="replies")
    if not notes:
        json.dump({}, open(cache_path, "w"))
        return {}

    children = {}
    for n in notes:
        children.setdefault(n.replyto, []).append(n)

    def subtree(rid):
        out, stack = [], list(children.get(rid, []))
        while stack:
            x = stack.pop()
            out.append(x)
            stack += children.get(x.id, [])
        return out

    out = {}
    for n in notes:
        if not any("Official_Review" in s for s in _short_invs(n)):
            continue
        author_comments = [
            (_val(c.content, "comment") or "")
            for c in subtree(n.id)
            if any("Author" in s for s in c.signatures)
        ]
        out[n.id] = {
            "final": _val(n.content, "rating"),
            "rebuttal": "\n\n---\n\n".join(t for t in author_comments if t),
        }
    json.dump(out, open(cache_path, "w"), ensure_ascii=False)
    return out


def extract_paper(client, pr_record, use_cache=True):
    """Join one ProReviewer paper record with OpenReview -> list of thread dicts."""
    forum_id = pr_record["paper_id"]
    finals = _forum_finals_and_rebuttals(client, forum_id, use_cache=use_cache)
    if not finals:
        return []

    title = pr_record.get("title")
    threads = []
    for rev in pr_record["reviews"]:
        nid = rev["id"]
        info = finals.get(nid)
        if not info:
            continue  # review note not found on OpenReview (rare)
        init = rev.get("initial_rating")
        final = info["final"]
        label = _label(init, final)
        if label is None:
            continue
        threads.append({
            "paper_id": forum_id,
            "note_id": nid,
            "title": title,
            "summary": rev.get("summary"),
            "strengths": rev.get("strengths"),
            "weaknesses": rev.get("weaknesses"),
            "questions": rev.get("questions"),
            "confidence": rev.get("confidence"),
            "soundness": rev.get("soundness"),
            "presentation": rev.get("presentation"),
            "contribution": rev.get("contribution"),
            "initial_rating": init,
            "final_rating": final,
            "delta": final - init,
            "label": label,
            "has_rebuttal": bool(info["rebuttal"]),
            "rebuttal": info["rebuttal"],
        })
    return threads
