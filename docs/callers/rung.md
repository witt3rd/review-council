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
- **Current state**: rung's caller was pinned to the v0.1.0 candidate commit
  (`45ad2fe`, the release's eval record). The pin report shows whether that is
  the release commit.
