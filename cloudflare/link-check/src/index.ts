/**
 * link-check — a Cloudflare Worker that crawls agentsandhumans.ai on a schedule and reports every
 * link that does not resolve.
 *
 * How it works. A sweep is a queue of URLs kept in KV. Each cron tick takes one batch off the
 * queue, fetches each URL, records the status, and pushes any new same-origin links it finds. When
 * the queue is empty the sweep is finished: the report is stored, a Slack message goes out if there
 * are breakages that were not in the previous sweep, and the next tick starts a fresh sweep once
 * the previous one is older than a day. Batching keeps every tick under the subrequest limit.
 *
 * Endpoints
 *   GET  /            the latest finished report as JSON
 *   GET  /report.md   the same as Markdown
 *   GET  /status      queue length and sweep progress
 *   POST /run         process one batch now (needs ?key=ADMIN_KEY)
 *   POST /reset       drop the current sweep and start over (needs ?key=ADMIN_KEY)
 */
import { normalizeHref, sameOrigin, extractLinks, ignored, isBroken, renderMarkdown } from './crawl.js';

export interface Env {
  STATE: KVNamespace;
  BASE_URL: string;
  BATCH: string;
  CHECK_EXTERNALS: string;
  IGNORE: string;
  ADMIN_KEY?: string;
  SLACK_WEBHOOK_URL?: string;
}

type Broken = { url: string; status: number; final: string | null; from: string[] };
type Sweep = {
  id: string; base: string; startedAt: string; finishedAt: string | null;
  queue: string[]; seen: Record<string, number>; from: Record<string, string[]>;
  checked: number; internal: number; external: number; broken: Broken[];
};

const UA = 'agentsandhumans-link-check/1.0 (+https://agentsandhumans.ai)';
const SWEEP_KEY = 'sweep:current';
const REPORT_KEY = 'report:latest';
const DAY = 24 * 60 * 60 * 1000;

function newSweep(base: string): Sweep {
  const now = new Date().toISOString();
  return { id: now.slice(0, 16).replace(/[-:T]/g, ''), base, startedAt: now, finishedAt: null, queue: [base + '/'], seen: {}, from: {}, checked: 0, internal: 0, external: 0, broken: [] };
}

async function probe(url: string, method: 'GET' | 'HEAD'): Promise<{ status: number; final: string; type: string; body: string }> {
  try {
    const r = await fetch(url, { method, redirect: 'follow', headers: { 'User-Agent': UA, Accept: 'text/html,*/*' }, cf: { cacheTtl: 0 } } as RequestInit);
    const type = r.headers.get('content-type') || '';
    const body = method === 'GET' && type.includes('html') ? await r.text() : '';
    return { status: r.status, final: r.url || url, type, body };
  } catch {
    return { status: 0, final: url, type: '', body: '' };
  }
}

/** Fetch one batch of queued URLs and fold the results into the sweep. Returns true when the sweep finished. */
export async function step(env: Env): Promise<{ sweep: Sweep; finished: boolean }> {
  const base = env.BASE_URL.replace(/\/$/, '');
  const batch = Math.max(1, Number(env.BATCH) || 40);
  const ignore = (env.IGNORE || '').split(',').map((s) => s.trim()).filter(Boolean);
  const checkExternals = (env.CHECK_EXTERNALS || 'true') !== 'false';

  let sweep = (await env.STATE.get<Sweep>(SWEEP_KEY, 'json')) ?? newSweep(base);
  if (sweep.finishedAt) {
    if (Date.now() - new Date(sweep.finishedAt).getTime() < DAY) return { sweep, finished: true };
    sweep = newSweep(base);
  }

  const take = sweep.queue.splice(0, batch);
  for (const url of take) {
    if (url in sweep.seen) continue;
    const internal = sameOrigin(url, base);
    if (!internal && !checkExternals) continue;
    let res = await probe(url, internal ? 'GET' : 'HEAD');
    if (!internal && (res.status === 405 || res.status === 403 || res.status === 0)) res = await probe(url, 'GET');
    sweep.seen[url] = res.status; sweep.checked++;
    if (internal) sweep.internal++; else sweep.external++;
    if (isBroken(res.status, res.final)) sweep.broken.push({ url, status: res.status, final: res.final !== url ? res.final : null, from: (sweep.from[url] ?? []).slice(0, 5) });
    if (internal && res.status === 200 && res.body) {
      for (const { href } of extractLinks(res.body)) {
        const n = normalizeHref(href, url);
        if (!n || n in sweep.seen) continue;
        if (sameOrigin(n, base) && ignored(n, ignore)) continue;
        (sweep.from[n] ??= []).length < 5 && sweep.from[n].push(url);
        if (!sweep.queue.includes(n)) sweep.queue.push(n);
      }
    }
  }

  const finished = sweep.queue.length === 0;
  if (finished) {
    sweep.finishedAt = new Date().toISOString();
    const previous = await env.STATE.get<Sweep>(REPORT_KEY, 'json');
    const report = { ...sweep, queue: [], seen: undefined, from: undefined };
    await env.STATE.put(REPORT_KEY, JSON.stringify(report));
    await env.STATE.put(`report:${sweep.id}`, JSON.stringify(report), { expirationTtl: 30 * DAY / 1000 });
    await notify(env, sweep, previous);
  }
  await env.STATE.put(SWEEP_KEY, JSON.stringify(sweep));
  return { sweep, finished };
}

