// Unit tests for the verdict script in .github/workflows/shared/verdict.md.
// The script runs as written (no copy): it is cut from the source file and
// run on recorded reviews with a fake `github`, `context` and `core`.
// Run: node --test tests/
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const SOURCE = new URL('../.github/workflows/shared/verdict.md', import.meta.url);

// The `script: |` block of the step with this name, dedented.
function stepScript(stepName) {
  const lines = readFileSync(SOURCE, 'utf8').split('\n');
  const start = lines.findIndex(l => l.trim() === `- name: ${stepName}`);
  assert.ok(start >= 0, `step "${stepName}" not found`);
  const at = lines.findIndex((l, i) => i > start && l.trim() === 'script: |');
  const indent = lines[at].search(/\S/);
  const body = [];
  for (const l of lines.slice(at + 1)) {
    if (l.trim() !== '' && l.search(/\S/) <= indent) break;
    body.push(l);
  }
  const strip = Math.min(...body.filter(l => l.trim()).map(l => l.search(/\S/)));
  return body.map(l => l.slice(strip)).join('\n');
}

const AsyncFunction = Object.getPrototypeOf(async () => {}).constructor;
const VERDICT = new AsyncFunction('github', 'context', 'core', 'process', stepScript("Verdict of this run's review"));
const PENDING = new AsyncFunction('github', 'context', 'core', 'process', stepScript('Verdict pending'));

const HEAD = 'a'.repeat(40);
const OTHER = 'b'.repeat(40);
const RUN = 4242;
const RUN_URL = `https://github.com/o/r/actions/runs/${RUN}`;

const review = (over = {}) => ({
  user: { type: 'Bot', login: 'github-actions[bot]' },
  state: 'COMMENTED',
  commit_id: HEAD,
  html_url: 'https://github.com/o/r/pull/7#pullrequestreview-1',
  body: `Steward: no findings in written law.\n\n> [Steward · review-council](${RUN_URL})`,
  ...over,
});

async function run(reviews, env = {}) {
  const statuses = [];
  const failed = [];
  const github = {
    paginate: async () => reviews,
    rest: {
      pulls: { listReviews: () => {} },
      repos: { createCommitStatus: async s => statuses.push(s) },
    },
  };
  const context = { repo: { owner: 'o', repo: 'r' }, runId: RUN, serverUrl: 'https://github.com' };
  const core = { info: () => {}, setFailed: m => failed.push(m) };
  const proc = { env: { REVIEWER: 'Steward', HEAD_SHA: HEAD, PR_NUMBER: '7', ...env } };
  await VERDICT(github, context, core, proc);
  return { statuses, failed };
}

test('a clean COMMENT review of the head passes', async () => {
  const { statuses, failed } = await run([review()]);
  assert.equal(statuses.length, 1);
  assert.equal(statuses[0].state, 'success');
  assert.equal(statuses[0].context, 'Steward verdict');
  assert.equal(statuses[0].sha, HEAD);
  assert.deepEqual(failed, []);
});

test('FIX and NOTE findings do not fail the verdict', async () => {
  const { statuses } = await run([review({ body: `Steward: 2 findings (0 BLOCK, 1 FIX, 1 NOTE)\n${RUN_URL}` })]);
  assert.equal(statuses[0].state, 'success');
});

test('a BLOCK count fails the verdict even on a COMMENT', async () => {
  const { statuses, failed } = await run([review({ body: `Steward: 1 findings (1 BLOCK, 0 FIX, 0 NOTE)\n${RUN_URL}` })]);
  assert.equal(statuses[0].state, 'failure');
  assert.equal(failed.length, 1);
});

test('REQUEST_CHANGES fails the verdict', async () => {
  const { statuses } = await run([review({ state: 'CHANGES_REQUESTED' })]);
  assert.equal(statuses[0].state, 'failure');
});

test('a review of an older commit fails the verdict', async () => {
  const { statuses } = await run([review({ commit_id: OTHER })]);
  assert.equal(statuses[0].state, 'failure');
  assert.match(statuses[0].description, /bbbbbbb/);
});

test('no review from this run fails the verdict', async () => {
  const { statuses } = await run([review({ body: 'Steward: no findings.\nhttps://github.com/o/r/actions/runs/42420' })]);
  assert.equal(statuses[0].state, 'failure');
  assert.match(statuses[0].description, /posted no Steward review/);
});

test("another reviewer's review in the same run is not this reviewer's", async () => {
  const { statuses } = await run([review({ body: `Warden: no findings in abuse.\n${RUN_URL}` })]);
  assert.equal(statuses[0].state, 'failure');
});

test("a person's review quoting the run URL does not count", async () => {
  const { statuses } = await run([review({ user: { type: 'User', login: 'someone' } })]);
  assert.equal(statuses[0].state, 'failure');
});

test('the latest of this reviewer\'s reviews in the run decides', async () => {
  const { statuses } = await run([
    review({ state: 'CHANGES_REQUESTED', body: `Steward: 1 findings (1 BLOCK, 0 FIX, 0 NOTE)\n${RUN_URL}` }),
    review(),
  ]);
  assert.equal(statuses[0].state, 'success');
});

test('the status is named for the reviewer, never the workflow', async () => {
  const { statuses } = await run([review({ body: `Editor: no findings in prose.\n${RUN_URL}` })], { REVIEWER: 'Editor' });
  assert.equal(statuses[0].context, 'Editor verdict');
  assert.equal(statuses[0].state, 'success');
});

test('a run with no pull request head writes no status and fails', async () => {
  const { statuses, failed } = await run([review()], { HEAD_SHA: '', PR_NUMBER: '' });
  assert.equal(statuses.length, 0);
  assert.equal(failed.length, 1);
});

test('an API error fails the verdict with the reason', async () => {
  const statuses = [];
  const failed = [];
  const github = {
    paginate: async () => { throw new Error('boom'); },
    rest: { pulls: { listReviews: () => {} }, repos: { createCommitStatus: async s => statuses.push(s) } },
  };
  await VERDICT(github, { repo: { owner: 'o', repo: 'r' }, runId: RUN, serverUrl: 'https://github.com' },
    { info: () => {}, setFailed: m => failed.push(m) },
    { env: { REVIEWER: 'Steward', HEAD_SHA: HEAD, PR_NUMBER: '7' } });
  assert.equal(statuses[0].state, 'failure');
  assert.match(statuses[0].description, /boom/);
});

test('the pending status lands on the head SHA under the reviewer name', async () => {
  const statuses = [];
  const github = { rest: { repos: { createCommitStatus: async s => statuses.push(s) } } };
  await PENDING(github, { repo: { owner: 'o', repo: 'r' }, runId: RUN, serverUrl: 'https://github.com' }, {},
    { env: { REVIEWER: 'Inspector', HEAD_SHA: HEAD } });
  assert.equal(statuses[0].state, 'pending');
  assert.equal(statuses[0].context, 'Inspector verdict');
  assert.equal(statuses[0].sha, HEAD);
});
