import { test } from 'node:test';
import assert from 'node:assert/strict';
import { normalizeHref, sameOrigin, extractLinks, ignored, isBroken, renderMarkdown } from './src/crawl.js';

test('normalizeHref resolves relative links and drops fragments and non-http schemes', () => {
  assert.equal(normalizeHref('/patterns/eval-comparison-view#top', 'https://agentsandhumans.ai/'), 'https://agentsandhumans.ai/patterns/eval-comparison-view');
  assert.equal(normalizeHref('notes', 'https://agentsandhumans.ai/patterns/'), 'https://agentsandhumans.ai/patterns/notes');
  assert.equal(normalizeHref('#subscribe', 'https://agentsandhumans.ai/'), null);
  assert.equal(normalizeHref('mailto:hi@example.com', 'https://agentsandhumans.ai/'), null);
});

test('sameOrigin compares scheme and host', () => {
  assert.equal(sameOrigin('https://agentsandhumans.ai/notes', 'https://agentsandhumans.ai'), true);
  assert.equal(sameOrigin('https://github.com/x', 'https://agentsandhumans.ai'), false);
});

test('extractLinks finds anchors, assets, stylesheets, and form actions', () => {
  const html = `<a href="/a">a</a><a href='/b'>b</a><img src="/c.png"><link rel="stylesheet" href="/d.css"><link rel="preload" href="/e"><form action="/api/subscribe"><script src="/f.js"></script><a href="/g?x=1&amp;y=2">g</a>`;
  const hrefs = extractLinks(html).map((l) => l.href);
  assert.deepEqual(hrefs, ['/a', '/b', '/c.png', '/d.css', '/api/subscribe', '/f.js', '/g?x=1&y=2']);
});

test('ignored matches path prefixes', () => {
  assert.equal(ignored('https://agentsandhumans.ai/api/subscribe', ['/api/']), true);
  assert.equal(ignored('https://agentsandhumans.ai/notes', ['/api/']), false);
});

test('isBroken treats 4xx, 5xx, network errors, and a redirect to /404 as broken', () => {
  assert.equal(isBroken(200, 'https://agentsandhumans.ai/notes'), false);
  assert.equal(isBroken(404, 'https://agentsandhumans.ai/x'), true);
  assert.equal(isBroken(0, 'https://agentsandhumans.ai/x'), true);
  assert.equal(isBroken(200, 'https://agentsandhumans.ai/404'), true);
  assert.equal(isBroken(403, 'https://chatgpt.com/?q=x', ['chatgpt.com', 'claude.ai']), false);
  assert.equal(isBroken(403, 'https://www.forbes.com/x', ['chatgpt.com']), true);
});

test('renderMarkdown lists breakages', () => {
  const md = renderMarkdown({ id: '1', base: 'https://agentsandhumans.ai', startedAt: 't', finishedAt: 't2', checked: 3, internal: 2, external: 1, broken: [{ url: 'https://agentsandhumans.ai/x', status: 404, final: null, from: ['https://agentsandhumans.ai/'] }] });
  assert.match(md, /\| 404 \| https:\/\/agentsandhumans.ai\/x \|/);
});
