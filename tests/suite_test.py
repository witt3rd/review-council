"""The suite runner's cap logic and refusals, offline."""

import importlib.util
import json
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("suite", ROOT / "tests" / "eval" / "suite.py")
suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suite)

BASE = {"fixtures": [{"fixture": "a", "cost_usd": 1.0}, {"fixture": "b", "cost_usd": 2.0}]}


class Suite(unittest.TestCase):
    def test_estimate_scales_with_fixtures(self):
        self.assertEqual(suite.estimate(BASE, None), 3.0)
        self.assertEqual(suite.estimate(BASE, ["b"]), 2.0)
        self.assertIsNone(suite.estimate(BASE, ["zzz"]))

    def test_verdict(self):
        ok = {"cost_usd": 3.0, "pass": True, "passed": 2, "total": 2}
        self.assertEqual(suite.verdict(ok, 8)[0], 0)
        self.assertEqual(suite.verdict({**ok, "cost_usd": 9.0}, 8)[0], 1)
        self.assertEqual(suite.verdict({**ok, "pass": False, "passed": 1}, 8)[0], 1)

    def run_main(self, *extra, baseline=BASE):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "b.json"
            p.write_text(json.dumps(baseline))
            return suite.main(["--sha", "x", "--baseline", str(p), *extra])

    def test_refuses_when_estimate_over_cap(self):
        self.assertEqual(self.run_main("--max-usd", "1"), 3)

    def test_refuses_without_baseline_cost(self):
        self.assertEqual(self.run_main(baseline={"fixtures": [{"fixture": "a"}]}), 3)

    def test_dry_run_spends_nothing(self):
        self.assertEqual(self.run_main("--dry-run"), 0)

    def test_subset_against_full_baseline_is_no_regression(self):
        full = {"fixtures": [{"fixture": "a", "cost_usd": 1.0, "pass": True}, {"fixture": "b", "cost_usd": 2.0, "pass": True}],
                "passed": 2, "total": 2}
        seen = {}

        def fake_run(cmd, **kw):
            if "score" in cmd:
                seen["baseline"] = json.loads(Path(cmd[cmd.index("--baseline") + 1]).read_text())
                rec = {"cost_usd": 1.0, "pass": True, "passed": 1, "total": 1}
                return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(rec))
            return subprocess.CompletedProcess(cmd, 0)

        with mock.patch.object(suite.subprocess, "run", fake_run):
            code = self.run_main("--only", "a", baseline=full)
        self.assertEqual(code, 0)
        self.assertEqual((seen["baseline"]["passed"], seen["baseline"]["total"]), (1, 1))


if __name__ == "__main__":
    unittest.main()
