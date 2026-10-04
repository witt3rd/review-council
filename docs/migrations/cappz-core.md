# Migration plan: cappz-core moves to the council's caller

Status: **prepared, not opened.** Opening the PRs needs the captain's go
(`MERGE: captain` on both). This file is the plan, the draft PR bodies and the
diffs. It lives in `docs/`, outside what the council ships, so it may name the
consumer (`tests/contract_test.py` scans only definitions, `shared/`, base
principles, `caller/` and locks).

Facts read from `witt3rd/cappz-core` (private, default branch `main`) and
from this repo, not assumed:

- It runs its **own** fleet: four gh-aw reviewers `review-{steward,architect,
  inspector,warden}.md` + locks, `shared/review-base.md` (engine, model
  `stealth/space-bunny-alpha`), `shared/principles.md`, `review-fleet.yml`
  (dispatches `/review` on opened/reopened/ready, **not** on push),
  generated `agentic_commands.yml`, `.github/aw/actions-lock.json`.
- Its ruleset `main` already requires `check`, `Steward verdict`,
  `Architect verdict`, `Inspector verdict`, `Warden verdict` (integration
  15368). The council sets the same four names, so **no ruleset change**.
- It already has the repo secret `OPENROUTER_API_KEY`.
- The newest council release is v0.1.0, tag object -> commit
  `e6006187db2d5c0a090e06b93c857620fda85eab`. Re-resolve before opening
  (`python3 tools/pins.py` prints the newest); a newer release replaces it.
- Its principles live in `.github/workflows/shared/principles.md` (CAPPZ
  principles, maintainers @witt3rd and @dereklasalle, Derek credited) plus the
  generic coding constraints the council's base principles already carry.

## Differences the owner must accept (behaviour, not plumbing)

| Today | After |
|---|---|
| Review runs on open/reopen/ready; a push does not rerun; `/review` comment reruns | Runs on every non-draft same-repo PR event incl. each push; newer push cancels older head. No `/review`, `/warden` etc. comment commands. |
| Model `stealth/space-bunny-alpha` | `model:` input; default in the caller template is `anthropic/claude-sonnet-5` (about $0.80 per five reviewers on a small PR; four here). Keep the old model by setting `with: model:`; decide in review. |
| Review text in cappz-core's own `review-base.md` | The council's contract (`shared/contract.md`): rounds, memory, `PROPOSAL TO THE OWNER:`. The label changes from `PROPOSAL TO THE MAINTAINERS:`. |
| Law read from the working tree | Law read from the PR's **base** commit: a PR that edits its own principles is judged by the old ones. |

## Sequence (two PRs, in order)

1. **Council PR (this repo)**: add `witt3rd/cappz-core` to `callers.txt` so
   `pins.yml` reports its pin. Docs-only otherwise. Merge first; harmless
   because the pin report marks an absent caller file as such.
2. **cappz-core PR** (one PR, so the required statuses never go missing):
   a. add `.github/workflows/review-council.yml` (below), pinned to the SHA;
   b. add `.github/review-council/principles.md` — the CAPPZ section
      carried over, not restated twice (see below);
   c. delete the old fleet: `review-{steward,architect,inspector,warden}.md`
      and `.lock.yml`, `review-fleet.yml`, `agentic_commands.yml` (generated
      only for these reviewers; confirm no other slash command uses it),
      `shared/review-base.md`, `shared/principles.md`; then update the
      docs that point at them (`AGENTS.md` principles pointer, the
      "Reviewer model" section of `CONTRIBUTING.md`, PR template if it names
      `/review`). `.github/aw/actions-lock.json` goes if nothing else uses it;
   d. the PR's own head is reviewed by the **old** fleet or by none (the
      new caller runs on the PR head's workflows, so it reviews itself).
      Expect the four `* verdict` statuses from the council on that head;
      if they do not arrive, the owner's ruleset bypass merges, then the
      next PR proves it.

Rollback: revert the cappz-core PR (one commit); the old fleet returns whole.
No secrets or rulesets change in either direction.

## Draft diff 1: council repo

```diff
--- a/callers.txt
+++ b/callers.txt
@@
 witt3rd/rung
 witt3rd/publishing
+witt3rd/cappz-core
```

## Draft diff 2: cappz-core `.github/workflows/review-council.yml`

`caller/review-council.yml` with the Warden kept, the Editor block removed, and
`COUNCIL_SHA`/`COUNCIL_TAG` filled in for the release resolved at open time
(v0.1.0 shown). The `model` line is the owner's decision (see table).

