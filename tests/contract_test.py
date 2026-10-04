"""Static contract checks for the council. No model, no network.

Run: python3 -m unittest discover -s tests -p '*_test.py'
Needs PyYAML (tests/requirements.txt).
"""

import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WF = ROOT / ".github" / "workflows"
SHARED = WF / "shared"

# The roster, in the order of the contract's table. Adding a reviewer means a
# definition, a lock, a row in the table and a "Not yours" mention in every
# other reviewer: this test fails until all are there.
ROSTER = ["Steward", "Architect", "Inspector", "Warden", "Editor"]

# Names of repos, products and people that call the council. None may appear
# in what the council ships to every caller (its definitions, shared parts,
# base principles, caller template and compiled locks), in the spirit of a
# consumer guard: the council knows no consumer.
CONSUMER_NAMES = [
    "cappz", "spire", "janus", "venue", "agent-binding", "derek", "lasalle",
    "rung", "publishing", "fleet-ops", "roger", "firstmate", "omarchy",
]


def frontmatter(path):
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    assert m, f"{path} has no frontmatter"
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def load_yaml(path):
    doc = yaml.safe_load(path.read_text())
    # YAML 1.1 reads the `on:` key as True; give it its name back.
    if True in doc:
        doc["on"] = doc.pop(True)
    return doc


def reviewer_files():
    return {name: WF / f"{name.lower()}.md" for name in ROSTER}


class Roster(unittest.TestCase):
    def test_every_reviewer_has_a_definition_and_a_lock(self):
        for name, md in reviewer_files().items():
            self.assertTrue(md.exists(), md)
            self.assertTrue(md.with_suffix(".lock.yml").exists(), f"{name}: no lock")

    def test_no_reviewer_outside_the_roster(self):
        found = sorted(p.stem for p in WF.glob("*.md"))
        self.assertEqual(found, sorted(n.lower() for n in ROSTER))

    def test_contract_table_lists_the_roster_in_order(self):
        _, body = frontmatter(SHARED / "contract.md")
        rows = re.findall(r"^\| (\w+) \| .+ \|$", body, re.M)
        self.assertEqual([r for r in rows if r != "Reviewer"], ROSTER)


class Scope(unittest.TestCase):
    def test_each_reviewer_states_its_scope_and_checks(self):
        for name, md in reviewer_files().items():
            _, body = frontmatter(md)
            with self.subTest(name):
                self.assertIn(f"\n# {name}\n", body)
                self.assertRegex(body, r"Your scope: \*\*.+")
                self.assertIn(f"Name yourself `{name}` in the review's first line", " ".join(body.split()))
                checks = re.findall(r"^(\d+)\. ", body, re.M)
                self.assertGreaterEqual(len(checks), 3, "fewer than 3 numbered checks")
                self.assertEqual(checks, [str(i) for i in range(1, len(checks) + 1)], "checks not numbered 1..n")

    def test_not_yours_names_every_other_reviewer(self):
        for name, md in reviewer_files().items():
            _, body = frontmatter(md)
            with self.subTest(name):
                m = re.search(r"Not yours, drop it:(.+?)(\n\n|\Z)", body, re.S)
                self.assertTrue(m, "no 'Not yours, drop it:' paragraph")
                para = m.group(1)
                for other in ROSTER:
                    if other != name:
                        self.assertIn(f"({other})", para)
                self.assertNotIn(f"({name})", para)

    def test_reviewers_share_one_frontmatter(self):
        # Only the description and the import inputs differ, so the reviewers
        # stay equal: same trigger, inputs, permissions, turns and minutes.
        shapes = {}
        for name, md in reviewer_files().items():
            fm, _ = frontmatter(md)
            self.assertEqual(fm["imports"], [{"uses": "shared/contract.md", "with": {"name": name, "id": name.lower()}}])
            self.assertTrue(fm["description"].startswith(f"Review council, {name}: "))
            self.assertIs(fm.get("inlined-imports"), True, f"{name}: inlined-imports must be true")
            shapes[name] = {k: v for k, v in fm.items() if k not in ("description", "imports")}
        first = shapes[ROSTER[0]]
        for name, shape in shapes.items():
            self.assertEqual(shape, first, f"{name} frontmatter differs from {ROSTER[0]}")


