# Calling the council from rung

Repo: `witt3rd/rung` (code). Generic steps: `docs/callers.md`.

- **Reviewers**: Steward, Architect, Inspector, Warden (the code set).
- **Caller**: `.github/workflows/review-council.yml`, from `caller/review-council.yml`,
  all four jobs pinned to one release SHA with the tag as comment. It is listed
  in `callers.txt`; `tools/pins.py` reports its drift.
- **Law**: `.github/review-council/principles.md` in rung holds rung's owner,
  principles, rules in force and per-reviewer checks. It stays under 24000 bytes
  and names no other repo. It is read from the PR's base commit.
- **Secret**: rung's own `OPENROUTER_API_KEY`.
- **Ruleset**: require `Steward verdict`, `Architect verdict`,
  `Inspector verdict`, `Warden verdict`.
- **Moving to a release**: one-line pin PR in rung (all four SHAs and the
  comment together), merged under rung's rules. Check with `python3 tools/pins.py`.
- **Current state** (checked 2026-10): rung's caller matches the template
  (same jobs, `if`, permissions, inputs, secrets, concurrency; only the header
  comment differs). It is pinned to `45ad2fe` with comment `v0.1.0 candidate`.
  `45ad2fe` is the commit the v0.1.0 evals ran on, not the release commit
  (`e600618`, tag `v0.1.0`), so the pin report says "no release". The reviewer
  locks are identical at both commits (only `eval.yml` differs), so behaviour
  is the same. Gap: a one-line pin PR in rung, all four SHAs to
  `e6006187db2d5c0a090e06b93c857620fda85eab` and the comment to `# v0.1.0`.
  It touches no principles file, so rung's own rules decide who merges.
