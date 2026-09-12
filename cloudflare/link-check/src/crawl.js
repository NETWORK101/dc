// Pure helpers shared by the Worker and its tests. No Workers APIs in here.

/** Normalise an href found on `from` into an absolute URL without a fragment, or null if it is not a link to check. */
export function normalizeHref(href, from) {
  const h = href.trim();
  if (!h || h.startsWith('#')) return null;
  if (/^(mailto|tel|javascript|data|sms):/i.test(h)) return null;
  let u;
  try { u = new URL(h, from); } catch { return null; }
  if (u.protocol !== 'http:' && u.protocol !== 'https:') return null;
  u.hash = '';
  return u.toString();
}

/** True when `url` is on the same origin as `base`. */
export function sameOrigin(url, base) {
  try { return new URL(url).origin === new URL(base).origin; } catch { return false; }
}

/** Extract candidate links from an HTML string: anchors, images, scripts, iframes, stylesheets, forms. */
export function extractLinks(html) {
  const out = [];
  const re = /<(a|img|script|iframe|source|link|form)\b([^>]*)>/gi;
  let m;
  while ((m = re.exec(html))) {
    const tag = m[1].toLowerCase(); const attrs = m[2];
    const pick = (name) => { const r = new RegExp(`\\b${name}\\s*=\\s*("([^"]*)"|'([^']*)'|([^\\s>]+))`, 'i').exec(attrs); return r ? (r[2] ?? r[3] ?? r[4]) : null; };
    let href = null;
    if (tag === 'a') href = pick('href');
    else if (tag === 'form') href = pick('action');
    else if (tag === 'link') { const rel = (pick('rel') || '').toLowerCase(); if (/stylesheet|icon|alternate|canonical/.test(rel)) href = pick('href'); }
    else href = pick('src');
    if (href) out.push({ tag, href: href.replace(/&amp;/g, '&') });
  }
  return out;
}

/** A path is ignored when it starts with any of the configured prefixes. */
export function ignored(url, prefixes) {
  const p = new URL(url).pathname + new URL(url).search;
  return prefixes.some((pre) => pre && p.startsWith(pre));
}

/** Decide whether a fetched result counts as broken. An SSR site that redirects missing rows to /404 counts too. */
export function isBroken(status, finalUrl) {
  if (status === 0 || status >= 400) return true;
  try { if (new URL(finalUrl).pathname.replace(/\/$/, '') === '/404') return true; } catch {}
  return false;
}

/** Render a sweep as Markdown. */
export function renderMarkdown(sweep) {
  const lines = [`# Link check · ${sweep.base}`, '', `Sweep ${sweep.id} · started ${sweep.startedAt}${sweep.finishedAt ? ` · finished ${sweep.finishedAt}` : ' · in progress'}`, '', `Checked ${sweep.checked} URLs (${sweep.internal} internal, ${sweep.external} external). Broken: ${sweep.broken.length}.`, ''];
  if (sweep.broken.length) {
    lines.push('| status | url | linked from |', '|---|---|---|');
    for (const b of sweep.broken) lines.push(`| ${b.status} | ${b.url} | ${b.from.slice(0, 3).join('<br>')} |`);
  } else lines.push('No broken links.');
  return lines.join('\n');
}
