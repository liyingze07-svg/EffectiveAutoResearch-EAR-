"""Ensure release verification detects both file corruption and stale aggregates."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.check_report import REPORT_ROOT, verify_report


class ReportVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.report = Path(self.temporary.name) / "report"
        shutil.copytree(REPORT_ROOT, self.report)

    def test_original_package_recomputes(self):
        result = verify_report(self.report)
        self.assertEqual(result["metrics"]["population_totals"]["episodes"], 64)

    def test_changed_source_aggregate_fails_integrity(self):
        with (self.report / "data" / "round_aggregates.csv").open("a") as handle:
            handle.write("\n")
        with self.assertRaisesRegex(ValueError, "integrity mismatch: data/round_aggregates.csv"):
            verify_report(self.report)

    def test_stale_derived_data_fails_even_with_updated_hash(self):
        path = self.report / "data" / "derived_metrics.json"
        derived = json.loads(path.read_text())
        derived["population_totals"]["episodes"] += 1
        path.write_text(json.dumps(derived))
        manifest_path = self.report / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        data = path.read_bytes()
        manifest["files"]["data/derived_metrics.json"] = {
            "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "recomputed metrics differ"):
            verify_report(self.report)


if __name__ == "__main__":
    unittest.main()