class Locks(unittest.TestCase):
    def test_each_lock_is_a_self_contained_reusable_workflow(self):
        for name, md in reviewer_files().items():
            lock_path = md.with_suffix(".lock.yml")
            text = lock_path.read_text()
            lock = load_yaml(lock_path)
            with self.subTest(name):
                self.assertNotIn("runtime-import", text, "a runtime import reads a file the caller does not have")
                call = lock["on"]["workflow_call"]
                self.assertEqual(call["inputs"]["model"]["type"], "string")
                self.assertIs(call["secrets"]["OPENROUTER_API_KEY"]["required"], True)
                self.assertEqual(lock["name"], name)

    def test_verdict_status_uses_the_reviewer_name_and_head_sha(self):
        for name, md in reviewer_files().items():
            lock = load_yaml(md.with_suffix(".lock.yml"))
            for job in ("verdict_pending", "verdict"):
                with self.subTest(f"{name} {job}"):
                    step = lock["jobs"][job]["steps"][-1]
                    self.assertEqual(step["env"]["REVIEWER"], name)
                    self.assertEqual(step["env"]["HEAD_SHA"], "${{ github.event.pull_request.head.sha }}")
                    self.assertNotIn("context.workflow", step["with"]["script"])
                    self.assertNotIn("context.sha", step["with"]["script"])

    def test_no_concurrency_group_keys_on_the_callers_workflow_name(self):
        # Inside a called workflow github.workflow is the caller's name: four
        # reviewers in one caller would share a group and cancel each other.
        for name, md in reviewer_files().items():
            lock = load_yaml(md.with_suffix(".lock.yml"))
            groups = [lock.get("concurrency", {}).get("group", "")]
            groups += [j.get("concurrency", {}).get("group", "") for j in lock["jobs"].values()]
            for g in groups:
                self.assertNotIn("github.workflow", g, f"{name}: {g}")


class Caller(unittest.TestCase):
    def setUp(self):
        self.caller = load_yaml(ROOT / "caller" / "review-council.yml")

    def test_runs_on_every_ready_pr_event_and_cancels_the_older_head(self):
        self.assertEqual(self.caller["on"]["pull_request"]["types"], ["opened", "reopened", "ready_for_review", "synchronize"])
        self.assertIs(self.caller["concurrency"]["cancel-in-progress"], True)
        self.assertIn("github.event.pull_request.number", self.caller["concurrency"]["group"])
        self.assertEqual(self.caller["permissions"], {})

    def test_each_job_grants_what_its_lock_needs(self):
        text = (ROOT / "caller" / "review-council.yml").read_text()
        for job_id, job in self.caller["jobs"].items():
            with self.subTest(job_id):
                m = re.match(r"witt3rd/review-council/\.github/workflows/(\w+)\.lock\.yml@COUNCIL_SHA$", job["uses"])
                self.assertTrue(m, job["uses"])
                self.assertEqual(m.group(1), job_id)
                self.assertIn(f"{job_id}.lock.yml@COUNCIL_SHA # COUNCIL_TAG\n", text)
                lock = load_yaml(WF / f"{job_id}.lock.yml")
                needed = {}
                for j in lock["jobs"].values():
                    for scope, level in (j.get("permissions") or {}).items():
                        if needed.get(scope) != "write":
                            needed[scope] = level
                granted = job["permissions"]
                for scope, level in needed.items():
                    self.assertIn(scope, granted, f"{job_id}: {scope} not granted")
                    if level == "write":
                        self.assertEqual(granted[scope], "write", f"{job_id}: {scope} must be write")
                inputs = lock["on"]["workflow_call"]["inputs"]
                for key in job.get("with", {}):
                    self.assertIn(key, inputs)
                for secret, spec in lock["on"]["workflow_call"]["secrets"].items():
                    if spec.get("required"):
                        self.assertIn(secret, job["secrets"])
                self.assertIn("!github.event.pull_request.draft", job["if"])
                self.assertIn("github.event.pull_request.head.repo.full_name == github.repository", job["if"])

    def test_the_commented_editor_job_matches_a_lock(self):
        text = (ROOT / "caller" / "review-council.yml").read_text()
        for m in re.finditer(r"workflows/(\w+)\.lock\.yml@", text):
            self.assertIn(m.group(1).capitalize(), ROSTER)


class ConsumerGuard(unittest.TestCase):
    def test_the_council_names_no_consumer(self):
        shipped = list(WF.glob("*.md")) + list(WF.glob("*.lock.yml")) + list(SHARED.glob("*.md"))
        shipped += list((ROOT / ".github" / "principles").glob("*.md")) + list((ROOT / "caller").glob("*"))
        pattern = re.compile(r"\b(" + "|".join(re.escape(n) for n in CONSUMER_NAMES) + r")\b", re.I)
        for path in shipped:
            for no, line in enumerate(path.read_text().splitlines(), 1):
                m = pattern.search(line)
                self.assertIsNone(m, f"{path.relative_to(ROOT)}:{no} names a consumer: {m and m.group(0)}")


if __name__ == "__main__":
    unittest.main()
