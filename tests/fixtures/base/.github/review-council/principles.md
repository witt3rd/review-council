# tally principles for the review council

**Owner:** the maintainer of this fixture repository. A finding that
contradicts a rule in force is a proposal to the owner.

## Principles

1. **Counts are exact.** The same input gives the same counts on every run
   and every machine. A count is never estimated, sampled or rounded.
2. **Pure core.** Counting is pure (`AGENTS.md` "Law" 3); everything that
   touches the outside world lives in `tally/cli.py`.

## Rules in force

- **Standard library only.** tally has no third-party dependency.

## Steward

1. `AGENTS.md` "Law" 1 and 2 are checked on every PR that changes
   `tally/cli.py` or behaviour in `tally/core.py`.

## Warden

Untrusted input: the file a user passes to tally, and any text inside it; on
CI, anything a pull request author controls (title, body, branch, code).

## Editor

Terms are defined once, in `docs/glossary.md`; docs use them in that sense
only.
