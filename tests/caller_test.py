"""Caller conformance: a sample repo adopting the council, offline.

Fills caller/review-council.yml as an adopter would (every reviewer pinned to
one SHA, tag as comment), then checks it against the locks it calls and runs
the pin report on it with the GitHub calls stubbed. No model, no network.

Run: python3 -m unittest discover -s tests -p '*_test.py'
"""

import importlib.util
import re
import unittest
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parent.parent
WF = ROOT / ".github" / "workflows"
FAKE_SHA = "a" * 40
TAG = "v9.9.9"
CALLER_REPO = "example/sample"
COUNCIL = "witt3rd/review-council"
CODE_REVIEWERS = ["steward", "architect", "inspector", "warden"]

spec = importlib.util.spec_from_file_location("pins", ROOT / "tools" / "pins.py")
pins = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pins)


def sample_caller(documents=False):
    """The template as an adopter fills it: pins set; a documents repo swaps
    the Warden for the Editor."""
    text = (ROOT / "caller" / "review-council.yml").read_text()
    text = text.replace("COUNCIL_SHA # COUNCIL_TAG", f"{FAKE_SHA} # {TAG}")
    if documents:
        lines, out, in_editor = text.splitlines(), [], False
        for line in lines:
            if line.startswith("  # editor:"):
                in_editor = True
            if in_editor and line.startswith("  # "):
                line = "  " + line[4:]
            out.append(line)
        text = "\n".join(out) + "\n"
        text = re.sub(r"\n  warden:\n(?:    .*\n|\n(?=    ))*", "\n", text)
    return text


def parse(text):
    doc = yaml.safe_load(text)
    if True in doc:
        doc["on"] = doc.pop(True)
    return doc


def lock(name):
    doc = yaml.safe_load((WF / f"{name}.lock.yml").read_text())
    if True in doc:
        doc["on"] = doc.pop(True)
    return doc


class CallerConformance(unittest.TestCase):
    def check(self, documents, expected):
        text = sample_caller(documents)
        doc = parse(text)
        jobs = doc["jobs"]
        self.assertEqual(sorted(jobs), sorted(expected))
        for name, job in jobs.items():
            m = re.fullmatch(rf"{COUNCIL}/\.github/workflows/(\w+)\.lock\.yml@{FAKE_SHA}", job["uses"])
            self.assertTrue(m, f"{name}: uses is not a full-SHA pin: {job['uses']}")
            self.assertEqual(m.group(1), name)
            called = lock(name)["on"]["workflow_call"]
            # Every input the caller passes exists, and no secret the lock
            # requires is left unpassed.
            for key in job.get("with", {}):
                self.assertIn(key, called["inputs"], f"{name}: unknown input {key}")
            for key, spec_ in called.get("secrets", {}).items():
                if spec_.get("required"):
                    self.assertIn(key, job["secrets"], f"{name}: required secret {key} not passed")
            for key in job["secrets"]:
                self.assertIn(key, called.get("secrets", {}), f"{name}: unknown secret {key}")
            # A called workflow gets no more permission than the caller grants.
            for jname, ljob in lock(name)["jobs"].items():
                perms = ljob.get("permissions")
                if isinstance(perms, dict):
                    for scope, level in perms.items():
                        granted = job["permissions"].get(scope)
                        ok = granted == "write" or granted == level
                        self.assertTrue(ok, f"{name}/{jname} needs {scope}: {level}, caller grants {granted}")
        # Pins carry the tag as a comment, all alike.
        self.assertEqual(len(re.findall(rf"^    uses: .*@{FAKE_SHA} # {TAG}$", text, re.M)), len(expected))

    def test_code_repo_caller(self):
        self.check(False, CODE_REVIEWERS)

    def test_documents_repo_caller(self):
        self.check(True, ["steward", "architect", "inspector", "editor"])

    def test_every_job_skips_drafts_and_forks(self):
        for name, job in parse(sample_caller())["jobs"].items():
            self.assertIn("draft", job["if"], name)
            self.assertIn("head.repo.full_name", job["if"], name)

    def test_template_has_no_unfilled_placeholder_once_pinned(self):
        self.assertNotIn("COUNCIL_", sample_caller())


class PinReport(unittest.TestCase):
    def run_report(self, caller_text, newest=TAG, sha=FAKE_SHA):
        with mock.patch.object(pins, "releases", return_value=({newest: sha}, newest)), \
             mock.patch.object(pins, "gh", return_value=caller_text):
            return pins.report([CALLER_REPO], COUNCIL)

    def test_sample_caller_is_current(self):
        out = self.run_report(sample_caller())
        self.assertIn(f"| {CALLER_REPO} | {TAG} (steward, architect, inspector, warden) | current |", out)

    def test_behind_when_a_newer_release_exists(self):
        with mock.patch.object(pins, "releases", return_value=({TAG: FAKE_SHA, "v10.0.0": "b" * 40}, "v10.0.0")), \
             mock.patch.object(pins, "gh", return_value=sample_caller()):
            out = pins.report([CALLER_REPO], COUNCIL)
        self.assertIn("behind: newest is v10.0.0", out)

    def test_mixed_pins_are_flagged(self):
        text = sample_caller().replace(FAKE_SHA, "c" * 40, 1)
        self.assertIn("reviewers pin different commits", self.run_report(text))

    def test_wrong_comment_is_flagged(self):
        text = sample_caller().replace(f"# {TAG}", "# v1.0.0")
        self.assertIn("comment says v1.0.0", self.run_report(text))

    def test_unreadable_caller_is_reported(self):
        with mock.patch.object(pins, "releases", return_value=({TAG: FAKE_SHA}, TAG)), \
             mock.patch.object(pins, "gh", return_value=None):
            self.assertIn("unreadable", pins.report([CALLER_REPO], COUNCIL))

    def test_callers_txt_lists_only_repos(self):
        for line in (ROOT / "callers.txt").read_text().splitlines():
            if line.strip() and not line.startswith("#"):
                self.assertRegex(line.strip(), r"^[\w.-]+/[\w.-]+$")


if __name__ == "__main__":
    unittest.main()
