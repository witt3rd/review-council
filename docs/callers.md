# Calling the council from your repo

The checklist is in `AGENTS.md` ("How a repo adopts it"). This is the detail.

## Pin by full SHA, with the tag as a comment

Every `uses:` in `.github/workflows/review-council.yml` names one release:

```yaml
uses: witt3rd/review-council/.github/workflows/steward.lock.yml@<40-hex-sha> # v0.1.0
```

- The SHA is the release's commit, not a branch or a tag: a tag in a `uses:`
  can be read as moved, a SHA cannot. Releases are immutable, so the tag
  comment stays true.
- Use the same SHA and tag on every reviewer job. A mixed pin runs reviewers
  of different contracts on one PR.
- Each release's notes print the whole caller with both filled in; copy that
  rather than assembling it. `git ls-remote https://github.com/witt3rd/review-council 'refs/tags/v*'`
  lists tags (an annotated tag also lists `^{}`, the commit).
- Moving to a new release is a one-line pin PR in your repo, merged under your
  rules. Status names (`<Reviewer> verdict`) only change on a major version.
- `tools/pins.py` (workflow `pins.yml`, weekly and on each release) reports
  every repo listed in `callers.txt` against the newest release. Add your repo
  there when you adopt.

## Write the principles file

Copy `caller/principles.md` to `.github/review-council/principles.md`. The
council reads it and `AGENTS.md` from the PR's **base** commit, so a PR is
judged by the law it started from and a PR cannot weaken its own judge.

- **Owner**: who decides. A finding that contradicts a rule in force is
  phrased as a proposal to them.
- **Principles**: what stays true when the product is rewritten, numbered,
  each with a bold name; a finding cites the name.
- **Rules in force**: what can change with the product. One place only.
- **Reviewer sections** (Steward, Architect, Inspector, Warden, Editor): extra
  checks for that reviewer; delete the ones for reviewers you do not call.
- Do not restate the base principles (`.github/principles/base.md`); they come
  with every reviewer.
- Keep the file under 24000 bytes; the council truncates past that.
- Name no one else's repo in it: it is yours alone.

## Secrets, rulesets, cost

- Repo secret `OPENROUTER_API_KEY`: your own key. The council holds none.
- Require each called `<Reviewer> verdict` status in the branch ruleset.
- Draft and fork PRs are not reviewed (a fork gets no secrets); the owner's
  ruleset bypass covers forks.
- Spend bills to you: about $0.80 for five reviewers on a small PR.
