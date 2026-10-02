"""Behavioral checks for writer ownership, fixed review and offline evolution."""

import contextlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from unittest import mock

from autonomousmath.dashboard.server import Dashboard, make_server
from autonomousmath.optimizer.evolution import Evolution, EvolutionBusy, _process_stamp, aggregate, atomic_json, read_json


def source_fixture(root):
    for name in ("engine", "prompts", "skills", "referee"):
        (root / name).mkdir(parents=True)
    (root / "engine" / "worker.py").write_text("# mutable worker\n")
    (root / "prompts" / "goal.prompt").write_text("prove, write, check\n")
    (root / "referee" / "rubric.txt").write_text("fixed independent final review\n")
    (root / "skills" / "reviewer-panel").mkdir()
    (root / "skills" / "reviewer-panel" / "SAC_PROMPT.md").write_text("fixed rubric\n")


class FixtureEvolution(Evolution):
    def _evaluate(self, generation, name, task_index, repeat, task, control):
        return {"task": task, "candidate": name, "offline": control["offline"],
                "status": "offline_demo", "accepted": True, "score": 8 if name != "baseline" else 6,
                "artifact_written": True, "calls": 0, "retries": 0}


class OptimizerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        source_fixture(self.source)
        self.optimizer = FixtureEvolution(self.root / "work", self.source)

    def tearDown(self):
        self.temporary.cleanup()

    def test_fixed_review_is_never_copied_and_baseline_is_checked(self):
        state = self.optimizer.initialize(["fixed task"])
        baseline = self.optimizer.workspace / "candidates" / "baseline"
        self.assertFalse((baseline / "referee").exists())
        self.assertFalse((baseline / "skills" / "reviewer-panel").exists())
        (baseline / "engine" / "worker.py").write_text("changed baseline\n")
        with self.assertRaisesRegex(ValueError, "baseline"):
            self.optimizer._check_fixed(state)

    def test_final_reviewer_cannot_change_between_generations(self):
        state = self.optimizer.initialize(["task"])
        (self.source / "referee" / "rubric.txt").write_text("relaxed\n")
        with self.assertRaisesRegex(ValueError, "reviewer"):
            self.optimizer._check_fixed(state)

    def test_same_tasks_baseline_comparison_and_elite_survival(self):
        result = self.optimizer.run(generations=3, tasks=["first", "second"])
        state = result["state"]
        self.assertEqual(state["generation"], 3)
        self.assertEqual(len(state["history"]), 3)
        for generation in state["history"]:
            self.assertIn("baseline", generation["metrics"])
            self.assertEqual(generation["tasks_hash"], state["tasks_hash"])
            for metrics in generation["metrics"].values():
                self.assertEqual(metrics["n"], 2)
                self.assertEqual(metrics["accept_rate"], 0)
                self.assertEqual(metrics["simulated_accept_rate"], 1)
        self.assertIn(state["elite"], state["population"])
        self.assertGreater(state["history"][1]["gap_vs_baseline"], 0)
        with self.assertRaisesRegex(ValueError, "fixed"):
            self.optimizer.initialize(["different task"])

    def test_offline_pass_does_not_count_as_real_acceptance(self):
        metrics = aggregate([{"offline": True, "accepted": True, "score": 9, "artifact_written": True,
                              "status": "offline_demo"}])
        self.assertEqual(metrics["accept_rate"], 0)
        self.assertEqual(metrics["simulated_accept_rate"], 1)
        self.assertAlmostEqual(metrics["composite"], .9667, places=4)

    def test_simulation_cannot_become_live_in_the_same_comparison(self):
        self.optimizer.initialize(["task"])
        with self.assertRaisesRegex(ValueError, "mode is fixed"):
            self.optimizer.set_control({"offline": False})

    def test_coach_output_without_harness_edits_is_a_clone(self):
        class NoEditCoach(FixtureEvolution):
            def _execute(inner, argv, cwd, log, label, stdin=None):
                log.write_text("I changed everything!\n")
                return 0, "I changed everything!"
        optimizer = NoEditCoach(self.optimizer.workspace, self.source)
        optimizer.initialize(["task"])
        optimizer._breed(1, ["baseline"], "clone", "mutate", {}, False, "codex")
        child = optimizer.workspace / "candidates" / "clone"
        self.assertEqual(read_json(child / "lineage.json")["outcome"], "clone")
        self.assertEqual(optimizer.snapshot()["state"]["coach_calls"], 2)

    def test_infrastructure_failure_does_not_breed_a_strategy(self):
        class BrokenEvolution(FixtureEvolution):
            def _evaluate(inner, *args):
                return {"status": "infra_fail", "offline": True, "calls": 1, "accepted": False}
        optimizer = BrokenEvolution(self.optimizer.workspace, self.source)
        state = optimizer.run(generations=1, tasks=["task"])["state"]
        self.assertEqual(state["status"], "blocked")
        self.assertEqual(state["generation"], 0)
        self.assertEqual(state["population"], ["baseline"])

    def test_quota_checkpoint_is_reevaluated_on_resume(self):
        attempts = []
        class RecoveringEvolution(FixtureEvolution):
            def _evaluate(inner, generation, name, task_index, repeat, task, control):
                attempts.append((generation, name, task_index, repeat))
                if len(attempts) == 1:
                    return {"status": "checkpoint", "reason": "quota", "offline": True, "calls": 1,
                            "retries": 1, "accepted": False}
                return super()._evaluate(generation, name, task_index, repeat, task, control)
        optimizer = RecoveringEvolution(self.optimizer.workspace, self.source)
        blocked = optimizer.run(generations=1, tasks=["task"])["state"]
        self.assertEqual(blocked["generation"], 0)
        recovered = optimizer.run(generations=1)["state"]
        self.assertEqual(recovered["generation"], 1)
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0], attempts[1])

    def test_equal_quality_prefers_fewer_calls_and_revisions(self):
        class EfficientEvolution(FixtureEvolution):
            def _evaluate(inner, generation, name, task_index, repeat, task, control):
                result = super()._evaluate(generation, name, task_index, repeat, task, control)
                result.update(score=8, calls=8 if name == "baseline" else 2,
                              review_revisions=3 if name == "baseline" else 1)
                return result
        optimizer = EfficientEvolution(self.optimizer.workspace, self.source)
        state = optimizer.run(generations=2, tasks=["task"])["state"]
        second = state["history"][1]
        self.assertNotEqual(second["champion"], "baseline")
        self.assertEqual(second["gap_vs_baseline"], 0)
        self.assertNotEqual(state["elite"], "baseline")
        metrics = second["metrics"][second["champion"]]
        self.assertEqual(metrics["calls_per_effective_result"], 2)
        self.assertEqual(metrics["revisions_per_effective_result"], 1)

    def test_parallel_start_has_one_writer_and_pause_checkpoints_inflight(self):
        started, release = threading.Event(), threading.Event()
        errors = []
        class BlockingEvolution(FixtureEvolution):
            def _evaluate(inner, *args):
                started.set()
                release.wait(5)
                return super()._evaluate(*args)
        first = BlockingEvolution(self.optimizer.workspace, self.source)
        def run():
            try:
                first.run(generations=1, tasks=["one", "two"])
            except Exception as error:
                errors.append(error)
        thread = threading.Thread(target=run)
        thread.start()
        self.assertTrue(started.wait(2))
        try:
            with self.assertRaises(EvolutionBusy):
                FixtureEvolution(first.workspace, self.source).run(generations=1)
            first.set_control({"enabled": False})
        finally:
            release.set()
            thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        state = first.snapshot()["state"]
        self.assertEqual(state["status"], "paused")
        self.assertEqual(len(state["jobs"]), 1)
        resumed = first.run(generations=1)
        self.assertEqual(resumed["state"]["generation"], 1)
        self.assertEqual(len(resumed["state"]["jobs"]), 2)

    def test_dashboard_repeated_start_does_not_create_second_worker(self):
        started, release = threading.Event(), threading.Event()
        class WaitingEvolution(FixtureEvolution):
            def _evaluate(inner, *args):
                started.set()
                release.wait(5)
                return super()._evaluate(*args)
        optimizer = WaitingEvolution(self.optimizer.workspace, self.source)
        optimizer.initialize(["task"])
        dashboard = Dashboard(optimizer)
        self.assertTrue(dashboard.start()["started"])
        self.assertTrue(started.wait(2))
        for _ in range(10):
            self.assertFalse(dashboard.start()["started"])
        optimizer.set_control({"enabled": False})
        release.set()
        dashboard.thread.join(5)
        self.assertFalse(dashboard.thread.is_alive())

    def test_emergency_stop_only_terminates_registered_process_group(self):
        self.optimizer.initialize(["task"])
        sentinel = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(15)"], start_new_session=True)
        outcome = []
        thread = threading.Thread(target=lambda: outcome.append(self.optimizer._execute(
            [sys.executable, "-c", "import time; time.sleep(15)"], self.root,
            self.root / "child.log", "test-owned-child")))
        try:
            thread.start()
            deadline = time.monotonic() + 3
            while not self.optimizer.snapshot()["state"].get("active_children") and time.monotonic() < deadline:
                time.sleep(.01)
            self.optimizer.emergency_stop()
            thread.join(5)
            self.assertFalse(thread.is_alive())
            self.assertIsNone(sentinel.poll())
            self.assertNotEqual(outcome[0][0], 0)
            self.assertEqual(self.optimizer.snapshot()["state"]["active_children"], {})
        finally:
            sentinel.terminate()
            sentinel.wait(5)

    def test_emergency_stop_kills_term_ignoring_descendant_in_another_session(self):
        self.optimizer.initialize(["task"])
        child_pid_file = self.root / "reviewer.pid"
        child_program = "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); print('ready',flush=True); time.sleep(60)"
        parent_program = (
            "import subprocess,sys,time; from pathlib import Path; "
            f"p=subprocess.Popen([sys.executable,'-c',{child_program!r}],start_new_session=True,stdout=subprocess.PIPE,text=True); "
            f"p.stdout.readline(); Path({str(child_pid_file)!r}).write_text(str(p.pid)); time.sleep(60)"
        )
        outcome = []
        thread = threading.Thread(target=lambda: outcome.append(self.optimizer._execute(
            [sys.executable, "-c", parent_program], self.root, self.root / "parent.log", "separate-reviewer")))
        pid = None
        try:
            thread.start()
            deadline = time.monotonic() + 3
            while not child_pid_file.exists() and time.monotonic() < deadline:
                time.sleep(.01)
            self.assertTrue(child_pid_file.exists())
            pid = int(child_pid_file.read_text())
            stamp = _process_stamp(pid)
            self.assertIsNotNone(stamp)
            self.optimizer.emergency_stop()
            thread.join(5)
            self.assertFalse(thread.is_alive())
            deadline = time.monotonic() + 5
            def running():
                if _process_stamp(pid) != stamp:
                    return False
                try:
                    return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0] != "Z"
                except OSError:
                    return False
            while running() and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertFalse(running(), "independent-session reviewer survived emergency stop")
        finally:
            if pid is not None and _process_stamp(pid):
                import os
                import signal
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_timeout_and_keyboard_interrupt_stop_separate_reviewer_sessions(self):
        self.optimizer.initialize(["task"])
        self.optimizer.set_control({"timeout_seconds": 1})
        for interrupted in (False, True):
            with self.subTest(interrupted=interrupted):
                pid_file = self.root / ("interrupt.pid" if interrupted else "timeout.pid")
                child_code = "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); print('ready',flush=True); time.sleep(60)"
                parent_code = ("import subprocess,sys,time; from pathlib import Path; "
                    f"p=subprocess.Popen([sys.executable,'-c',{child_code!r}],start_new_session=True,stdout=subprocess.PIPE,text=True); "
                    f"p.stdout.readline(); Path({str(pid_file)!r}).write_text(str(p.pid)); time.sleep(60)")
                communicate = subprocess.Popen.communicate
                first = True
                def interrupt_once(process, *args, **kwargs):
                    nonlocal first
                    if first:
                        first = False
                        deadline = time.monotonic() + 3
                        while not pid_file.exists() and time.monotonic() < deadline:
                            time.sleep(.01)
                        raise KeyboardInterrupt()
                    return communicate(process, *args, **kwargs)
                context = mock.patch.object(subprocess.Popen, "communicate", interrupt_once) if interrupted else contextlib.nullcontext()
                with context:
                    if interrupted:
                        with self.assertRaises(KeyboardInterrupt):
                            self.optimizer._execute([sys.executable, "-c", parent_code], self.root,
                                                    self.root / "interrupt.log", "interrupt")
                    else:
                        rc, _ = self.optimizer._execute([sys.executable, "-c", parent_code], self.root,
                                                       self.root / "timeout.log", "timeout")
                        self.assertEqual(rc, 124)
                self.assertTrue(pid_file.exists())
                pid = int(pid_file.read_text())
                try:
                    process_state = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
                except OSError:
                    process_state = None
                self.assertIn(process_state, (None, "Z"), "reviewer remained alive after cleanup")
                self.assertEqual(self.optimizer.snapshot()["state"]["active_children"], {})

    def test_dashboard_rejects_cross_origin_control(self):
        server = make_server(self.optimizer.workspace, port=0, optimizer=self.optimizer)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            headers = {"X-Control-Token": server.controller.token, "Origin": "https://unrelated.example",
                       "Content-Type": "application/json"}
            request = urllib.request.Request(base + "/api/start", data=b"{}", headers=headers)
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(request)
            self.assertEqual(error.exception.code, 403)
            self.assertFalse(self.optimizer.active())
            request = urllib.request.Request(base + "/api/control", data=b'{"parallelism": 2}',
                headers={"X-Control-Token": server.controller.token, "Origin": base, "Content-Type": "application/json"})
            with urllib.request.urlopen(request) as response:
                self.assertEqual(json.load(response)["parallelism"], 2)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(3)


class OfflineCLIIntegration(unittest.TestCase):
    def test_two_offline_generations_use_actual_engine_cli(self):
        repository = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, "-m", "autonomousmath.optimizer", "evolve", "--workspace", directory,
                                     "--offline", "--generations", "2", "--direction", "a finite sample math guarantee"],
                                    cwd=repository, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout[-4000:])
            state = read_json(Path(directory) / "evolution_state.json")
            self.assertEqual(state["generation"], 2)
            self.assertTrue(state["jobs"])
            self.assertTrue(all(job.get("offline") for job in state["jobs"].values()))
            for generation in state["history"]:
                self.assertIn("baseline", generation["metrics"])
                self.assertTrue(all(metrics["accept_rate"] == 0 for metrics in generation["metrics"].values()))
            self.assertEqual(state["coach_calls"], 0)


if __name__ == "__main__":
    unittest.main()
