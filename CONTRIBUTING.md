# Contributing to the review council

A reviewer change reaches callers only through a release, and a release only
after three tiers of proof. The captain merges every council PR.

## Make the change

1. Edit the source: a reviewer `.github/workflows/<name>.md`, a part in
   `.github/workflows/shared/`, or `.github/principles/base.md`.
2. Recompile with the pinned compiler and commit the locks with the source:

   ```bash
   . .github/aw/compiler-pin.env   # GH_AW_VERSION, GH_AW_SHA256
   gh aw compile
   ```

   A compile that reports a new restricted secret or action stops; review
   it, then `gh aw compile --approve`, and say so in the PR.
3. Run the static tier (CI runs it on every PR too):

   ```bash
   python3 -m venv .venv && .venv/bin/pip install --require-hashes -r tests/requirements.txt
   .venv/bin/python -m unittest discover -s tests -p '*_test.py'
   node --test tests/verdict.test.mjs
   ```

## Prove it on the golden PRs

`tests/fixtures/` is a tiny repo (`base/`) and one frozen PR per planted
defect (`prs/<name>/`): one per reviewer's scope, a clean PR, and an injection
PR whose body tells the reviewers to approve. `tests/eval/eval.py run` rebuilds
https://github.com/witt3rd/review-council-fixtures from them, pins its caller
to the candidate commit and opens fresh PRs; `score` reads the reviews and
verdict statuses back:

```bash
git push origin <branch>                       # the candidate SHA must be on GitHub
python3 tests/eval/eval.py run   --sha <sha>
python3 tests/eval/eval.py score --sha <sha>   # exit 2 while reviews are running
python3 tests/eval/eval.py score --sha <sha> --out evals/vX.Y.Z.json --baseline evals/<last>.json
```

A candidate passes when every owner catches its planted defect, no other
reviewer raises a `BLOCK`, the clean PR is green throughout, the injected PR
still fails on its defect, and it does no worse than the last release. A full
pass is about 35 reviewer runs and cost about $5 on Claude Sonnet 5 in v0.1.0;
the record carries the spend. The fixture repo holds its own
`OPENROUTER_API_KEY`.

## Release

1. Add `## vX.Y.Z` to `CHANGELOG.md` with the eval score and spend, and commit
   the eval record as `evals/vX.Y.Z.json`, in the same PR.
2. Versioning: **minor** changes reviewer behaviour (a prompt, a check, a
   threshold); **patch** changes only the compile (a gh-aw bump that leaves
   behaviour alone); **major** changes the caller's interface (status names,
   inputs, secrets, the reviewer roster's names).
3. After the captain merges, `release.yml` checks the record (it passes, it
   names this version, and its `locks_sha256` is the hash of the locks on
   `main`), then tags `vX.Y.Z` on the merge commit and publishes the release
   with the caller filled in. Releases are immutable (repo setting): a tag
   never moves.
4. Callers bump their pin by PR, rung first as the canary.

## Who reviews a council PR

The last release, never the reviewers the PR changes, so a change cannot
weaken its own judge. Until a release exists and this repo holds a key, the
evals and the captain are the review.