```diff
+name: Review council
+on:
+  pull_request:
+    types: [opened, reopened, ready_for_review, synchronize]
+permissions: {}
+concurrency:
+  group: review-council-${{ github.event.pull_request.number }}
+  cancel-in-progress: true
+jobs:
+  steward:
+    if: &same-repo-ready >-
+      !github.event.pull_request.draft &&
+      github.event.pull_request.head.repo.full_name == github.repository
+    uses: witt3rd/review-council/.github/workflows/steward.lock.yml@e6006187db2d5c0a090e06b93c857620fda85eab # v0.1.0
+    permissions: &council-permissions
+      actions: read
+      contents: read
+      issues: write
+      pull-requests: write
+      statuses: write
+    with: &council-inputs
+      model: anthropic/claude-sonnet-5
+    secrets: &council-secrets
+      OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
+  architect:
+    if: *same-repo-ready
+    uses: witt3rd/review-council/.github/workflows/architect.lock.yml@e6006187db2d5c0a090e06b93c857620fda85eab # v0.1.0
+    permissions: *council-permissions
+    with: *council-inputs
+    secrets: *council-secrets
+  inspector:
+    if: *same-repo-ready
+    uses: witt3rd/review-council/.github/workflows/inspector.lock.yml@e6006187db2d5c0a090e06b93c857620fda85eab # v0.1.0
+    permissions: *council-permissions
+    with: *council-inputs
+    secrets: *council-secrets
+  warden:
+    if: *same-repo-ready
+    uses: witt3rd/review-council/.github/workflows/warden.lock.yml@e6006187db2d5c0a090e06b93c857620fda85eab # v0.1.0
+    permissions: *council-permissions
+    with: *council-inputs
+    secrets: *council-secrets
```

(When opening, copy `caller/review-council.yml` of the chosen release verbatim
instead of this excerpt; its comments are dropped here for length.)

## Draft diff 3: cappz-core `.github/review-council/principles.md`

Shape from `caller/principles.md`; content moved, not rewritten, from
`shared/principles.md` (keep under 24000 bytes):

- **Owner:** @witt3rd and @dereklasalle.
- **Principles:** the numbered CAPPZ principles (Derek is credited; keys stay
  with their owner; ...) exactly as in the old file. Drop the old "How this
  file is used" and the generic coding-constraints list: the council's base
  principles already carry citation, grounding, single source and the
  timeless constraints.
- **Rules in force:** the repo-specific rules from `review-base.md` lines
  ~150 on ("This PR is to the rebuilt CAPPZ core ...").
- **Steward / Architect / Inspector / Warden:** the per-reviewer checks now in
  the four `review-*.md` files, one section each. The Warden section keeps
  the key-handling and credit checks.

## Draft PR body: council repo

```
Add witt3rd/cappz-core to callers.txt so the pin report tracks its pin.

Docs: docs/migrations/cappz-core.md is the plan for moving cappz-core from
its own review fleet to the council's caller. No reviewer, contract or
caller template changes.

MERGE: captain
```
Label: `needs:captain`.

## Draft PR body: cappz-core

```
Replace the repo's own review fleet with the review council's caller.

What changes
- Adds .github/workflows/review-council.yml, pinned to witt3rd/review-council
  <TAG> (<full SHA>); four reviewers: Steward, Architect, Inspector, Warden.
- Adds .github/review-council/principles.md: the CAPPZ principles and
  per-reviewer checks, moved from shared/principles.md and review-*.md.
- Removes review-{steward,architect,inspector,warden} (md + lock),
  review-fleet.yml, agentic_commands.yml, shared/review-base.md,
  shared/principles.md; updates the docs that pointed at them.

What does not change
- Required statuses: the council sets the same Steward/Architect/Inspector/
  Warden verdict names. No ruleset edit. The repo's own OPENROUTER_API_KEY
  is reused.

Behaviour you accept by merging
- Reviews rerun on every push (before: only on open/ready or /review).
- /review and /warden comment commands are gone.
- Model: <anthropic/claude-sonnet-5 | stealth/space-bunny-alpha>; spend
  about $0.60-0.80 per small PR.
- Law is read from the base commit; label is PROPOSAL TO THE OWNER.

Rollback: revert this commit.

MERGE: captain
```
Label: `needs:captain` (touches principles files and reviewer law).

## Checks before opening

- [ ] Captain approves opening and picks the model.
- [ ] `python3 tools/pins.py` newest tag/SHA substituted above.
- [ ] No other workflow in cappz-core depends on `agentic_commands.yml`,
      `review-*.lock.yml` or `.github/aw/actions-lock.json`.
- [ ] Principles file diffed against the old one: no CAPPZ principle lost.
- [ ] After merge, the next PR shows four `* verdict` statuses on its head.