async function notify(env: Env, sweep: Sweep, previous: Sweep | null) {
  if (!env.SLACK_WEBHOOK_URL) return;
  const before = new Set((previous?.broken ?? []).map((b) => b.url));
  const fresh = sweep.broken.filter((b) => !before.has(b.url));
  const fixed = (previous?.broken ?? []).filter((b) => !sweep.broken.some((x) => x.url === b.url));
  if (!fresh.length && !fixed.length) return;
  const lines = [`Link check on ${sweep.base}: ${sweep.broken.length} broken of ${sweep.checked} checked.`];
  for (const b of fresh.slice(0, 15)) lines.push(`• NEW ${b.status} ${b.url} (from ${b.from[0] ?? '?'})`);
  for (const b of fixed.slice(0, 10)) lines.push(`• fixed ${b.url}`);
  await fetch(env.SLACK_WEBHOOK_URL, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ text: lines.join('\n') }) });
}

export default {
  async scheduled(_event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    ctx.waitUntil(step(env));
  },

  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    const json = (data: unknown, status = 200) => new Response(JSON.stringify(data, null, 2), { status, headers: { 'content-type': 'application/json; charset=utf-8' } });
    const authed = () => !!env.ADMIN_KEY && url.searchParams.get('key') === env.ADMIN_KEY;

    if (req.method === 'GET' && url.pathname === '/') {
      const report = await env.STATE.get(REPORT_KEY);
      return report ? new Response(report, { headers: { 'content-type': 'application/json; charset=utf-8' } }) : json({ message: 'No finished sweep yet. The cron fills one batch every tick; POST /run?key=… to move it along.' }, 404);
    }
    if (req.method === 'GET' && url.pathname === '/report.md') {
      const report = await env.STATE.get<Sweep>(REPORT_KEY, 'json');
      return report ? new Response(renderMarkdown(report), { headers: { 'content-type': 'text/markdown; charset=utf-8' } }) : new Response('No finished sweep yet.\n', { status: 404 });
    }
    if (req.method === 'GET' && url.pathname === '/status') {
      const sweep = await env.STATE.get<Sweep>(SWEEP_KEY, 'json');
      return json(sweep ? { id: sweep.id, startedAt: sweep.startedAt, finishedAt: sweep.finishedAt, queued: sweep.queue.length, checked: sweep.checked, broken: sweep.broken.length } : { message: 'No sweep started.' });
    }
    if (req.method === 'POST' && url.pathname === '/run') {
      if (!authed()) return json({ error: 'unauthorised' }, 401);
      const { sweep, finished } = await step(env);
      return json({ finished, queued: sweep.queue.length, checked: sweep.checked, broken: sweep.broken.length });
    }
    if (req.method === 'POST' && url.pathname === '/reset') {
      if (!authed()) return json({ error: 'unauthorised' }, 401);
      await env.STATE.delete(SWEEP_KEY);
      return json({ ok: true });
    }
    return json({ error: 'not found' }, 404);
  },
};
