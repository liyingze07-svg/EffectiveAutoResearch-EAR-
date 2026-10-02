import json
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

from autonomousmath.referee import gate
from autonomousmath.checking import final_check


class RefereeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.campaign = self.root / "task"
        (self.campaign / "paper").mkdir(parents=True)
        (self.campaign / "proof.md").write_text("Synthetic proof: a real number squared is nonnegative.")
        (self.campaign / "paper/main.tex").write_text("\\documentclass{article}\n\\begin{document}Synthetic manuscript.\\end{document}\n")

    def test_fixture_is_labelled_and_review_feedback_reaches_next_round(self):
        rejected = gate.review(self.campaign, {"review_round": 1}, self.root / "reviews/one", offline=True)
        accepted = gate.review(self.campaign, {"review_round": 2}, self.root / "reviews/two", offline=True)
        self.assertFalse(rejected["accepted"])
        self.assertEqual(rejected["status"], "rejected")
        self.assertTrue(accepted["accepted"])
        self.assertTrue(accepted["offline"])
        self.assertEqual(accepted["status"], "offline_demo")
        self.assertIn("Synthetic", accepted["reviews"][0]["summary"])

    def test_terminal_review_cannot_be_written_in_worker_directory(self):
        with self.assertRaises(ValueError):
            gate.review(self.campaign, {}, self.campaign / "review", offline=True)

    def test_source_version_covers_proof_and_figure_assets(self):
        before = gate.content_hash(self.campaign)
        (self.campaign / "proof.md").write_text("Changed proof.")
        self.assertNotEqual(before, gate.content_hash(self.campaign))
        before = gate.content_hash(self.campaign)
        (self.campaign / "paper/figure.png").write_bytes(b"synthetic image")
        self.assertNotEqual(before, gate.content_hash(self.campaign))

    def test_symlink_cannot_import_host_content_into_review(self):
        (self.campaign / "paper/private.tex").symlink_to(self.root / "outside.tex")
        result = gate.review(self.campaign, {}, self.root / "reviews", offline=True)
        self.assertEqual(result["status"], "blocked")

    def test_one_reject_blocks_dual_accept(self):
        rows = [dict(verdict="Accept (Poster)", quality="Solid", summary="Review", findings=[], backend="codex"),
                dict(verdict="Reject", quality="Incremental", summary="Review", findings=["Gap"], backend="codex")]
        with patch.object(gate, "_compile", return_value={}), patch.object(gate, "_review_cli", side_effect=rows):
            result = gate.review(self.campaign, {}, self.root / "reviews")
        self.assertFalse(result["accepted"])
        self.assertEqual(result["status"], "rejected")

    def test_modifying_source_during_review_invalidates_accept(self):
        def reviewer(*args):
            (self.campaign / "proof.md").write_text("Changed after review started.")
            return dict(verdict="Accept", quality="Solid", summary="Review", findings=[], backend="codex")
        with patch.object(gate, "_compile", return_value={}), patch.object(gate, "_review_cli", side_effect=reviewer):
            result = gate.review(self.campaign, {}, self.root / "reviews")
        self.assertFalse(result["accepted"])
        self.assertEqual(result["status"], "blocked")
        self.assertIn("stale", result["feedback"])

    def test_missing_formalizer_is_deferred(self):
        result = final_check(self.campaign, {}, self.root / "check")
        self.assertEqual(result["status"], "deferred")
        self.assertEqual(result["coverage"], [])

    def test_external_checker_reports_claim_coverage_for_same_version(self):
        script = self.root / "checker.py"
        script.write_text("import json,sys,pathlib\n"
                          "r=json.loads(pathlib.Path(sys.argv[1]).read_text())\n"
                          "r.update(status='partial',coverage=['Lemma 1'])\n"
                          "pathlib.Path(r['output_file']).write_text(json.dumps(r))\n")
        result = final_check(self.campaign, {"final_check_command": [sys.executable, str(script), "{request}"]},
                             self.root / "checks")
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["coverage"], ["Lemma 1"])
        self.assertEqual(result["paper_content_hash"], gate.content_hash(self.campaign))

    def test_final_checker_editing_paper_invalidates_result(self):
        script = self.root / "checker.py"
        script.write_text("import json,sys,pathlib\n"
                          "r=json.loads(pathlib.Path(sys.argv[1]).read_text())\n"
                          "pathlib.Path(r['campaign_dir'],'proof.md').write_text('Changed proof')\n"
                          "r.update(status='verified',coverage=['Lemma 1'])\n"
                          "pathlib.Path(r['output_file']).write_text(json.dumps(r))\n")
        result = final_check(self.campaign, {"final_check_command": [sys.executable, str(script), "{request}"]},
                             self.root / "checks")
        self.assertEqual(result["status"], "blocked")
        self.assertIn("changed", result["reason"])


if __name__ == "__main__":
    unittest.main()
