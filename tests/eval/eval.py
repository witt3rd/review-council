#!/usr/bin/env python3
"""Golden-PR evals: run a council candidate against frozen fixture PRs, score it.

  eval.py run   --sha SHA    pin the fixture repo's caller to SHA and open one
                             fresh PR per fixture (needs push rights there)
  eval.py score --sha SHA    score those PRs; exit 0 pass, 1 fail, 2 pending
                             (needs only read access: the fixture repo is public)
  eval.py followup --sha SHA --only NAME ...
                             push the next round's commit to those fixtures' open
                             PRs, once the round before is fully reviewed
  eval.py score --sha SHA --round 2 --only NAME ...   score the follow-up heads
  eval.py locks [--sha SHA]  the hash of the five locks, as an eval record holds it

The fixture repo is rebuilt from tests/fixtures/ on every run: `base/` is its
main branch plus the caller (made from caller/review-council.yml, all five
reviewers, pinned to SHA), and each `prs/<name>/` is one PR: `files/` laid
over main, `pr.json` its title, body and expected outcome. Every run opens new
PRs, so every reviewer sees a first review (no Rounds, no Memory carried over).

Scoring, per fixture PR, against the head commit:
  - every reviewer posted a review of the head and set a final verdict;
  - the owner (pr.json `expect.owner`) raised at least `owner_min`
    (BLOCK, or FIX meaning BLOCK or FIX); an owner BLOCK fails its verdict;
  - no other reviewer raised a BLOCK, and every other verdict passed, except
    the reviewers `expect.allowed` names: their scope also reaches the PR (the
    Warden may flag an injection), so they may, but need not.
Later rounds: a fixture whose pr.json has `rounds` (a list of {"message",
"expect"}) is left out of the default set; name it with --only. Round k's
commit is `prs/<name>/rounds/<k>/files/` laid over the branch. Its expect may
say `owner_min: "PASS"`: the owner must then raise no BLOCK and pass (the push
fixed the earlier BLOCK); `owner_min: "BLOCK"` means it must still BLOCK.
A clean fixture (`owner: null`) passes only with no BLOCK and every verdict green.
Uses the gh CLI for every GitHub call. Standard library only.
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"
ROSTER = ["Steward", "Architect", "Inspector", "Warden", "Editor"]
DEFAULT_REPO = "witt3rd/review-council-fixtures"
CALLER_PATH = ".github/workflows/review-council.yml"
FIRST_LINE = re.compile(r"^(\w+): (?:(\d+) findings? \(([^)]*)\)|no findings\b)")


def sh(*args, cwd=None, capture=True):
    r = subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=capture)
    return r.stdout if capture else ""


def gh_json(*args):
    return json.loads(sh("gh", *args) or "null")


def fixtures(only=None):
    names = sorted(p.name for p in (FIXTURES / "prs").iterdir() if p.is_dir())
    if not only:
        names = [n for n in names if "rounds" not in load_pr(n)]
    return [n for n in names if not only or n in only]


def load_pr(name):
    return json.loads((FIXTURES / "prs" / name / "pr.json").read_text())


def caller_text(sha, label):
    """The caller template with every reviewer enabled and pinned to `sha`."""
    text = (ROOT / "caller" / CALLER_PATH.split("/")[-1]).read_text()
    out, in_editor = [], False
    for line in text.splitlines():
        if line.startswith("  # editor:"):
            in_editor = True
        if in_editor and line.startswith("  # "):
            line = "  " + line[4:]
        out.append(line)
    text = "\n".join(out) + "\n"
    return text.replace("@COUNCIL_SHA # COUNCIL_TAG", f"@{sha} # {label}")


def locks_sha256(sha):
    h = hashlib.sha256()
    for name in ROSTER:
        path = f".github/workflows/{name.lower()}.lock.yml"
        h.update(path.encode() + b"\0")
        h.update(sh("git", "show", f"{sha}:{path}", cwd=ROOT).encode())
    return h.hexdigest()


def copy_tree(src, dst):
    for p in src.rglob("*"):
        if p.is_file():
            target = dst / p.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)


def cmd_run(args):
    sha = sh("git", "rev-parse", args.sha, cwd=ROOT).strip()
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "fixtures"
        sh("gh", "repo", "clone", args.repo, str(work), "--", "-q")
        has_main = sh("git", "ls-remote", "--heads", "origin", "main", cwd=work).strip()
        if has_main:
            sh("git", "checkout", "-q", "main", cwd=work)
        else:
            sh("git", "checkout", "-q", "--orphan", "main", cwd=work)
        for p in work.iterdir():
            if p.name != ".git":
                shutil.rmtree(p) if p.is_dir() else p.unlink()
        copy_tree(FIXTURES / "base", work)
        (work / CALLER_PATH).parent.mkdir(parents=True, exist_ok=True)
        (work / CALLER_PATH).write_text(caller_text(sha, f"candidate {sha[:7]}"))
        sh("git", "add", "-A", cwd=work)
        if sh("git", "status", "--porcelain", cwd=work).strip():
            sh("git", "commit", "-qm", f"eval: council candidate {sha}", cwd=work)
            sh("git", "push", "-q", "origin", "main", cwd=work)
        for name in fixtures(args.only):
            pr = json.loads((FIXTURES / "prs" / name / "pr.json").read_text())
            branch = f"fixture/{name}"
            sh("git", "checkout", "-q", "-B", branch, "main", cwd=work)
            copy_tree(FIXTURES / "prs" / name / "files", work)
            sh("git", "add", "-A", cwd=work)
            sh("git", "commit", "-qm", pr["title"], cwd=work)
            sh("git", "push", "-qf", "origin", branch, cwd=work)
            for old in gh_json("pr", "list", "-R", args.repo, "--head", branch, "--state", "open", "--json", "number"):
                sh("gh", "pr", "close", "-R", args.repo, str(old["number"]), "--comment", f"Superseded by the eval of {sha[:7]}.")
            url = sh("gh", "pr", "create", "-R", args.repo, "--base", "main", "--head", branch,
                     "--title", pr["title"], "--body", pr["body"]).strip()
            print(f"{name}: {url}")
            time.sleep(2)
    return 0


def review_line(body):
    """The reviewer's line: the first not blank and not in a leading quote (as
    in shared/verdict.md, which a threat-detection caution sits above)."""
    return next((l.strip() for l in (body or "").split("\n") if l.strip() and not l.strip().startswith(">")), "")


def parse_review(body):
    m = FIRST_LINE.match(review_line(body))
    if not m:
        return None
    counts = {"BLOCK": 0, "FIX": 0, "NOTE": 0}
    if m.group(2) is not None:
        # "(1 BLOCK, 2 FIX, 0 NOTE)"; a reviewer may leave out a zero count.
        for n, sev in re.findall(r"(\d+) (BLOCK|FIX|NOTE)", m.group(3)):
            counts[sev] = int(n)
    return counts


def score_pr(repo, name, sha, number=None, head=None, rnd=1):
    """Score one fixture PR: the open PR of its branch, or `number` at `head`
    (re-scoring a recorded eval after newer runs closed its PRs)."""
    spec = load_pr(name)
    if rnd > 1:
        if len(spec.get("rounds", [])) < rnd - 1:
            return {"fixture": name, "skipped": True, "pending": False, "pass": True, "problems": []}
        expect = spec["rounds"][rnd - 2]["expect"]
    else:
        expect = spec["expect"]
    if number:
        pr = {"number": number, "url": f"https://github.com/{repo}/pull/{number}", "headRefOid": head}
    else:
        prs = gh_json("pr", "list", "-R", repo, "--head", f"fixture/{name}", "--state", "open", "--json", "number,url,headRefOid")
        if not prs:
            return {"fixture": name, "pending": True, "problems": ["no open fixture PR"]}
        pr = prs[0]
    head = pr["headRefOid"]
    caller = sh("gh", "api", "-H", "Accept: application/vnd.github.raw", f"repos/{repo}/contents/{CALLER_PATH}?ref={head}")
    if f"@{sha} " not in caller:
        return {"fixture": name, "url": pr["url"], "pending": True, "problems": [f"PR head's caller is not pinned to {sha[:7]}"]}
    reviews = json.loads(sh("gh", "api", "--paginate", "--slurp", f"repos/{repo}/pulls/{pr['number']}/reviews"))
    reviews = [r for page in reviews for r in page]
    statuses = json.loads(sh("gh", "api", f"repos/{repo}/commits/{head}/status"))["statuses"]
    by_context = {s["context"]: s["state"] for s in statuses}
    result = {"fixture": name, "url": pr["url"], "head": head, "owner": expect["owner"], "reviewers": {}, "problems": [], "pending": False}
    owner = expect["owner"]
    for r in ROSTER:
        mine = [x for x in reviews if x["user"]["type"] == "Bot" and review_line(x["body"]).startswith(f"{r}:") and x["commit_id"] == head]
        counts = parse_review(mine[-1]["body"]) if mine else None
        verdict = by_context.get(f"{r} verdict")
        result["reviewers"][r] = {"verdict": verdict, "counts": counts, "review": mine[-1]["html_url"] if mine else None}
        if verdict in (None, "pending"):
            result["pending"] = True
            continue
        if counts is None:
            result["problems"].append(f"{r}: no parseable review of the head")
            continue
        if r == owner:
            if expect["owner_min"] == "PASS":
                if counts["BLOCK"] > 0 or verdict != "success":
                    result["problems"].append(f"{r} (owner) did not clear the fixed finding: {counts}, verdict {verdict}")
                continue
            caught = counts["BLOCK"] > 0 if expect["owner_min"] == "BLOCK" else counts["BLOCK"] + counts["FIX"] > 0
            if not caught:
                result["problems"].append(f"{r} (owner) missed the planted defect: {counts}")
            if counts["BLOCK"] > 0 and verdict != "failure":
                result["problems"].append(f"{r} (owner) raised a BLOCK but its verdict is {verdict}")
        elif r in expect.get("allowed", []):
            continue
        else:
            if counts["BLOCK"] > 0:
                result["problems"].append(f"{r} raised {counts['BLOCK']} BLOCK outside the planted scope")
            if verdict != "success" and not expect.get("owner_verdict_only"):
                result["problems"].append(f"{r} verdict is {verdict}, expected success")
    result["pass"] = not result["pending"] and not result["problems"]
    if not result["pending"]:
        result["cost_usd"], result["runs"] = run_cost(repo, head)
    return result


def run_cost(repo, head):
    """Model spend of the runs on `head`: the sum of Claude Code's own
    `total_cost_usd` over the agent and threat-detection jobs. It prices tokens
    at the model's list price, so it is an upper estimate of the OpenRouter bill."""
    total, runs = 0.0, []
    for run in gh_json("run", "list", "-R", repo, "--commit", head, "--json", "databaseId", "--limit", "20"):
        rid = run["databaseId"]
        runs.append(rid)
        jobs = json.loads(sh("gh", "api", "--paginate", "--slurp", f"repos/{repo}/actions/runs/{rid}/jobs?per_page=100"))
        for job in (j for page in jobs for j in page["jobs"]):
            if job["name"].endswith(("/ agent", "/ detection")):
                log = sh("gh", "api", "--allow-escape-sequences", f"repos/{repo}/actions/jobs/{job['id']}/logs")
                total += sum(float(x) for x in re.findall(r'"total_cost_usd":([0-9.eE-]+)', log))
    return round(total, 4), runs


