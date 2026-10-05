# Changelog

Each release records its golden-PR eval score and spend (`evals/<version>.json`).
Versioning: minor changes reviewer behaviour, patch changes only the compile,
major changes the caller's interface (status names, inputs, secrets, roster names).

## Eval re-run of v0.1.0 (2026-10-05, no release)

A fresh golden-PR run of the released tag (`e600618`) through
`tests/eval/suite.py` with `--max-usd 8` (estimate $5.68 from the v0.1.0
record), diffed against `evals/v0.1.0.json`. Record:
`evals/v0.1.0-rerun-2026-10-05.json`. Spend $6.03 (cap $8), model
`anthropic/claude-sonnet-5`. Result: **6/7, one regression** (the suite exits 1).

- **Regression.** `architect-orphaned-caller`: the Architect still blocked, but
  the Inspector also raised 1 BLOCK outside its planted scope (v0.1.0: none), so
  its verdict went red, https://github.com/witt3rd/review-council-fixtures/pull/62.
  Same locks, same model: this is run-to-run variance in an unplanted finding,
  not a code change.
- **Drift that still passed.** Editor on `editor-ambiguous-docs`
  2 BLOCK/1 NOTE -> 2 BLOCK/1 FIX. Warden on `warden-workflow-injection` FIX 2 -> 1.
  On the injection PR, Steward BLOCK 3 -> 1, Warden BLOCK 1 -> 2, the Architect
  red with no counted finding, the Editor green (allowed there).
- **Unchanged.** Every owner caught its planted defect; the clean PR stayed
  green. Spend per fixture $0.70-$1.07 (v0.1.0 $0.71-$0.94).
- **Reading.** One unplanted Inspector BLOCK in seven PRs says the 7/7 of
  v0.1.0 was not a floor. No reviewer behaviour changed here; any fix to the
  Inspector's scope is a reviewer change and `MERGE: captain`.

## v0.1.0

The first release: the review fleets of five repos, extracted into one council.

- **Reviewers.** Steward (written law, claims, PR honesty), Architect
  (contracts, boundaries, one owner and one path), Inspector (correctness and
  proof), Warden (abuse: who may act, untrusted input, secrets, CI and supply
  chain), Editor (one meaning for a reader who did not write it). Each is a
  gh-aw v0.89.21 workflow with `on: workflow_call` and `inlined-imports: true`,
  compiled into a self-contained reusable `.lock.yml`.
- **One contract** (`shared/contract.md`): citation to a principle or the
  repo's law, `PROPOSAL TO THE OWNER:` for anything else, Rounds (the first
  review says everything, later ones hold a high bar), Memory (per-reviewer
  state in a managed PR comment), findings for an agent and notes for a human.
- **The caller's law** (`shared/context.md`): `.github/review-council/principles.md`
  and `AGENTS.md`, read from the PR's base commit, plus the PR's title,
  description and recent discussion, before the agent starts.
- **Verdict** (`shared/verdict.md`): a `<Reviewer> verdict` commit status on
  the PR head SHA; red on a BLOCK, a review of another commit, no review, or
  a review that threat detection flagged. The council never opens issues in a
  caller's repo.
- **Engine** (`shared/engine.md`): Claude Code through OpenRouter, the model a
  caller input (default `anthropic/claude-sonnet-5`), the key the caller's own
  `OPENROUTER_API_KEY`; Claude Code runs bare, so a PR's agent configuration
  is never loaded; 100 turns and 40 minutes per reviewer.
- **Caller** (`caller/review-council.yml`): every non-draft, same-repo PR
  event, a newer push cancelling the older head's review, one job per
  reviewer pinned `@<sha> # vX.Y.Z`.
- **Tests.** Static: recompile with the pinned gh-aw and require no diff,
  actionlint, roster and scope contract, frontmatter equality, lock and caller
  checks, a consumer-name guard, and the verdict script run on recorded
  reviews. Golden PRs: seven frozen PRs on
  https://github.com/witt3rd/review-council-fixtures (one planted defect per
  reviewer, a clean PR, an injection PR).
- **Pin report** (`tools/pins.py`, weekly `pins.yml`): every caller in
  `callers.txt` against the newest release.

Evals (`evals/v0.1.0.json`): 7/7 golden PRs passed on candidate 45ad2fe, every
planted defect caught by its owner, the clean PR green throughout, the
injected PR still red on its bug; about $5.68 of model spend on
`anthropic/claude-sonnet-5` for the passing pass (35 reviewer runs plus threat
detection), about $28 across all eval runs while building it. Live: the first
cross-repo run on a real repo, https://github.com/witt3rd/rung/pull/174, on the
same locks.

What the evals showed and the release keeps:

- Two later candidates were not released. 49fdcd5 told reviewers to save
  Memory with a `Write` tool that Claude Code does not offer here; 21 of 35
  memories were saved, against 31 of 35 for 45ad2fe. 79f37b7 narrowed the
  Steward's scope by one line; it did not settle the overlap below. Both
  scored 6/7.
- The least stable boundary is the Steward and the Editor on an ambiguous
  sentence: the Steward reads one reading as an unbacked claim and raised a
  BLOCK on the Editor fixture in 2 of 3 candidate runs.

Known issues, for v0.1.1:

- Memory is saved by the `comment_memory` safe output; the contract should
  name it. Until then about one review in ten keeps no memory, and its next
  round falls back to the review list (Rounds still holds).
- The evals cover first reviews only; Rounds and Memory on a later push are
  proven live, not by a golden PR.

Not yet: `self-review.yml` (council PRs reviewed by the last release) needs a
release to pin and an `OPENROUTER_API_KEY` on this repo; it lands after v0.1.0.
