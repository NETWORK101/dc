#!/usr/bin/env python3
"""Print every live field note and essay on agentsandhumans.ai as one JSON line each (prefix INV).

Reads the sitemap for note slugs and the site's Web MCP endpoint for each item's fields.
Runs from GitHub Actions because the Claude sandbox cannot reach the site.
"""
import json, re, sys, urllib.request

BASE = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'https://agentsandhumans.ai'
UA = 'agentsandhumans-inventory/1.0'

def get(path):
    req = urllib.request.Request(BASE + path, headers={'User-Agent': UA, 'Accept': '*/*'})
    with urllib.request.urlopen(req, timeout=30) as r: return r.read().decode('utf-8', 'replace')

def rpc(calls):
    body = json.dumps([{'jsonrpc': '2.0', 'id': i, 'method': 'tools/call', 'params': {'name': n, 'arguments': a}} for i, (n, a) in enumerate(calls)]).encode()
    req = urllib.request.Request(BASE + '/api/mcp', data=body, method='POST', headers={'User-Agent': UA, 'content-type': 'application/json', 'accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r: res = json.loads(r.read().decode())
    out = {}
    for item in res:
        text = ''.join(c.get('text', '') for c in item.get('result', {}).get('content', []) if c.get('type') == 'text')
        out[item['id']] = text
    return [out.get(i, '') for i in range(len(calls))]

sitemap = get('/sitemap.xml')
slugs = re.findall(r'<loc>' + re.escape(BASE) + r'/note/([^<]+)</loc>', sitemap)
print(f'# {len(slugs)} note slugs in sitemap', file=sys.stderr)
for i in range(0, len(slugs), 15):
    chunk = slugs[i:i+15]
    for slug, text in zip(chunk, rpc([('get_field_note', {'id': s}) for s in chunk])):
        try:
            d = json.loads(text)
        except Exception:
            print('INV ' + json.dumps({'kind': 'note', 'slug': slug, 'error': text[:200]})); continue
        d.pop('prose', None); d.pop('_source', None)
        print('INV ' + json.dumps({'kind': 'note', 'slug': slug, 'raw': d}, ensure_ascii=False))

essays = [x for x in json.loads(get('/api/search.json')) if x.get('kind') == 'essay']
print(f'# {len(essays)} essays', file=sys.stderr)
eslugs = [e['url'].split('/notes/')[-1] for e in essays]
texts = rpc([('get_essay', {'slug': s}) for s in eslugs])
for e, s, t in zip(essays, eslugs, texts):
    print('INV ' + json.dumps({'kind': 'essay', 'slug': s, 'title': e['label'], 'head': t[:700]}, ensure_ascii=False))
