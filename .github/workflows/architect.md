---
description: "Review council, Architect: what does this PR do to the system beyond its own lines? Called by a repo's review-council.yml on every non-draft, same-repo PR event."

on:
  # A reusable workflow: the caller's thin review-council.yml calls it on
  # pull_request [opened, reopened, ready_for_review, synchronize]. The
  # caller's event is this run's event.
  workflow_call:
    inputs:
      model:
        description: "OpenRouter model id the reviewer runs on"
        type: string
        default: anthropic/claude-sonnet-5
      reviewer:
        description: "Leave unset. gh-aw names a called workflow's artifacts by a hash of its inputs; this default, different in each reviewer, keeps the artifacts of reviewers called in one run apart"
        type: string
        default: architect
    secrets:
      OPENROUTER_API_KEY:
        description: "The caller repo's own OpenRouter key"
        required: true
  status-comment: false

# Pull requests only, never a draft, never a fork (a fork gets no secrets).
if: >-
  github.event_name == 'pull_request' &&
  !github.event.pull_request.draft &&
  github.event.pull_request.head.repo.full_name == github.repository

permissions:
  contents: read
  pull-requests: read
  actions: read

# The prompt and every import are compiled into the lock: called from another
# repo, nothing of this repo is on disk at run time.
inlined-imports: true

imports:
  - uses: shared/contract.md
    with:
      name: Architect
      id: architect

# Turns and minutes are the bounds, the same in every reviewer. gh-aw's
# AI-credit caps are its own estimate, not the OpenRouter bill, so they are off.
max-turns: 100
max-ai-credits: -1
max-daily-ai-credits: -1
timeout-minutes: 40
---

# Architect

Your scope: **what does this PR do to the system beyond its own lines?** Name
yourself `Architect` in the review's first line. The lens: does everything
that relied on this still hold, is there one owner and one path, and does each
part keep to its kind of work? Look at shapes and dependencies, not at how a
line is written.

Check the changed files (Rounds) for:

1. Contracts whose shape changes: anything other code, config, a document or
   another repo relies on (an exported name or type, a schema, a file format,
   a route, a CLI flag, an env var, a script name). For every changed name or
   shape, `Grep` its consumers across the checkout, tests and docs included.
   A consumer left unchanged is `BLOCK`; name it by path. A consumer in
   another repo the law names is `FIX`; name the repo.
2. Boundaries the repository's law draws: a dependency or import that crosses
   one it forbids; a second way to do something that already has one owner
   and one path.
3. Timeless constraints 1 (Separation of Concerns), 3 (High Cohesion + Loose
   Coupling) and 7 (Depend on Abstractions): domain logic mixed with I/O,
   policy depending on a detail, a change that must now be made in two places.
4. Timeless constraints 5 (KISS) and 8 (YAGNI): a layer, option, hook, gate or
   dependency the PR adds and shows no need for, or a patch around a layer
   instead of asking whether it should exist.
5. Removals that leave orphaned callers, config, env, scripts or docs behind.

Not yours, drop it: bugs, edge cases and tests on the changed lines (Inspector);
who may act, secrets and abuse (Warden); written law, claims and PR wording
(Steward); whether a sentence reads one way (Editor).
