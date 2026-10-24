"""Multi-round fixtures: shape and scoring of the owner's follow-up verdict, offline."""

import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("evalmod", ROOT / "tests" / "eval" / "eval.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)
MULTI = [n for n in ev.fixtures(["inspector-off-by-one-fixed", "inspector-off-by-one-unfixed"])]


class Rounds(unittest.TestCase):
    def test_default_set_leaves_multi_round_out(self):
        self.assertFalse(set(MULTI) & set(ev.fixtures()))
        self.assertEqual(len(MULTI), 2)

    def test_each_round_has_files_and_expect(self):
        for n in MULTI:
            d = ev.FIXTURES / "prs" / n
            self.assertTrue(any((d / "rounds" / "2" / "files").rglob("*.py")))
            self.assertIn(ev.load_pr(n)["rounds"][0]["expect"]["owner_min"], ("PASS", "BLOCK"))

    def score(self, name, owner_review, verdict):
        def fake_sh(*a, **k):
            if "contents" in " ".join(a):
                return f"x@{'a' * 40} y"
            if a[-1].endswith("/reviews"):
                return json.dumps([[{"user": {"type": "Bot"}, "body": b, "commit_id": "h", "html_url": "u"}
                                    for b in [owner_review] + [f"{r}: no findings" for r in ev.ROSTER if r != "Inspector"]]])
            return json.dumps({"statuses": [{"context": f"{r} verdict", "state": verdict if r == "Inspector" else "success"} for r in ev.ROSTER]})
        with mock.patch.object(ev, "sh", fake_sh), mock.patch.object(ev, "run_cost", lambda *a: (0, [])), \
                mock.patch.object(ev, "gh_json", lambda *a: [{"number": 1, "url": "u", "headRefOid": "h"}]):
            return ev.score_pr("r", name, "a" * 40, rnd=2)

    def test_fixed_passes_only_when_cleared(self):
        self.assertTrue(self.score("inspector-off-by-one-fixed", "Inspector: no findings", "success")["pass"])
        r = self.score("inspector-off-by-one-fixed", "Inspector: 1 finding (1 BLOCK, 0 FIX, 0 NOTE)", "failure")
        self.assertFalse(r["pass"])

    def test_unfixed_passes_only_when_still_blocked(self):
        self.assertTrue(self.score("inspector-off-by-one-unfixed", "Inspector: 1 finding (1 BLOCK, 0 FIX, 0 NOTE)", "failure")["pass"])
        self.assertFalse(self.score("inspector-off-by-one-unfixed", "Inspector: no findings", "success")["pass"])


if __name__ == "__main__":
    unittest.main()
