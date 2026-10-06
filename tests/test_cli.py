"""Check thin CLI contracts without authentication, network, or model calls."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ear import cli, workspaces


def snapshot(path):
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts}


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="EAR CLI spaces ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_cli(self, *args, expected=0):
        result = subprocess.run(["bash", str(ROOT / "ear.sh"), *map(str, args)],
            cwd=self.root, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def test_help_and_doctor_from_external_directory(self):
        self.assertIn("rebuttal", self.run_cli("--help").stdout)
        self.assertIn("standard library only", self.run_cli("doctor", "--offline").stdout)

    def test_report_json_is_recomputed_release_metrics(self):
        actual = json.loads(self.run_cli("demo", "report", "--json").stdout)
        expected = json.loads((ROOT / "docs/technical-report/v6/data/derived_metrics.json").read_text())
        self.assertEqual(actual, expected)
        text = self.run_cli("demo", "report").stdout
        self.assertIn("52.8%", text)
        self.assertIn("Human time was not measured", text)

    def test_offline_demo_no_clobber(self):
        out = self.root / "demo output"
        self.run_cli("demo", "check", "--output", out)
        summary = json.loads((out / "SUMMARY.json").read_text())
        self.assertEqual(summary["model_calls"], 0)
        before = snapshot(out)
        self.run_cli("demo", "check", "--output", out, expected=2)
        self.assertEqual(snapshot(out), before)

    def test_idea_forwards_original_arguments_and_preserves_workspace(self):
        out = self.root / "idea output"
        arguments = ["idea", "--survey", "query with spaces", "--workspace", str(out), "--codex-cli"]
        with patch.object(cli, "_run", return_value=7) as runner:
            self.assertEqual(cli.main(arguments), 7)
        self.assertEqual(runner.call_args.args[0], ["bash", str(out / "run.sh"),
                                                  "--survey", "query with spaces", "--codex-cli"])
        self.assertTrue((out / "skills/idea-pipeline/SKILL.md").is_file())
        (out / "outputs").mkdir()
        (out / "outputs/private-note.txt").write_text("keep")
        before = snapshot(out)
        self.run_cli("idea", "--status", "--workspace", out)
        self.assertEqual(snapshot(out), before)

    def test_idea_refuses_unmarked_and_wrong_workflow_directories(self):
        out = self.root / "existing"
        out.mkdir()
        (out / "mine.txt").write_text("keep")
        before = snapshot(out)
        self.run_cli("idea", "query", "--workspace", out, expected=2)
        self.assertEqual(snapshot(out), before)
        (out / workspaces.MARKER).write_text('{"workflow":"rebuttal"}')
        self.run_cli("idea", "query", "--workspace", out, expected=2)

    def test_idea_status_and_help_do_not_initialize(self):
        out = self.root / "missing"
        self.run_cli("idea", "--status", "--workspace", out, expected=2)
        self.assertFalse(out.exists())
        self.run_cli("idea", "--help", "--workspace", out)
        self.assertFalse(out.exists())

    def test_workspace_cannot_be_nested_in_copied_sources(self):
        # Keep the guard test entirely in a temporary fake checkout.
        source = self.root / "fake checkout"
        with patch.object(workspaces, "ROOT", source):
            with self.assertRaisesRegex(ValueError, "source directories"):
                workspaces.prepare_idea(source / "autovibeidea/tools/new-run", create=True)
            with self.assertRaisesRegex(ValueError, "source directories"):
                workspaces.initialize_rebuttal(source / "rebuttal/harness/new-run", "demo")
        self.assertFalse(source.exists())

    def test_resource_copy_excludes_secrets_outputs_and_symlinks(self):
        source, destination = self.root / "source", self.root / "target"
        source.mkdir()
        for name in ("safe.py", ".env", "config.local.json", "ignored.bin"):
            (source / name).write_text("fixture")
        (source / "outputs").mkdir()
        (source / "outputs/private.md").write_text("private")
        (source / "linked.py").symlink_to(source / "safe.py")
        workspaces._copy_resources(source, destination)
        self.assertEqual(set(snapshot(destination)), {"safe.py"})

    def test_math_passthrough_and_exit_status(self):
        arguments = ["run", "--config", "my config.json", "--candidate-root", "candidate path",
                     "--workspace", "math workspace", "--max-calls", "2"]
        with patch.object(cli, "_run", return_value=2) as runner:
            self.assertEqual(cli.main(["math", *arguments]), 2)
        self.assertEqual(runner.call_args.args[0], [sys.executable, "-B", "-m", "autonomousmath", *arguments])
        self.assertEqual(runner.call_args.kwargs["env"]["PYTHONPATH"].split(os.pathsep)[0], str(ROOT))

    def test_math_relative_config_workspace_offline_and_status(self):
        (self.root / "my config.json").write_text(json.dumps({"offline": True,
            "workspace": "math workspace", "episodes": 1}))
        result = self.run_cli("math", "run", "--config", "my config.json")
        self.assertEqual(json.loads(result.stdout)["status"], "offline_demo")
        workspace = self.root / "math workspace"
        self.assertTrue((workspace / "state.json").is_file())
        status = json.loads(self.run_cli("status", workspace, "--workflow", "math").stdout)
        self.assertEqual(status["status"], "offline_demo")
        self.run_cli("stop", workspace, "--workflow", "math")
        self.assertTrue((workspace / "STOP").is_file())

    def test_rebuttal_init_dry_run_and_no_clobber(self):
        workspace = self.root / "rebuttal output"
        self.run_cli("rebuttal", "init", "--from-example", "--workspace", workspace, "--paper", "my-paper")
        campaign = workspace / "campaigns/my-paper"
        for name in ("CLAUDE", "GOAL", "SPEC", "VERIFY", "RESOURCE"):
            self.assertNotIn("{{", (campaign / f"{name}.md").read_text())
        self.assertFalse((workspace / "rebuttal_verifier/.env").exists())
        self.assertTrue((workspace / "harness/shared-assets/rebuttal-tips.md").is_file())
        before = snapshot(workspace)
        self.run_cli("rebuttal", "init", "--from-example", "--workspace", workspace, expected=2)
        result = self.run_cli("rebuttal", "run", "--workspace", workspace,
                              "--paper", "my-paper", "--dry-run", "--from", "r1")
        self.assertIn("DRY", result.stdout)
        self.assertEqual(snapshot(workspace), before)
        status = json.loads(self.run_cli("status", workspace, "--workflow", "rebuttal").stdout)
        self.assertEqual(status["process_status"], "not_tracked")
        self.assertIsNone(status["campaigns"][0]["reviewer_results"])

    def test_rebuttal_rejects_invalid_slug_before_creating_workspace(self):
        workspace = self.root / "should not exist"
        self.run_cli("rebuttal", "init", "--from-example", "--workspace", workspace,
                     "--paper", "../escape", expected=2)
        self.assertFalse(workspace.exists())

    def test_rebuttal_stop_reports_unsupported_without_writes(self):
        result = self.run_cli("stop", "absent", "--workflow", "rebuttal", expected=2)
        self.assertIn("no managed stop", result.stderr)
        self.assertFalse((self.root / "absent").exists())


if __name__ == "__main__":
    unittest.main()
