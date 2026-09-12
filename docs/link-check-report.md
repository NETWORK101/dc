# Link check · agentsandhumans.ai · 2026-09-12

Crawled from GitHub Actions (run 34719265551 on NETWORK101/dc) because the Claude sandbox cannot
reach the site. Same-origin crawl from `/`, every off-site link HEAD-checked with a GET fallback.

| | |
|---|---|
| Internal URLs crawled | 162 |
| Internal broken | 0 real (2 false positives, below) |
| External links | 173 |
| External failing | 73, of which 56 are bot-blocked by design (below) |

## The two links reported as dead

`→ COMPARISON VIEW` and `→ OFF-BRIEF ALERT` on the homepage essay cards. Both pattern pages are
live and return 200:

- https://agentsandhumans.ai/patterns/eval-comparison-view
- https://agentsandhumans.ai/patterns/off-brief-alert

The ref on the essay cards is not a link. In `site/src/pages/index.astro` the whole card is one
`<a href="/notes/<slug>">`, and the pattern ref inside it is a `<span class="pattern-ref">`
styled to look like the lead essay's real `<a class="pattern-ref">`. A tap on the ref opens the
essay, not the pattern. On a phone the card fills the screen, so it reads as the lead essay and
the ref reads as a dead link. Fix: make the card an `<article>`, keep the essay link on the art,
meta, title and dek, and make the ref its own `<a href="/patterns/<slug>">`.

## Internal false positives

| URL | Why it is not a bug |
|---|---|
| `/api/subscribe` | Form action, POST only. A GET returns 404 by design. Excluded in the Worker via `IGNORE`. |
| `/cdn-cgi/l/email-protection` | Cloudflare's email obfuscation rewrites `mailto:` links to this path. It works in a browser. |

## External links that fail

**Bot-blocked, not broken (56).** Every pattern page carries two "ask an assistant" links,
`https://chatgpt.com/?q=…` and `https://claude.ai/new?q=…`. Both hosts return 403 to any
non-browser client. They work for a person. The Worker treats 403 from these two hosts as fine.

**Paywalled or bot-blocked news (6).** openai.com, axios.com, forbes.com, reuters.com and
help.openai.com return 401 or 403 to crawlers. Worth a manual click but almost certainly fine.

**Real 404s to fix in content (11).**

| Status | URL | Linked from |
|---|---|---|
| 404 | https://freeplay.ai/blog/accelerate-ai-product-development-with-freeplay-s-new-eval-creation-alignment-tools | /note/agree-or-disagree-with-the-judge-ten-at-a-time, /patterns/eval-case-drilldown |
| 404 | https://huggingface.co/blog/agent-intrusion-timeline | /note/the-alert-fired-and-did-not-wake-anyone, /patterns/emergency-stop |
| 404 | https://metr.org/blog/hugging-face-investigation/ | /note/independent-investigators-found-a-swarm-that-organized-itself, /patterns/agent-identity |
| 404 | https://techcrunch.com/2026/09/04/openai-rogue-agents-no-process/ | /note/the-agents-keep-escaping-and-there-is-no-standing-process, /patterns/emergency-stop |
| 404 | https://www.anthropic.com/news/claude-code | /note/claude-code-multi-file-editing, /patterns/recovery |
| 404 | https://www.linkedin.com/in/danielclarkux/ | /about |
| 404 | https://icons.duckduckgo.com/ip3/engineering.atspotify.com.ico | favicon for a Spotify engineering source |
| 404 | https://icons.duckduckgo.com/ip3/freeplay.ai.ico | favicon for Freeplay |
| 404 | https://icons.duckduckgo.com/ip3/time.com.ico | favicon for Time |

The five article URLs are source links in field notes. Each needs the corrected URL from the
original source, or the note's source link removed. The LinkedIn URL on the About page may be a
bot block rather than a wrong URL; LinkedIn returns 404 to unauthenticated crawlers for some
profiles. The three favicon URLs come from the source-icon helper and fail quietly; the site
should fall back to a neutral glyph when DuckDuckGo has no icon.

## How to re-run

- GitHub Actions: the `Link check` workflow in NETWORK101/dc runs daily at 06:17 UTC and on demand
  (Actions tab, Run workflow). The report is the job summary and the `link-report` artifact.
- Cloudflare: `cloudflare/link-check` is a Worker that runs the same crawl in batches on a cron,
  keeps the report in KV, and posts new breakages to Slack. See its README to deploy.
- Locally: `python3 tools/crawl-links.py https://agentsandhumans.ai --externals`.