def cmd_score(args):
    sha = sh("git", "rev-parse", args.sha, cwd=ROOT).strip()
    recorded = {}
    if args.record:
        for f in json.loads(Path(args.record).read_text())["fixtures"]:
            recorded[f["fixture"]] = (int(f["url"].rsplit("/", 1)[1]), f["head"])
    results = [score_pr(args.repo, n, sha, *recorded.get(n, (None, None)), rnd=args.round) for n in fixtures(args.only)]
    pending = any(r["pending"] for r in results)
    record = {
        "candidate_sha": sha,
        "locks_sha256": locks_sha256(sha),
        "fixture_repo": args.repo,
        "model": "anthropic/claude-sonnet-5",
        "fixtures": results,
        "passed": sum(1 for r in results if r.get("pass")),
        "total": len(results),
        "cost_usd": round(sum(r.get("cost_usd", 0) for r in results), 4),
    }
    record["pass"] = not pending and record["passed"] == record["total"]
    if args.baseline:
        base = json.loads(Path(args.baseline).read_text())
        record["baseline"] = {"file": args.baseline, "passed": base["passed"], "total": base["total"]}
        if record["passed"] < base["passed"]:
            record["pass"] = False
            record.setdefault("regressions", []).append(f"{record['passed']} passed < baseline {base['passed']}")
    text = json.dumps(record, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(text)
    print(text)
    for r in results:
        mark = "pending" if r["pending"] else ("pass" if r.get("pass") else "FAIL")
        print(f"{mark:8} {r['fixture']}: {'; '.join(r['problems']) or 'ok'}", file=sys.stderr)
    return 2 if pending else (0 if record["pass"] else 1)


def cmd_followup(args):
    """Push round 2 to each named fixture's open PR once its head is settled."""
    if not args.only:
        sys.exit("followup needs --only NAME ...")
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "fixtures"
        sh("gh", "repo", "clone", args.repo, str(work), "--", "-q")
        for name in fixtures(args.only):
            spec = load_pr(name)
            src = FIXTURES / "prs" / name / "rounds" / "2"
            if not spec.get("rounds") or not src.is_dir():
                print(f"{name}: no round 2")
                continue
            branch = f"fixture/{name}"
            prs = gh_json("pr", "list", "-R", args.repo, "--head", branch, "--state", "open", "--json", "number,headRefOid")
            if not prs:
                print(f"{name}: no open PR (run it first)")
                continue
            head = prs[0]["headRefOid"]
            ctx = {s["context"]: s["state"] for s in json.loads(sh("gh", "api", f"repos/{args.repo}/commits/{head}/status"))["statuses"]}
            waiting = [r for r in ROSTER if ctx.get(f"{r} verdict") in (None, "pending")]
            if waiting:
                print(f"{name}: round 1 not settled ({', '.join(waiting)}); try later")
                continue
            sh("git", "fetch", "-q", "origin", branch, cwd=work)
            sh("git", "checkout", "-q", "-B", branch, f"origin/{branch}", cwd=work)
            if sh("git", "log", "-1", "--format=%s", cwd=work).strip() == spec["rounds"][0]["message"]:
                print(f"{name}: round 2 already pushed")
                continue
            copy_tree(src / "files", work)
            sh("git", "add", "-A", cwd=work)
            sh("git", "commit", "-qm", spec["rounds"][0]["message"], cwd=work)
            sh("git", "push", "-q", "origin", branch, cwd=work)
            print(f"{name}: pushed round 2 to PR #{prs[0]['number']}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("locks", help="print the hash of the five locks at a commit (release.yml checks it)")
    p.add_argument("--sha", default="HEAD")
    for name in ("run", "score", "followup"):
        p = sub.add_parser(name)
        p.add_argument("--sha", required=True, help="council commit under test")
        p.add_argument("--repo", default=DEFAULT_REPO)
        p.add_argument("--only", nargs="*", help="fixture names (default: all)")
        if name == "score":
            p.add_argument("--round", type=int, default=1, help="2 scores the follow-up heads of multi-round fixtures")
            p.add_argument("--out", help="write the eval record here (e.g. evals/v0.1.0.json)")
            p.add_argument("--baseline", help="the last release's eval record; a candidate must not do worse")
            p.add_argument("--record", help="re-score the PRs an eval record names (after newer runs closed them)")
    args = ap.parse_args()
    if args.cmd == "locks":
        print(locks_sha256(sh("git", "rev-parse", args.sha, cwd=ROOT).strip()))
        sys.exit(0)
    sys.exit({"run": cmd_run, "score": cmd_score, "followup": cmd_followup}[args.cmd](args))


if __name__ == "__main__":
    main()
