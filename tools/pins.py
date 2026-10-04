#!/usr/bin/env python3
"""Report every caller's council pin against the newest release.

Reads callers.txt, fetches each caller's .github/workflows/review-council.yml
from its default branch, and prints one row per caller: the release each
reviewer job is pinned to, and whether that is the newest. Drift shows up as a
report, not a surprise. A private caller the token cannot read is reported as
unreadable, never skipped. Uses the gh CLI; standard library only.

  tools/pins.py [--callers callers.txt] [--council witt3rd/review-council]
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PIN = re.compile(r"uses:\s*([\w.-]+/[\w.-]+)/\.github/workflows/(\w+)\.lock\.yml@([0-9a-f]{40})(?:\s*#\s*(\S+))?")


def gh(*args):
    r = subprocess.run(["gh", *args], text=True, capture_output=True)
    return r.stdout if r.returncode == 0 else None


def releases(council):
    """tag -> commit sha for every release, and the newest tag."""
    data = json.loads(gh("api", "--paginate", "--slurp", f"repos/{council}/releases?per_page=100") or "[]")
    rel = [r for page in data for r in page if not r["draft"] and not r["prerelease"]]
    tags = {}
    for r in rel:
        ref = json.loads(gh("api", f"repos/{council}/git/ref/tags/{r['tag_name']}") or "null")
        if not ref:
            continue
        obj = ref["object"]
        if obj["type"] == "tag":
            obj = json.loads(gh("api", f"repos/{council}/git/tags/{obj['sha']}"))["object"]
        tags[r["tag_name"]] = obj["sha"]
    latest = json.loads(gh("api", f"repos/{council}/releases/latest") or "null")
    return tags, (latest or {}).get("tag_name")


def report(callers, council):
    tags, newest = releases(council)
    by_sha = {sha: tag for tag, sha in tags.items()}
    rows = []
    for repo in callers:
        text = gh("api", "-H", "Accept: application/vnd.github.raw", f"repos/{repo}/contents/.github/workflows/review-council.yml")
        if text is None:
            rows.append((repo, "-", "unreadable with this token, or no caller"))
            continue
        # The template's commented-out Editor job is no pin.
        live = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))
        pins = [m for m in PIN.findall(live) if m[0] == council]
        if not pins:
            rows.append((repo, "-", "no council pin found"))
            continue
        reviewers = ", ".join(r for _, r, _, _ in pins)
        shas = {sha for _, _, sha, _ in pins}
        comments = {c for _, _, _, c in pins}
        if len(shas) > 1:
            rows.append((repo, f"mixed ({reviewers})", "reviewers pin different commits"))
            continue
        sha = shas.pop()
        tag = by_sha.get(sha)
        if tag is None:
            state = f"pins {sha[:7]}, which is no release"
        elif comments - {tag}:
            state = f"comment says {', '.join(sorted(c for c in comments if c))}, the SHA is {tag}"
        elif tag != newest:
            state = f"behind: newest is {newest}"
        else:
            state = "current"
        rows.append((repo, f"{tag or sha[:7]} ({reviewers})", state))
    lines = [f"Council pins against the newest release, {newest or 'none yet'}", "",
             "| Caller | Pinned to | State |", "|---|---|---|"]
    lines += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--callers", default=str(ROOT / "callers.txt"))
    ap.add_argument("--council", default="witt3rd/review-council")
    args = ap.parse_args()
    callers = [l.strip() for l in Path(args.callers).read_text().splitlines() if l.strip() and not l.startswith("#")]
    out = report(callers, args.council)
    print(out)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
