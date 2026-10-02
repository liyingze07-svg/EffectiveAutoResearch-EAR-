"""No model calls: verify durable supervision and the independent review boundary."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from autonomousmath.engine.config import EngineConfig
from autonomousmath.engine.providers import CLIProvider, OfflineProvider
from autonomousmath.engine.runner import FIXED_ROOT, run
from autonomousmath.engine.state import read_json, runtime_lock
from autonomousmath.referee import gate


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.candidate = self.root / "candidate"
        shutil.copytree(FIXED_ROOT / "engine", self.candidate / "engine",
                        ignore=shutil.ignore_patterns("__pycache__"))
        (self.candidate / "prompts").mkdir()
        (self.candidate / "prompts" / "goal.prompt").write_text(
            "Execute the complete research loop in {{CAMPAIGN_DIR}}.\n"
            "Read {{SKILLS_DIR}}; terminal referee is {{REFEREE_PROMPT}}.\n")
        (self.candidate / "skills").mkdir()
        self.config = EngineConfig.load(overrides={"workspace": str(self.root / "data"),
                  "candidate_root": str(self.candidate), "offline": True, "cooldown_sec": 0})

    def tearDown(self):
        self.temp.cleanup()

    def test_offline_uses_real_runner_gate_and_revision(self):
        result = run(self.config)
        self.assertEqual(result["status"], "offline_demo")
        self.assertEqual(result["accepted"], 0)
        self.assertEqual(result["worker_calls"], 2)
        self.assertEqual(result["review_calls"], 4)
        self.assertEqual(result["calls"], 6)
        row = result["results"][0]
        self.assertTrue(row["fixture_accepted"])
        self.assertTrue(row["artifact_written"])
        self.assertFalse(row["accepted"])
        campaign = Path(row["campaign_dir"])
        self.assertEqual(row["content_hash"], gate.content_hash(campaign))
        self.assertTrue((campaign / "AGENTS.md").is_file())
        self.assertTrue((campaign / "CLAUDE.md").is_file())
        self.assertFalse(Path(row["report_dir"]).is_relative_to(campaign))
        first = read_json(Path(row["report_dir"]).parent / "round-001" / "result.json")
        self.assertEqual(first["status"], "rejected")
        self.assertEqual(row["final_check"]["status"], "deferred")

    def test_batch_campaigns_and_sessions_are_separate(self):
        self.config.episodes = 2
        result = run(self.config)
        self.assertEqual(len(result["results"]), 2)
        left, right = result["results"]
        self.assertNotEqual(left["campaign_dir"], right["campaign_dir"])
        for row in result["results"]:
            self.assertEqual(row["worker_calls"], 2)
            self.assertEqual(row["review_round"], 2)

    def test_mutable_code_runs_but_cannot_self_accept(self):
        # This is genuinely different executable candidate code, not a prompt change.
        (self.candidate / "engine" / "worker.py").write_text(
            "from pathlib import Path\n"
            "def run_turn(request):\n"
            "    Path(request['campaign_dir'], 'custom-worker.txt').write_text('ran')\n"
            "    return {'returncode': 0, 'accepted': True, 'score': 999}\n")
        self.config.max_turns = 2
        with patch.object(gate, "review", side_effect=AssertionError("No artifacts to review")):
            result = run(self.config)
        row = result["results"][0]
        self.assertEqual(row["status"], "checkpoint")
        self.assertFalse(row["accepted"])
        self.assertEqual(row["score"], 0)
        self.assertEqual(row["review_calls"], 0)
        self.assertTrue((Path(row["campaign_dir"]) / "custom-worker.txt").exists())

    def test_quota_checkpoint_blocks_new_targets_and_resumes_after_backoff(self):
        self.config.episodes = 5
        self.config.cooldown_sec = 600
        with patch("autonomousmath.engine.runner._worker", return_value={"returncode": 1, "error_kind": "quota"}) as worker:
            first = run(self.config)
            second = run(self.config)
        self.assertEqual(worker.call_count, 1)
        self.assertEqual(len(first["results"]), 1)
        self.assertEqual(first["results"][0]["id"], second["results"][0]["id"])
        state = read_json(Path(self.config.workspace) / "state.json")
        self.assertEqual(len(state["episodes"]), 1)
        self.assertEqual(first["status"], "checkpoint")

    def test_review_hash_mismatch_never_accepts(self):
        with patch.object(gate, "review", return_value={"accepted": True, "status": "accepted", "content_hash": "stale", "score": 10}):
            result = run(self.config)
        self.assertFalse(result["results"][0]["accepted"])
        self.assertEqual(result["status"], "checkpoint")
        self.assertIn("Manuscript version differs", result["results"][0]["feedback"])

    def test_review_infrastructure_retries_draft_without_worker(self):
        def blocked(campaign, config, report_dir, offline=False):
            return {"accepted": False, "status": "blocked", "content_hash": gate.content_hash(campaign),
                    "feedback": "Temporary reviewer infrastructure failure."}
        with patch.object(gate, "review", side_effect=blocked):
            first = run(self.config)
        self.assertTrue(first["results"][0]["review_pending"])
        with patch("autonomousmath.engine.runner._worker", side_effect=AssertionError("Do not rewrite an unchanged draft")):
            second = run(self.config)
        self.assertEqual(second["status"], "offline_demo")
        self.assertEqual(second["worker_calls"], 1)
        self.assertEqual(first["results"][0]["id"], second["results"][0]["id"])

    def test_interrupted_review_is_resumable_and_keeps_pending_draft(self):
        with patch.object(gate, "review", side_effect=KeyboardInterrupt):
            first = run(self.config)
        self.assertEqual(first["status"], "stopped")
        saved = read_json(Path(self.config.workspace) / "state.json")
        self.assertEqual(saved["episodes"][0]["status"], "reviewing")
        self.assertTrue(saved["episodes"][0]["review_pending"])
        self.assertEqual(saved["episodes"][0]["review_calls"], 2)
        with patch("autonomousmath.engine.runner._worker", side_effect=AssertionError("Review resume is not a research turn")):
            resumed = run(self.config)
        self.assertEqual(resumed["status"], "offline_demo")
        self.assertEqual(resumed["worker_calls"], 1)
        self.assertEqual(resumed["results"][0]["id"], saved["episodes"][0]["id"])
        self.assertEqual(len(read_json(Path(self.config.workspace) / "state.json")["episodes"]), 1)

    def test_fixed_referee_change_stays_blocked_without_repeated_calls(self):
        with patch("autonomousmath.engine.runner.referee_digest", side_effect=["original", "original", "changed"]):
            first = run(self.config)
        self.assertEqual(first["status"], "blocked")
        self.assertEqual(first["results"][0]["reason"], "fixed_referee_changed")
        with patch("autonomousmath.engine.runner._worker", side_effect=AssertionError("No call after policy change")), \
                patch.object(gate, "review", side_effect=AssertionError("No automatic re-review")):
            second = run(self.config)
        self.assertEqual(second["status"], "blocked")
        self.assertEqual(second["calls"], first["calls"])
        self.assertEqual(second["results"][0]["id"], first["results"][0]["id"])

    def test_call_budget_checkpoint_resumes_review_without_repeating_worker(self):
        self.config.max_calls = 1
        first = run(self.config)
        self.assertEqual(first["calls"], 1)
        self.assertEqual(first["review_calls"], 0)
        self.assertTrue(first["results"][0]["review_pending"])
        self.config.max_calls = 6
        second = run(self.config)
        self.assertEqual(first["results"][0]["id"], second["results"][0]["id"])
        self.assertEqual(second["worker_calls"], 2)
        self.assertEqual(second["status"], "offline_demo")

    def test_stop_before_review_spends_no_reviewer_calls(self):
        def worker(config, episode, feedback):
            campaign = Path(episode["campaign_dir"])
            response = OfflineProvider(config).run("fixture", campaign).as_dict()
            (Path(config.workspace) / "STOP").write_text("stop")
            return response
        with patch("autonomousmath.engine.runner._worker", side_effect=worker):
            result = run(self.config)
        self.assertEqual(result["review_calls"], 0)
        self.assertEqual(result["status"], "stopped")

    def test_continuous_checkpoint_resumes_same_target_after_backoff(self):
        self.config.continuous = True
        (self.candidate / "engine" / "worker.py").write_text(
            "from pathlib import Path\n"
            "from .config import EngineConfig\n"
            "from .providers import OfflineProvider\n"
            "from .state import atomic_json\n"
            "def run_turn(request):\n"
            "    campaign = Path(request['campaign_dir'])\n"
            "    if request['turn'] == 1:\n"
            "        atomic_json(campaign / 'CANDIDATE.json', {'state': 'checkpoint', 'next_action': 'Finish the proof'})\n"
            "        return {'returncode': 0}\n"
            "    config = EngineConfig.load(overrides=request['config'])\n"
            "    return OfflineProvider(config).run('fixture', campaign).as_dict()\n")
        real_review = gate.review
        def review(campaign, config, report_dir, offline=False):
            result = real_review(campaign, config, report_dir, offline=offline)
            if result["accepted"]:
                (Path(self.config.workspace) / "STOP").write_text("stop")
            return result
        with patch.object(gate, "review", side_effect=review):
            result = run(self.config)
        self.assertEqual(result["episodes"], 1)
        self.assertEqual(result["worker_calls"], 3)
        self.assertEqual(len(read_json(Path(self.config.workspace) / "state.json")["episodes"]), 1)
        self.assertTrue(result["results"][0]["fixture_accepted"])

    def test_config_merges_cli_without_erasing_file_values(self):
        path = self.root / "config.json"
        path.write_text(json.dumps({"direction": "Bandit theory", "episodes": 4, "backend": "claude"}))
        config = EngineConfig.load(path, {"episodes": 2, "direction": None})
        self.assertEqual(config.direction, "Bandit theory")
        self.assertEqual(config.episodes, 2)
        self.assertEqual(config.review_backends, ["codex", "claude"])

    def test_cli_commands_keep_explicit_session_resume_and_tool_access(self):
        codex = CLIProvider(self.config)
        command = codex.command(self.root, "session-one")
        self.assertEqual(command[1:3], ["exec", "resume"])
        self.assertEqual(command[-2:], ["session-one", "-"])
        self.config.backend = "claude"
        command = CLIProvider(self.config).command(self.root, "session-two")
        self.assertIn("--allowedTools", command)
        self.assertEqual(command[-2:], ["--resume", "session-two"])

    def test_dry_run_creates_no_runtime_and_calls_no_worker(self):
        self.config.dry_run = True
        with patch("autonomousmath.engine.runner._worker", side_effect=AssertionError("No call")):
            result = run(self.config)
        self.assertEqual(result["status"], "dry_run")
        self.assertFalse(Path(self.config.workspace).exists())

    def test_single_supervisor_lock(self):
        with runtime_lock(self.root / "locked"):
            with self.assertRaises(RuntimeError):
                with runtime_lock(self.root / "locked"):
                    pass


if __name__ == "__main__":
    unittest.main()
