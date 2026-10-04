# AGENTS.md — review-council

One AI review council for many repos. Five reviewers (Steward, Architect,
Inspector, Warden, Editor) are gh-aw agentic workflows compiled into reusable
workflows. A repo calls the ones it wants from a thin caller pinned to a
release, supplies its own law and its own OpenRouter key, and gets one
required commit status per reviewer, `<Reviewer> verdict`, on the PR head.
The council holds no key and no consumer's law.

## How a repo adopts it

1. Copy `caller/review-council.yml` to `.github/workflows/review-council.yml`.
   Keep the reviewers the repo wants (code repos: Steward, Architect,
   Inspector, Warden; documents repos swap the Warden for the Editor). Pin
   every `uses:` to one release's full commit SHA with its tag as a comment,
   `@<sha> # vX.Y.Z`; each release's notes print the caller filled in.
2. Copy `caller/principles.md` to `.github/review-council/principles.md` and
   write the repo's principles, rules in force, owner and per-reviewer checks.
   The council reads it and `AGENTS.md` from the PR's **base** commit.
3. Set the repo secret `OPENROUTER_API_KEY` (the repo's own key).
4. Require `<Reviewer> verdict` for each called reviewer in the branch ruleset.
5. Add the repo to `callers.txt` here, so the pin report (`pins.yml`) sees it.

Runs on every non-draft, same-repo PR event (opened, reopened, ready, each
push); a newer push cancels the older head's review. Fork PRs get no secrets,
so they get no verdict: the owner's ruleset bypass covers them. Actions
minutes and model spend bill to the caller (about $0.80 for five reviewers on
a small PR on Claude Sonnet 5, measured in the evals).

## Invariants (a small edit can break these)

- **Locks are compiled, never edited.** Edit a `.md`, run `gh aw compile`
  with the pinned gh-aw (`.github/aw/compiler-pin.env`, v0.89.21), commit
  source and lock together. CI recompiles and requires no diff.
- **Self-contained locks.** Every reviewer keeps `inlined-imports: true`:
  called from another repo, nothing of this repo is on disk.
- **The caller's names are not ours.** In a called workflow `github.workflow`
  is the caller's name and `github.sha` the merge commit: status names,
  memory ids, concurrency and session ids use the reviewer's fixed name; the
  verdict is set on `pull_request.head.sha`. Each reviewer's `reviewer` input
  default differs, or gh-aw's artifact names collide in one caller run.
- **Repo-neutral.** No consumer name in what ships (definitions, `shared/`,
  base principles, caller, locks); `tests/contract_test.py` guards it. A
  consumer's checks go in its own principles file.
- **One contract.** The review format, Rounds, Memory and the verdict rule
  live once, in `.github/workflows/shared/`. The reviewers' frontmatter is
  identical apart from description, name and that input default.
- **Status names are the caller's interface.** Renaming a reviewer, its
  status, an input or a secret is a major version.
- **Base principles live at `.github/principles/base.md`**, not
  `principles/base.md` as the design note drew: gh-aw refuses an import
  outside `.github/`, symlinks included.

## Commands

```bash
gh aw compile                                               # after any .md edit
python3 -m unittest discover -s tests -p '*_test.py'        # needs tests/requirements.txt
node --test tests/verdict.test.mjs
python3 tests/eval/eval.py run   --sha <candidate>          # golden PRs (push rights on the fixture repo)
python3 tests/eval/eval.py score --sha <candidate> --out evals/vX.Y.Z.json
python3 tools/pins.py                                       # every caller's pin vs the newest release
```

## Map

- `.github/workflows/<reviewer>.md` — scope and numbered checks; `.lock.yml`
  beside each is the reusable workflow callers pin.
- `.github/workflows/shared/` — `contract.md` (format, Rounds, Memory, tools,
  safe outputs), `context.md` (PR text, discussion, the caller's law from the
  base commit), `engine.md` (Claude Code via OpenRouter, model input),
  `verdict.md` (the status jobs).
- `.github/principles/base.md` — what every repo inherits.
- `caller/` — the templates a repo copies.
- `tests/` — static tier (`contract_test.py`, `verdict.test.mjs`) and the
  golden-PR tier (`eval/`, `fixtures/`, run on
  https://github.com/witt3rd/review-council-fixtures). Fixture PRs carry
  planted defects and an injection on purpose; never merge one.
- `evals/` — one record per release; `release.yml` tags only on a passing one.
- `CONTRIBUTING.md` — how a change is made, evaluated and released.
- `CHANGELOG.md` — every release with its eval scores and spend.

## Who merges

The captain merges every council PR (`MERGE: captain`, label
`needs:captain`): reviewer behaviour is review-contract law. Callers move by a
one-line pin PR in their own repo, merged under that repo's rules.
