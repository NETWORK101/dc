#!/usr/bin/env python3
"""Render the docs/*.md files to docs/*.html with the site's type and tokens. No dependencies."""
import re, sys, html, pathlib

STYLE = """
:root{--bg:#F3F4F0;--surface:#FBFBF9;--surface-2:#F0F1EC;--line:#D4D8D2;--line-2:#B9BFB8;--ink:#171A21;--ink-2:#4A5060;--ink-3:#7A8194;--accent:#2B4CFF;--mono-bg:#EDEFE9;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#12151C;--surface:#1A1E27;--surface-2:#20252F;--line:#2B303C;--line-2:#3C4353;--ink:#E8EAF0;--ink-2:#AAB0C0;--ink-3:#767D90;--accent:#6D85FF;--mono-bg:#141820;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#12151C;--surface:#1A1E27;--surface-2:#20252F;--line:#2B303C;--line-2:#3C4353;--ink:#E8EAF0;--ink-2:#AAB0C0;--ink-3:#767D90;--accent:#6D85FF;--mono-bg:#141820;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"IBM Plex Sans","Segoe UI",Helvetica,Arial,sans-serif;font-size:16px;line-height:1.6;padding-inline:clamp(16px,4vw,40px);padding-block:0}
.wrap{max-width:860px;margin-inline:auto}
.mast{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;padding-block:18px;border-bottom:1px solid var(--line);margin-bottom:40px}
.brand{display:flex;align-items:baseline;gap:12px;text-decoration:none;color:var(--ink)}
.brand .name{font-family:"Bricolage Grotesque","Helvetica Neue",Arial,sans-serif;font-weight:700;font-size:20px;letter-spacing:-.02em}
.brand .by{font-size:12px;color:var(--ink-3)}
.mast a.back{font-size:13px;color:var(--ink-2);text-decoration:none;padding:6px 10px;border:1px solid var(--line-2);border-radius:6px}
h1,h2,h3,h4{font-family:"Bricolage Grotesque","Helvetica Neue",Arial,sans-serif;font-weight:600;line-height:1.15;letter-spacing:-.01em;text-wrap:balance;margin:0}
h1{font-size:clamp(30px,4.5vw,44px);font-weight:500;margin-bottom:12px}
h2{font-size:26px;margin:48px 0 14px;padding-top:24px;border-top:1px solid var(--line)}
h3{font-size:19px;margin:28px 0 10px}
p{margin:0 0 14px;max-width:70ch}
h1+p em{color:var(--ink-2)}
a{color:var(--accent)}
ul,ol{padding-left:22px;margin:0 0 14px}
li{margin-bottom:6px}
code{font-family:"IBM Plex Mono",Consolas,monospace;font-size:.9em;background:var(--mono-bg);padding:1px 5px;border-radius:4px}
pre{background:var(--mono-bg);padding:12px 14px;border-radius:6px;overflow-x:auto;font-size:13px;line-height:1.5;margin:0 0 16px}
pre code{background:none;padding:0;font-size:inherit}
.tbl{overflow-x:auto;margin:0 0 18px}
table{border-collapse:collapse;font-size:14px;width:100%}
th{text-align:left;font-weight:600;font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:var(--ink-2);padding:8px 10px;border-bottom:2px solid var(--line-2);white-space:nowrap}
td{padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
hr{border:0;border-top:1px solid var(--line);margin:32px 0}
blockquote{margin:0 0 14px;padding:8px 14px;border-left:3px solid var(--line-2);color:var(--ink-2)}
footer{border-top:1px solid var(--line);margin-top:56px;padding-block:24px 40px;font-size:13px;color:var(--ink-3)}
"""

FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,300..800&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">'

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', lambda m: '<code>' + m.group(1) + '</code>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
    return s

def render(md):
    lines = md.split('\n'); out = []; i = 0; para = []
    def flush():
        if para:
            out.append('<p>' + inline(' '.join(x.strip() for x in para)) + '</p>'); para.clear()
    while i < len(lines):
        ln = lines[i]
        if ln.startswith('```'):
            flush(); j = i + 1; buf = []
            while j < len(lines) and not lines[j].startswith('```'): buf.append(lines[j]); j += 1
            out.append('<pre><code>' + html.escape('\n'.join(buf)) + '</code></pre>'); i = j + 1; continue
        if re.match(r'^#{1,4} ', ln):
            flush(); lvl = len(ln) - len(ln.lstrip('#')); out.append(f'<h{lvl}>{inline(ln[lvl+1:].strip())}</h{lvl}>'); i += 1; continue
        if re.match(r'^-{3,}\s*$', ln):
            flush(); out.append('<hr>'); i += 1; continue
        if ln.startswith('|'):
            flush(); rows = []
            while i < len(lines) and lines[i].startswith('|'): rows.append(lines[i]); i += 1
            cells = lambda r: [c.strip() for c in r.strip().strip('|').split('|')]
            head = cells(rows[0]); body = [cells(r) for r in rows[2:]] if len(rows) > 1 and re.match(r'^\|[\s:-]+\|', rows[1]) else [cells(r) for r in rows[1:]]
            t = '<div class="tbl"><table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in head) + '</tr></thead><tbody>'
            for r in body: t += '<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>'
            out.append(t + '</tbody></table></div>'); continue
        m = re.match(r'^(\s*)([-*]|\d+\.) (.*)', ln)
        if m:
            flush(); ordered = m.group(2)[0].isdigit(); tag = 'ol' if ordered else 'ul'; items = []
            while i < len(lines):
                m2 = re.match(r'^(\s*)([-*]|\d+\.) (.*)', lines[i])
                if m2 and len(m2.group(1)) == len(m.group(1)):
                    items.append(m2.group(3)); i += 1
                elif lines[i].startswith(' ' * (len(m.group(1)) + 2)) and lines[i].strip() and items:
                    items[-1] += ' ' + lines[i].strip(); i += 1
                else: break
            out.append(f'<{tag}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + f'</{tag}>'); continue
        if ln.startswith('>'):
            flush(); buf = []
            while i < len(lines) and lines[i].startswith('>'): buf.append(lines[i][1:].strip()); i += 1
            out.append('<blockquote>' + inline(' '.join(buf)) + '</blockquote>'); continue
        if not ln.strip(): flush(); i += 1; continue
        para.append(ln); i += 1
    flush(); return '\n'.join(out)

def build(src):
    md = src.read_text(); body = render(md)
    title = re.search(r'^# (.+)$', md, re.M).group(1).split(' — ')[0].strip()
    doc = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
{FONTS}
<style>{STYLE}</style>
</head>
<body>
<div class="wrap">
<header class="mast">
  <a class="brand" href="https://agentsandhumans.ai"><span class="name">The Future of Work</span><span class="by">by agentsandhumans.ai</span></a>
  <a class="back" href="../index.html">Back to the prototype</a>
</header>
<main>
{body}
</main>
<footer>The Future of Work is a Phase 0 prototype from agentsandhumans.ai. Sample data throughout.</footer>
</div>
</body>
</html>
'''
    dst = src.with_suffix('.html'); dst.write_text(doc); print('wrote', dst, len(doc))

for f in sorted(pathlib.Path('docs').glob('*.md')): build(f)
