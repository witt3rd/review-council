# Eval harness runbook

Operator steps for proving a council candidate on the golden PRs. Why and the
pass bar are in `CONTRIBUTING.md`; the harness is `tests/eval/eval.py`.

## Before you start

- `gh` authenticated with push rights on `witt3rd/review-council-fixtures`
  (needed by `run` only; `score` needs read access, the repo is public).
- The fixture repo has its own `OPENROUTER_API_KEY` secret. A full run costs
  about $5.70 (35 reviewer runs, v0.1.0). Check spend before repeating.
- The candidate commit is pushed to GitHub (callers resolve it by SHA).
  Its locks are compiled and committed with the source.

## Run

```bash
python3 tests/eval/eval.py run --sha <candidate>            # all 7 fixtures
python3 tests/eval/eval.py run --sha <candidate> --only inspector-off-by-one
```

`run` rebuilds the fixture repo's `main` from `tests/fixtures/base` plus a
caller pinned to the candidate, force-pushes one `fixture/<name>` branch per
PR, closes the previous open PR of that branch and opens a new one. It prints
each PR URL. Never merge a fixture PR.

## Score

Wait for the reviews (typically several minutes), then:

```bash
python3 tests/eval/eval.py score --sha <candidate>
```

Exit codes: 0 pass, 1 fail, 2 still pending (re-run later). stderr has one
line per fixture: `pass`, `FAIL` with the problems, or `pending`.

To keep a record:

```bash
python3 tests/eval/eval.py score --sha <candidate> --out evals/vX.Y.Z.json --baseline evals/<last>.json
```

A pass needs every fixture to pass and no fewer than the baseline's passes.
The record holds per-fixture results, `locks_sha256` and `cost_usd`.

## Re-score without the operator's machine

Actions, workflow `eval`, dispatched with `sha` (full) and optionally `record`
(`evals/vX.Y.Z.json`, to re-score the PRs a record names after newer runs
closed them). Use it to check a record you did not write.

## Reading failures

- `no open fixture PR` / `PR head's caller is not pinned to <sha>`: `run` has
  not happened for this SHA, or a newer run replaced it. Pending, not failed.
- `no parseable review of the head`: the reviewer did not post, or its first
  line is not `<Reviewer>: N findings (…)` / `no findings`. Open the run in
  the fixture repo's Actions.
- `(owner) missed the planted defect`: a reviewer regression; the fix is a
  reviewer change (`MERGE: captain`), then run again.
- `raised a BLOCK outside the planted scope` / verdict not success: a false
  positive; read that review before changing a prompt.
- LLM output varies. A single miss is evidence; rerun only the one fixture
  with `--only` to see whether it is stable before drawing a conclusion.

## Adding a fixture

Add `tests/fixtures/prs/<name>/` with `files/` (laid over `base/`) and
`pr.json` (`title`, `body`, `expect.owner`, `owner_min` `BLOCK` or `FIX`,
optional `allowed`, `owner_verdict_only`). Keep it free of consumer names.
A new fixture changes the denominator, so rebaseline the next record.

## One command, with a spend cap

```bash
python3 tests/eval/suite.py --sha <candidate> --baseline evals/<last>.json [--max-usd 8] [--only NAME ...] [--dry-run]
```

`tests/eval/suite.py` runs, waits for the reviews and scores. It estimates the
spend from the baseline record and refuses (exit 3) when that is over
`--max-usd`; after scoring it fails (exit 1) when measured spend exceeded the
cap or a fixture regressed; exit 2 means reviews were still pending at
`--timeout`. With `--only`, the baseline is cut to the chosen fixtures first, so a passing subset is no regression. `--dry-run` prints the estimate and commands and spends nothing.
