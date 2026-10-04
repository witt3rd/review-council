---
# The reviewer's verdict: one commit status named `<Reviewer> verdict` on the
# PR head SHA it reviewed. The caller's ruleset requires one per reviewer.
#
# Two constraints of a reusable workflow shape it. Inside a called workflow
# `github.workflow` is the CALLER's name, so the status is named after the
# reviewer's fixed name (the `name` import input), never the workflow. And on
# a `pull_request` event `github.sha` is the merge commit, so the status is set
# on `pull_request.head.sha`.
#
# The status is pending while the review runs, so a rerun never leaves an
# older pass standing, and red when this run's review requests changes or
# counts a BLOCK, when the review is of another commit, or when this run
# posted no review. All reviewers post as one identity (GITHUB_TOKEN) in one
# run, so a review is this reviewer's only when it is a bot's, quotes this
# run's URL and its first line starts with the reviewer's name.
#
# tests/verdict.test.mjs runs the `verdict` script below on recorded reviews.

import-schema:
  # The reviewer's display name, as in the status context and the review's
  # first line: Steward, Architect, Inspector, Warden, Editor.
  name:
    type: string
    required: true

jobs:
  verdict_pending:
    needs: [activation]
    runs-on: ubuntu-slim
    timeout-minutes: 5
    permissions:
      statuses: write
    steps:
      # The agent needs this job; a failed status write must not skip the
      # review, and `verdict` overwrites the status either way.
      - name: Verdict pending
        continue-on-error: true
        uses: actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3 # v9.0.0
        env:
          REVIEWER: "${{ github.aw.import-inputs.name }}"
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
        with:
          script: |
            await github.rest.repos.createCommitStatus({ ...context.repo, sha: process.env.HEAD_SHA, state: 'pending',
              context: `${process.env.REVIEWER} verdict`, description: 'Reviewing',
              target_url: `${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}` });
  verdict:
    needs: [activation, agent, detection, safe_outputs, verdict_pending]
    if: always() && needs.activation.result == 'success'
    runs-on: ubuntu-slim
    timeout-minutes: 5
    permissions:
      pull-requests: read
      statuses: write
    steps:
      - name: Verdict of this run's review
        uses: actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3 # v9.0.0
        env:
          REVIEWER: "${{ github.aw.import-inputs.name }}"
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
        with:
          script: |
            const reviewer = process.env.REVIEWER;
            const head = process.env.HEAD_SHA || '';
            const pull_number = Number(process.env.PR_NUMBER || 0);
            const run_url = `${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}`;
            const verdict = async () => {
              if (!pull_number || !/^[0-9a-f]{40}$/.test(head)) return { fail: 'This run names no pull request head.' };
              const reviews = await github.paginate(github.rest.pulls.listReviews, { ...context.repo, pull_number, per_page: 100 });
              const mine = new RegExp(`/actions/runs/${context.runId}(?!\\d)`);
              const first = r => (r.body || '').split('\n')[0].trim();
              // A bot's only (a person with write can post a review that quotes
              // this run's URL), and this reviewer's only (every reviewer of the
              // run quotes the same URL).
              const review = reviews.filter(r => r.user?.type === 'Bot' && mine.test(r.body || '')
                && first(r).startsWith(`${reviewer}:`)).pop();
              if (!review) return { fail: `This run posted no ${reviewer} review on #${pull_number}.` };
              const line = first(review);
              core.info(`${review.html_url}\n${review.state}: ${line}`);
              const url = review.html_url;
              if (review.commit_id !== head) return { url, fail: `The review is of ${String(review.commit_id).slice(0, 7)}, not ${head.slice(0, 7)}.` };
              const blocks = Number((line.match(/\((\d+) BLOCK/) || [])[1] || 0);
              if (review.state === 'CHANGES_REQUESTED' || blocks > 0) return { url, fail: line };
              if (review.state !== 'COMMENTED') return { url, fail: `Review state ${review.state}.` };
              return { url, pass: line };
            };
            let v;
            try { v = await verdict(); } catch (e) { v = { fail: `Could not read the review: ${e.message}` }; }
            if (/^[0-9a-f]{40}$/.test(head)) {
              await github.rest.repos.createCommitStatus({ ...context.repo, sha: head,
                state: v.fail ? 'failure' : 'success', context: `${reviewer} verdict`,
                description: (v.fail || v.pass).slice(0, 140), target_url: v.url || run_url });
            }
            if (v.fail) core.setFailed(v.fail);
---
