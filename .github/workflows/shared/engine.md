---
# The one engine for every council reviewer: Claude Code through OpenRouter.
# The model is the caller's `model` input (each reviewer declares it under
# `on.workflow_call.inputs`); the key is the caller's own OPENROUTER_API_KEY,
# passed by name. The council holds no key. Turns and minutes are a release
# constant in each reviewer: gh-aw refuses an expression in `max-turns`.

import-schema:
  # Lower-case reviewer id, for the provider session header.
  id:
    type: string
    required: true

engine:
  id: claude
  # The workspace is the caller's PR head, which the PR author controls: load
  # none of its agent configuration (CLAUDE.md, .claude/, hooks).
  bare: true
  model: ${{ inputs.model }}
  # gh-aw's default runs one agent job per workflow at a time in a repo, so
  # one reviewer's reviews of different PRs would queue behind each other.
  # One PR at a time per reviewer is enough: a newer push cancels the caller.
  concurrency:
    group: "review-council-${{ github.aw.import-inputs.id }}-${{ github.event.pull_request.number }}"
  env:
    # Claude Code appends /v1/messages itself, so no /v1 here.
    ANTHROPIC_BASE_URL: "https://openrouter.ai/api"
    ANTHROPIC_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
    # Claude Code's aliases name Anthropic-native IDs OpenRouter does not serve.
    ANTHROPIC_DEFAULT_OPUS_MODEL: ${{ inputs.model }}
    ANTHROPIC_DEFAULT_SONNET_MODEL: ${{ inputs.model }}
    ANTHROPIC_DEFAULT_HAIKU_MODEL: ${{ inputs.model }}
    CLAUDE_CODE_SUBAGENT_MODEL: ${{ inputs.model }}
    # One session id per reviewer run, so the provider keeps the run's cache.
    ANTHROPIC_CUSTOM_HEADERS: "x-session-id: review-council-${{ github.aw.import-inputs.id }}-${{ github.run_id }}-${{ github.run_attempt }}"
    # Stops the fast-mode check that dials api.anthropic.com (firewall-blocked).
    CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: "1"

# gh-aw's API proxy uses this fallback rate for a model with no configured
# price; the model is a runtime input, so the compiler cannot price it, and
# without a rate the threat-detection job refuses it. It is gh-aw's estimate,
# not the OpenRouter bill: the reviewers turn the AI-credit caps off.
models:
  default-ai-credits-pricing:
    input: 0.000001
    output: 0.000001

network:
  allowed:
    - defaults
    - openrouter.ai
---
