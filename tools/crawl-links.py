#!/usr/bin/env python3
"""Crawl a site from one origin and report every internal link that does not resolve.

Usage: crawl-links.py BASE_URL [--out report.json] [--max 2000] [--externals]

Follows same-origin links only. Reports: HTTP status per URL, redirect chains, the pages that
link to each broken target, and (with --externals) a HEAD check on off-site links.
"""
import sys, json, re, html, time, argparse, urllib.request, urllib.error, urllib.parse
from collections import deque, defaultdict
from html.parser import HTMLParser

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and a.get('href'): self.links.append(('a', a['href']))
        elif tag in ('img', 'script', 'iframe', 'source', 'video', 'audio') and a.get('src'): self.links.append((tag, a['src']))
        elif tag == 'link' and a.get('href') and a.get('rel') in ('stylesheet', 'icon', 'alternate', 'canonical'): self.links.append(('link', a['href']))
        elif tag == 'form' and a.get('action'): self.links.append(('form', a['action']))

ap = argparse.ArgumentParser(); ap.add_argument('base'); ap.add_argument('--out', default='link-report.json')
ap.add_argument('--max', type=int, default=2000); ap.add_argument('--externals', action='store_true'); ap.add_argument('--delay', type=float, default=0.0)
ap.add_argument('--allow-403', default='chatgpt.com,claude.ai', help='hosts whose 403 is a bot block, not a breakage')
args = ap.parse_args()
base = args.base.rstrip('/'); origin = urllib.parse.urlparse(base)
opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
UA = 'agentsandhumans-link-check/1.0'

def fetch(url, method='GET'):
    req = urllib.request.Request(url, method=method, headers={'User-Agent': UA, 'Accept': 'text/html,*/*'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read() if method == 'GET' else b''
            return r.status, r.geturl(), r.headers.get('content-type', ''), body
    except urllib.error.HTTPError as e:
        return e.code, e.geturl() or url, e.headers.get('content-type', '') if e.headers else '', b''
    except Exception as e:
        return 0, url, str(e), b''

def norm(href, from_url):
    href = html.unescape(href.strip())
    if href.startswith(('mailto:', 'tel:', 'javascript:', 'data:')) or href.startswith('#'): return None
    u = urllib.parse.urljoin(from_url, href)
    p = urllib.parse.urlparse(u)
    return urllib.parse.urlunparse((p.scheme, p.netloc, p.path or '/', '', p.query, ''))

def internal(u):
    p = urllib.parse.urlparse(u); return (p.scheme, p.netloc) == (origin.scheme, origin.netloc)

seen = {}; sources = defaultdict(set); kinds = {}; queue = deque([base + '/']); externals = set()
while queue and len(seen) < args.max:
    url = queue.popleft()
    if url in seen: continue
    status, final, ctype, body = fetch(url)
    # SSR sites redirect missing rows to /404; treat a final URL of /404 or an error page as broken
    final_path = urllib.parse.urlparse(final).path
    broken = status >= 400 or status == 0 or final_path.rstrip('/') == '/404'
    seen[url] = {'status': status, 'final': final if final != url else None, 'broken': broken, 'type': ctype.split(';')[0]}
    if args.delay: time.sleep(args.delay)
    if status == 200 and 'html' in ctype and internal(url):
        p = Links()
        try: p.feed(body.decode('utf-8', 'replace'))
        except Exception: pass
        for kind, href in p.links:
            n = norm(href, url)
            if not n: continue
            kinds.setdefault(n, kind)
            if internal(n):
                sources[n].add(url)
                if n not in seen: queue.append(n)
            else:
                externals.add(n); sources[n].add(url)

ext_results = {}
if args.externals:
    for e in sorted(externals):
        st, fin, ct, _ = fetch(e, 'HEAD')
        if st in (405, 403, 0): st, fin, ct, _ = fetch(e, 'GET')
        host = urllib.parse.urlparse(e).hostname or ''
        bot_blocked = st == 403 and any(host == a or host.endswith('.' + a) for a in args.allow_403.split(',') if a)
        ext_results[e] = {'status': st, 'final': fin if fin != e else None, 'broken': (st >= 400 or st == 0) and not bot_blocked}

broken = {u: v for u, v in seen.items() if v['broken']}
report = {
    'base': base, 'crawled': len(seen), 'broken_internal': len(broken),
    'broken': [{'url': u, 'status': v['status'], 'final': v['final'], 'kind': kinds.get(u, 'a'), 'linked_from': sorted(sources[u])[:10]} for u, v in sorted(broken.items())],
    'redirects': [{'url': u, 'final': v['final']} for u, v in sorted(seen.items()) if v['final'] and not v['broken']],
    'externals': {'count': len(externals), 'checked': bool(args.externals), 'broken': [{'url': u, **r, 'linked_from': sorted(sources[u])[:5]} for u, r in sorted(ext_results.items()) if r['broken']]},
}
json.dump(report, open(args.out, 'w'), indent=2)
print(f"crawled {len(seen)} internal URLs, {len(broken)} broken, {len(externals)} external links{' (checked)' if args.externals else ' (not checked)'}")
for b in report['broken']:
    print(f"  {b['status']:>3}  {b['url']}  <- {', '.join(b['linked_from'][:3])}")
for b in report['externals']['broken']: print(f"  ext {b['status']:>3}  {b['url']}")
