---
# Deterministic context: a job reads the PR's title, description, recent
# discussion and the caller repo's own law before the agent starts, so the
# reviewer spends no turns finding them. Its outputs are quoted into the
# prompt by shared/contract.md.
#
# The law is the caller's `.github/review-council/principles.md` and
# `AGENTS.md`, read from the PR's BASE commit, so a PR cannot rewrite the law
# it is judged by. A missing file is stated in the prompt, never skipped.

# Full history: a later review diffs against the head an earlier one saw.
checkout:
  fetch-depth: 0

jobs:
  pr_context:
    runs-on: ubuntu-slim
    timeout-minutes: 5
    permissions:
      contents: read
      pull-requests: read
      issues: read
    outputs:
      context: ${{ steps.fetch.outputs.context }}
      title: ${{ steps.fetch.outputs.title }}
      description: ${{ steps.fetch.outputs.description }}
      law: ${{ steps.fetch.outputs.law }}
    steps:
      - id: fetch
        env:
          GH_TOKEN: ${{ github.token }}
          REPO: ${{ github.repository }}
          PR: ${{ github.event.pull_request.number }}
          BASE: ${{ github.event.pull_request.base.sha }}
        run: |
          set -euo pipefail
          [[ "$PR" =~ ^[0-9]+$ ]] || { echo "::error::this run names no pull request"; exit 1; }
          [[ "$BASE" =~ ^[0-9a-f]{40}$ ]] || { echo "::error::the pull request names no base commit"; exit 1; }
          gh api "repos/$REPO/pulls/$PR" > /tmp/pr.json
          title=$(jq -r .title /tmp/pr.json)
          description=$(jq -r '.body // ""' /tmp/pr.json)
          if [ "${#description}" -gt 8000 ]; then description="${description:0:8000}"$'\n'"(description truncated at 8000 characters)"; fi
          law=""
          for f in .github/review-council/principles.md AGENTS.md; do
            if gh api -H "Accept: application/vnd.github.raw" "repos/$REPO/contents/$f?ref=$BASE" > /tmp/law.md 2>/dev/null; then
              law+=$'\n'"<repo-file path=\"$f\" ref=\"$BASE\">"$'\n'"$(head -c 24000 /tmp/law.md)"$'\n'"</repo-file>"$'\n'
              if [ "$(wc -c < /tmp/law.md)" -gt 24000 ]; then law+="($f truncated at 24000 bytes)"$'\n'; fi
            else
              law+=$'\n'"(no $f at $BASE)"$'\n'
            fi
          done
          # The council posts as github-actions[bot]; its reviews and memory
          # comments reach the reviewer through Memory, not this block.
          {
            gh api --paginate "repos/$REPO/issues/$PR/comments" --jq '.[]|{t:.created_at,u:.user.login,a:.author_association,w:"pr",b:.body}'
            gh api --paginate "repos/$REPO/pulls/$PR/comments" --jq '.[]|{t:.created_at,u:.user.login,a:.author_association,w:("inline "+.path+":"+((.line // .original_line)|tostring)),b:.body}'
          } | jq -s '[.[]|select(.u != "github-actions[bot]")]|sort_by(.t)|.[-10:]' > /tmp/comments.json
          n=$(jq length /tmp/comments.json)
          body=$(jq -r '.[]|"[\(.t) @\(.u) (\(.a)) on \(.w)]\n\(.b|.[0:2000])\n"' /tmp/comments.json)
          delim="CTX_$(openssl rand -hex 8)"
          {
            echo "context<<$delim"
            echo "Discussion on this PR: the last $n comments by anyone other than the council (oldest first)."
            if [ "$n" -gt 0 ]; then echo "$body"; fi
            echo "$delim"
            echo "title<<$delim"; echo "$title"; echo "$delim"
            echo "description<<$delim"; echo "$description"; echo "$delim"
            echo "law<<$delim"; echo "$law"; echo "$delim"
          } >> "$GITHUB_OUTPUT"
  activation:
    needs: [pr_context]
---
