"""Mechanical supervision, not a scientific DAG.

Each child receives the complete composed goal. It chooses its tools and its own
research trajectory. This supervisor owns call budgets, durable state, and the
independent final review boundary, including for a mutable candidate engine.
"""
from __future__ import annotations

import hashlib
import importlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

from .config import EngineConfig
from .state import StateStore, atomic_json, read_json, runtime_lock, terminate_tree, utc_now, wait_until


FIXED_ROOT = Path(__file__).resolve().parents[1]
RESUMABLE = {"working", "refining", "reviewing", "checkpoint", "blocked"}


def referee_digest(root: Path = FIXED_ROOT) -> str:
    digest = hashlib.sha256()
    base = root / "referee"
    for path in sorted(base.rglob("*")):
        if path.is_file() and path.suffix in (".py", ".md", ".prompt", ".json") and "__pycache__" not in path.parts:
            digest.update(str(path.relative_to(base)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def asset_root(config: EngineConfig) -> Path:
    path = Path(config.candidate_root) if config.candidate_root else FIXED_ROOT
    if (path / "autonomousmath" / "engine").is_dir():
        path = path / "autonomousmath"
    return path.resolve()


def doctor(config: EngineConfig) -> dict:
    root = asset_root(config)
    commands = {"python": sys.executable, "pdflatex": shutil.which("pdflatex"),
                "bibtex": shutil.which("bibtex"), "pdftotext": shutil.which("pdftotext"),
                "pdfinfo": shutil.which("pdfinfo")}
    for backend in {config.backend, *(config.review_backends or [])}:
        cmd = config.codex_command if backend == "codex" else config.claude_command
        commands[backend] = shutil.which(cmd)
    files = {"goal_prompt": (root / "prompts" / "goal.prompt").is_file(),
             "skills": (root / "skills").is_dir(),
             "fixed_gate": (FIXED_ROOT / "referee" / "gate.py").is_file(),
             "fixed_referee_prompt": (FIXED_ROOT / "referee" / "SAC_PROMPT.md").is_file(),
             "candidate_worker": (root / "engine" / "worker.py").is_file()}
    missing = [name for name, value in files.items() if not value]
    if not config.offline:
        missing += [name for name, value in commands.items() if not value]
    return {"ok": not missing, "offline": config.offline, "commands": commands,
            "files": files, "missing": missing, "engine_root": str(root),
            "note": "Checks dependencies only; no authentication or model calls."}


def _artifact_state(campaign: Path) -> dict:
    proof = campaign / "proof.md"
    tex = campaign / "paper" / "main.tex"
    pdf = campaign / "paper" / "main.pdf"
    def present(path: Path) -> bool:
        return path.is_file() and not path.is_symlink() and path.stat().st_size > 0
    states = {"proof_written": present(proof), "source_written": present(tex), "pdf_written": present(pdf)}
    if states["pdf_written"]:
        with pdf.open("rb") as stream:
            states["pdf_written"] = stream.read(5) == b"%PDF-"
    states["artifact_written"] = all(states.values())
    return states


def _new_episode(store: StateStore, config: EngineConfig) -> dict:
    eid = f"episode-{len(store.state['episodes']) + 1:06d}-{uuid.uuid4().hex[:8]}"
    campaign = store.root / "tasks" / eid
    campaign.mkdir(parents=True)
    episode = {"id": eid, "campaign_dir": str(campaign), "status": "working", "calls": 0,
               "worker_calls": 0, "review_calls": 0,
               "retries": 0, "review_revisions": 0, "review_round": 0, "session_id": None,
               "accepted": False, "offline": config.offline, "quality_score": 0.0,
               "score": 0.0, "artifact_written": False, "created_at": utc_now()}
    store.state["episodes"].append(episode)
    store.event("episode_started", id=eid, offline=config.offline)
    store.save()
    return episode


def _worker(config: EngineConfig, episode: dict, feedback: str) -> dict:
    control = Path(config.workspace) / "control" / episode["id"]
    control.mkdir(parents=True, exist_ok=True)
    request = control / f"request-{episode['worker_calls']:03d}.json"
    response = control / f"response-{episode['worker_calls']:03d}.json"
    root = asset_root(config)
    atomic_json(request, {"config": config.as_dict(), "fixed_root": str(FIXED_ROOT),
                          "engine_root": str(root), "campaign_dir": episode["campaign_dir"],
                          "turn": episode["worker_calls"], "session_id": episode.get("session_id"),
                          "feedback": feedback})
    cmd = [sys.executable, "-m", "autonomousmath.engine.worker", "--request", str(request),
           "--response", str(response)]
    if config.candidate_root:
        cmd += ["--candidate-root", str(root)]
    env = dict(os.environ)
    project = str(FIXED_ROOT.parent)
    env["PYTHONPATH"] = project + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    # Inherit the supervisor's process group: a registered killpg stops every descendant.
    process = None
    try:
        process = subprocess.Popen(cmd, cwd=episode["campaign_dir"], env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        process.communicate(timeout=config.timeout_sec + 30)
    except subprocess.TimeoutExpired:
        if process is not None:
            terminate_tree(process)
            process.communicate()
        return {"returncode": 124, "error_kind": "timeout"}
    except OSError:
        return {"returncode": 127, "error_kind": "infrastructure"}
    except BaseException:
        if process is not None:
            terminate_tree(process)
        raise
    payload = read_json(response, {})
    if process.returncode or not isinstance(payload, dict) or "returncode" not in payload:
        return {"returncode": process.returncode or 1, "error_kind": "worker_error"}
    return payload


def _feedback(campaign: Path, text: str) -> None:
    (campaign / "REVIEW_FEEDBACK.md").write_text(text + "\n", encoding="utf-8")


def _checkpoint(store: StateStore, episode: dict, reason: str, config: EngineConfig) -> None:
    episode.update(status="checkpoint", reason=reason, next_attempt_at=time.time() + config.cooldown_sec)
    campaign = Path(episode["campaign_dir"])
    with (campaign / "PROGRESS.md").open("a", encoding="utf-8") as stream:
        stream.write(f"\n[{utc_now()}] CHECKPOINT — {reason}; resume this campaign after backoff.\n")
    store.event("checkpoint", id=episode["id"], reason=reason,
                next_attempt_at=episode["next_attempt_at"])
    store.save()


def _review(config: EngineConfig, episode: dict, gate, frozen_digest: str, store: StateStore) -> dict:
    if referee_digest() != frozen_digest:
        return {"status": "blocked", "accepted": False, "failure_kind": "fixed_referee_changed",
                "feedback": "Fixed referee changed; review refused."}
    episode["review_round"] += 1
    episode["review_calls"] += 2
    episode["calls"] = episode["worker_calls"] + episode["review_calls"]
    # Persist accounting and the pending draft before any external review call.
    # A killed reviewer cannot erase the manuscript or cause a new research turn.
    episode["review_pending"] = True
    store.save()
    review_config = config.as_dict()
    review_config["review_round"] = episode["review_round"]
    report_dir = Path(config.workspace) / "reviews" / episode["id"] / f"round-{episode['review_round']:03d}"
    report = gate.review(Path(episode["campaign_dir"]), review_config, report_dir, offline=config.offline)
    if not isinstance(report, dict):
        return {"status": "blocked", "accepted": False, "feedback": "Invalid independent review response."}
    if referee_digest() != frozen_digest:
        return {"status": "blocked", "accepted": False, "failure_kind": "fixed_referee_changed",
                "feedback": "Fixed referee changed during review."}
    current = gate.content_hash(Path(episode["campaign_dir"]))
    if report.get("content_hash") != current:
        return {"status": "blocked", "accepted": False,
                "feedback": "Manuscript version differs from the independently reviewed version."}
    return report


def _run_episode(config: EngineConfig, episode: dict, store: StateStore, gate, frozen_digest: str) -> dict:
    campaign = Path(episode["campaign_dir"])
    feedback = episode.get("feedback", "")
    episode.setdefault("worker_calls", episode.get("calls", 0))
    episode.setdefault("review_calls", 0)
    if episode.get("offline") != config.offline:
        raise ValueError("A fixture campaign cannot resume as real research, or vice versa")
    deadline = float(episode.get("next_attempt_at", 0))
    if deadline > time.time():
        if not config.continuous:
            return episode
        if not wait_until(store.root, deadline):
            episode["status"] = "checkpoint"
            return episode
    turns_this_run = 0
    while turns_this_run < config.max_turns and episode["calls"] < config.max_calls:
        if (store.root / "STOP").exists():
            _checkpoint(store, episode, "operator_stop", config)
            return episode
        if referee_digest() != frozen_digest:
            episode.update(status="blocked", reason="fixed_referee_changed")
            store.save()
            return episode
        # Only a supervisor-owned pending-review checkpoint may reuse a submission.
        submission = campaign / "CANDIDATE.json"
        review_only = bool(episode.get("review_pending")) and _artifact_state(campaign)["artifact_written"]
        if not review_only:
            if submission.exists():
                archive = campaign / "submissions"
                archive.mkdir(exist_ok=True)
                os.replace(submission, archive / f"candidate-before-{episode['worker_calls'] + 1:03d}.json")
            episode.update(status="refining" if feedback else "working", next_attempt_at=0)
            episode["worker_calls"] += 1
            episode["calls"] = episode["worker_calls"] + episode["review_calls"]
            turns_this_run += 1
            store.state.update(status="running", current_episode=episode["id"])
            store.event("turn_started", id=episode["id"], turn=episode["worker_calls"])
            store.save()
            result = _worker(config, episode, feedback)
            if result.get("session_id"):
                episode["session_id"] = result["session_id"]
            # A candidate's self-reported accepted/score fields are intentionally ignored.
            episode.update(_artifact_state(campaign))
            if int(result.get("returncode", 1)) != 0:
                episode["retries"] += 1
                kind = str(result.get("error_kind") or "infrastructure")
                _checkpoint(store, episode, kind, config)
                if config.continuous and episode["retries"] <= config.max_infra_retries:
                    if wait_until(store.root, episode["next_attempt_at"]):
                        feedback = "Resume your saved progress. The previous CLI call was interrupted by " + kind + "."
                        continue
                if episode["retries"] > config.max_infra_retries:
                    episode.update(status="blocked", reason="infrastructure_retry_cap")
                    store.save()
                return episode
        candidate = read_json(submission, {})
        phase = candidate.get("state") if isinstance(candidate, dict) else None
        if phase == "retreat":
            episode.update(status="retreat", reason=str(candidate.get("reason", "model_retreat"))[:1000])
            store.event("episode_retreat", id=episode["id"])
            store.save()
            return episode
        if phase == "checkpoint":
            _checkpoint(store, episode, "model_checkpoint", config)
            episode["feedback"] = str(candidate.get("next_action") or candidate.get("reason") or "Resume saved progress.")
            store.save()
            return episode
        if phase != "draft_ready" or not episode["artifact_written"]:
            feedback = ("Your goal is not complete: submit nonempty proof.md, complete paper/main.tex "
                        "and a valid compiled paper/main.pdf, then CANDIDATE.json state=draft_ready. "
                        "Continue the same complete research loop from existing files and saved progress.")
            episode["feedback"] = feedback
            store.event("continuation", id=episode["id"], reason="incomplete_artifact")
            store.save()
            continue
        if (store.root / "STOP").exists():
            episode["review_pending"] = True
            _checkpoint(store, episode, "operator_stop_before_review", config)
            return episode
        if episode["calls"] + 2 > config.max_calls:
            episode["review_pending"] = True
            _checkpoint(store, episode, "call_budget_exhausted_before_review", config)
            return episode
        episode["review_pending"] = True
        store.event("review_started", id=episode["id"], round=episode["review_round"] + 1)
        episode["status"] = "reviewing"
        store.save()
        try:
            report = _review(config, episode, gate, frozen_digest, store)
        except Exception as exc:
            report = {"accepted": False, "status": "blocked", "feedback": "Independent reviewer infrastructure: " + type(exc).__name__}
        score = report.get("score", 0.0)
        try:
            score = float(score or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        episode.update(quality_score=score, score=score, report_dir=str(report.get("report_dir", "")),
                       content_hash=report.get("content_hash"), source_hash=report.get("source_hash"),
                       compiled_pdf_hash=report.get("compiled_pdf_hash"),
                       final_review={k: report.get(k) for k in ("accepted", "status", "content_hash", "reviews", "score", "offline")})
        store.event("review_completed", id=episode["id"], round=episode["review_round"],
                    verdict=report.get("status"), score=score, offline=config.offline)
        if report.get("status") == "blocked":
            episode["retries"] += 1
            feedback = str(report.get("feedback") or "Review infrastructure blocked. Resume and resubmit unchanged artifacts.")
            episode["feedback"] = feedback
            episode["review_pending"] = True
            if report.get("failure_kind") == "fixed_referee_changed":
                episode.update(status="blocked", reason="fixed_referee_changed")
                store.event("fixed_referee_changed", id=episode["id"])
                store.save()
                return episode
            _checkpoint(store, episode, "review_infrastructure", config)
            return episode
        episode["review_pending"] = False
        if report.get("accepted"):
            if config.offline or report.get("offline") or report.get("status") == "offline_demo":
                episode.update(status="offline_demo", accepted=False, fixture_accepted=True, offline=True)
            else:
                episode.update(status="accepted", accepted=True)
            if episode["status"] == "offline_demo":
                episode["final_check"] = {"status": "deferred", "coverage": [],
                                          "reason": "Offline fixtures are not mathematical research results."}
            else:
                from autonomousmath.checking import final_check
                try:
                    episode["final_check"] = final_check(campaign, config.as_dict(),
                                                          store.root / "checks" / episode["id"])
                except Exception as exc:
                    episode["final_check"] = {"status": "blocked", "coverage": [], "reason": type(exc).__name__}
                if gate.content_hash(campaign) != report.get("content_hash"):
                    episode.update(status="blocked", accepted=False, reason="paper_changed_during_final_check")
            episode["completed_at"] = utc_now()
            store.event("episode_completed", id=episode["id"], status=episode["status"])
            store.save()
            return episode
        episode["review_revisions"] += 1
        if episode["review_revisions"] > config.max_review_revisions:
            episode.update(status="rejected", accepted=False, reason="review_revision_cap")
            store.save()
            return episode
        feedback = str(report.get("feedback") or "Address every independent review finding and resubmit.")
        _feedback(campaign, feedback)
        episode.update(status="refining", feedback=feedback)
        store.save()
    _checkpoint(store, episode, "call_budget_exhausted", config)
    return episode


def run(config: EngineConfig) -> dict:
    root = Path(config.workspace)
    if config.dry_run:
        checks = doctor(config)
        return {"status": "dry_run", "episodes": 0, "accepted": 0, "offline": config.offline,
                "workspace": str(root), "results": [], "config": config.as_dict(), "doctor": checks,
                "goal_prompt": str(asset_root(config) / "prompts" / "goal.prompt")}
    checks = doctor(config)
    if not checks["ok"]:
        return {"status": "blocked", "reason": "missing_dependencies", "doctor": checks,
                "episodes": 0, "accepted": 0, "offline": config.offline, "workspace": str(root), "results": []}
    gate = importlib.import_module("autonomousmath.referee.gate")
    frozen_digest = referee_digest()
    results = []
    with runtime_lock(root):
        # A new explicit run command resumes after a prior operator STOP.
        (root / "STOP").unlink(missing_ok=True)
        store = StateStore(root)
        store.state.update(status="running", backend=config.backend, direction=config.direction,
                           offline=config.offline, referee_digest=frozen_digest)
        store.save()
        try:
            while config.continuous or len(results) < config.episodes:
                if (root / "STOP").exists():
                    break
                pending = next((e for e in reversed(store.state["episodes"])
                                if e.get("status") in RESUMABLE), None) if config.resume else None
                episode = pending if pending else _new_episode(store, config)
                if episode.get("reason") == "fixed_referee_changed":
                    episode["status"] = "blocked"
                    results.append(dict(episode))
                    store.save()
                    break
                outcome = _run_episode(config, episode, store, gate, frozen_digest)
                if (config.continuous and outcome["status"] == "checkpoint"
                        and outcome.get("reason") in ("model_checkpoint", "review_infrastructure")
                        and outcome["calls"] < config.max_calls
                        and outcome["retries"] <= config.max_infra_retries):
                    if wait_until(root, float(outcome.get("next_attempt_at", time.time()))):
                        continue
                results.append(dict(outcome))
                # Never replace a quota/infra checkpoint with a fresh target.
                if outcome["status"] in ("checkpoint", "blocked"):
                    break
                if config.interval_sec and (config.continuous or len(results) < config.episodes):
                    if not wait_until(root, time.time() + config.interval_sec):
                        break
        except KeyboardInterrupt:
            store.state["status"] = "stopped"
            store.save()
            return _summary(config, results, "stopped")
        status = "stopped" if (root / "STOP").exists() else (results[-1]["status"] if results else "idle")
        store.state.update(status=status, current_episode=None)
        store.save()
    return _summary(config, results, status)


def _summary(config: EngineConfig, results: list[dict], status: str) -> dict:
    return {"status": status, "episodes": len(results), "accepted": sum(bool(r.get("accepted")) for r in results),
            "calls": sum(r.get("calls", 0) for r in results),
            "worker_calls": sum(r.get("worker_calls", 0) for r in results),
            "review_calls": sum(r.get("review_calls", 0) for r in results),
            "offline": config.offline, "workspace": config.workspace, "results": results}
