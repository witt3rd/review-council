#!/usr/bin/env python3
"""Golden-PR regression suite: run, wait, score, under a spend cap.

  suite.py --sha SHA --baseline evals/vX.Y.Z.json [--max-usd 8] [--timeout 1800]
           [--only NAME ...] [--out evals/candidate.json] [--dry-run]

One command around eval.py. Before anything is spent it estimates the cost from
the baseline record (its cost_usd, scaled by the fixtures chosen) and refuses
when that exceeds --max-usd. It then runs the fixtures, polls the score until
no fixture is pending or --timeout passes, and fails if the measured spend went
over the cap. A model run cannot be recalled once started, so the cap is a gate
before the run and a verdict after it, not a mid-run kill.

Exit: 0 pass, 1 regression or over the cap, 2 still pending at the timeout,
3 refused before running (estimate over the cap, or no baseline cost).
Standard library only; spends model money only when not --dry-run.
"""

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVAL = HERE / "eval.py"
DEFAULT_MAX_USD = 8.0


def estimate(baseline, only):
    """Expected spend for the chosen fixtures, from the baseline record."""
    fx = baseline["fixtures"]
    if only:
        fx = [f for f in fx if f["fixture"] in only]
        if not fx:
            return None
    cost = sum(f.get("cost_usd", 0) for f in fx)
    return round(cost, 4) if cost else None


def restrict(baseline, only):
    """The baseline limited to the chosen fixtures, with passed/total recomputed."""
    if not only:
        return baseline
    fx = [f for f in baseline["fixtures"] if f["fixture"] in only]
    return {**baseline, "fixtures": fx, "passed": sum(1 for f in fx if f.get("pass")), "total": len(fx)}


def verdict(record, max_usd):
    """(exit code, reasons) from a score record and the cap."""
    reasons = []
    if record["cost_usd"] > max_usd:
        reasons.append(f"spend ${record['cost_usd']:.2f} over the cap ${max_usd:.2f}")
    if not record["pass"]:
        reasons.append(f"{record['passed']}/{record['total']} passed" + ("; " + "; ".join(record.get("regressions", [])) if record.get("regressions") else ""))
    return (1 if reasons else 0), reasons


def eval_cmd(*args):
    return [sys.executable, str(EVAL), *args]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sha", required=True)
    ap.add_argument("--baseline", required=True, help="last release's eval record")
    ap.add_argument("--max-usd", type=float, default=DEFAULT_MAX_USD)
    ap.add_argument("--timeout", type=int, default=1800, help="seconds to wait for reviews")
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--out")
    ap.add_argument("--repo")
    ap.add_argument("--dry-run", action="store_true", help="print the estimate and commands, spend nothing")
    a = ap.parse_args(argv)

    baseline = json.loads(Path(a.baseline).read_text())
    est = estimate(baseline, a.only)
    if est is None:
        print("refused: the baseline has no cost for the chosen fixtures", file=sys.stderr)
        return 3
    print(f"estimate ${est:.2f} against the cap ${a.max_usd:.2f}", file=sys.stderr)
    if est > a.max_usd:
        print("refused: the estimate is over the cap; raise --max-usd or choose --only", file=sys.stderr)
        return 3

    with tempfile.TemporaryDirectory() as d:
        base_file = Path(d) / "baseline.json"
        base_file.write_text(json.dumps(restrict(baseline, a.only)))
        return execute(a, str(base_file))


def execute(a, baseline_path):
    common = ["--sha", a.sha] + (["--repo", a.repo] if a.repo else []) + (["--only", *a.only] if a.only else [])
    score = eval_cmd("score", *common, "--baseline", baseline_path) + (["--out", a.out] if a.out else [])
    if a.dry_run:
        print("would run:", " ".join(eval_cmd("run", *common)))
        print("would score:", " ".join(score))
        return 0

    subprocess.run(eval_cmd("run", *common), check=True)
    deadline = time.time() + a.timeout
    while True:
        r = subprocess.run(score, text=True, stdout=subprocess.PIPE)
        if r.returncode != 2:
            break
        if time.time() >= deadline:
            print("timeout: reviews still pending", file=sys.stderr)
            return 2
        time.sleep(a.interval)
    record = json.loads(r.stdout[: r.stdout.rindex("}") + 1])
    code, reasons = verdict(record, a.max_usd)
    print(f"spend ${record['cost_usd']:.2f}; " + ("pass" if code == 0 else "FAIL: " + "; ".join(reasons)), file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
