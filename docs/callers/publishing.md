# Calling the council from publishing

Repo: `witt3rd/publishing`. Generic steps: `docs/callers.md`.

`publishing` has no caller yet (`callers.txt` lists it ahead of adoption, so
the pin report shows it as "unreadable ... or no caller" until it does).

To adopt:

1. Copy `caller/review-council.yml` to `.github/workflows/review-council.yml`.
   publishing is code (a renderer and its container profile): keep Steward,
   Architect, Inspector and Warden. Pin every `uses:` to the newest release's
   full SHA, tag as comment (`gh release view` prints the filled caller).
2. Copy `caller/principles.md` to `.github/review-council/principles.md`; write
   owner, principles, rules in force and per-reviewer checks. The Warden's
   section should name the sandbox and user-content rules that repo holds.
   Do not edit principles on a PR that needs the council's verdict: the council
   reads it from the base commit, so land it first.
3. Set the repo secret `OPENROUTER_API_KEY` (publishing's own key).
4. Require the four `<Reviewer> verdict` statuses in the ruleset only after the
   first council run on a PR has reported them, or the PR cannot merge.
5. `python3 tools/pins.py` should then show it `current`.

Adopting changes what gates publishing's merges: a captain decision.

Conformance (checked 2026-10): publishing has no
`.github/workflows/review-council.yml` on its default branch (the contents
API returns 404), so there is nothing to compare with the template. The pin
report lists it as unreadable or no caller. Adoption, with its principles
file, is `MERGE: captain`.
