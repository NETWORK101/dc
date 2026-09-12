# link-check

A Cloudflare Worker that crawls agentsandhumans.ai on a schedule and reports every link that does
not resolve. Same layout as the Workers under `workers/` in the site repo, so it can be copied there.

## How it works

A sweep is a queue of URLs kept in KV. Every cron tick (10 minutes) takes one batch off the queue,
fetches each URL, records the status, and pushes any new same-origin links it finds. Off-site links
get a HEAD request with a GET fallback. When the queue runs dry the sweep is finished: the report is
stored under `report:latest`, kept for 30 days under `report:<id>`, and a Slack message goes out if
a breakage is new since the previous sweep or an old one is fixed. A fresh sweep starts once the
last one is a day old.

Batching keeps every tick under the Workers subrequest limit. On the free plan set `BATCH` to 40;
on the paid plan you can raise it to a few hundred and lower the cron frequency.

An SSR page that redirects a missing row to `/404` counts as broken even though the final response
is 200, which is how the site's pattern, note, and principle routes fail.

## Endpoints

| Method | Path | What |
|---|---|---|
| GET | `/` | Latest finished report as JSON |
| GET | `/report.md` | The same as Markdown |
| GET | `/status` | Queue length and progress of the current sweep |
| POST | `/run?key=ADMIN_KEY` | Process one batch now |
| POST | `/reset?key=ADMIN_KEY` | Drop the current sweep |

## Deploy

```
cd cloudflare/link-check
npm install
npx wrangler kv namespace create link-check-state   # paste the id into wrangler.jsonc
npx wrangler secret put ADMIN_KEY
npx wrangler secret put SLACK_WEBHOOK_URL            # optional
npx wrangler deploy
```

Then push a sweep through by hand to see the first report without waiting an hour:

```
for i in $(seq 1 8); do curl -s -X POST "https://link-check.<account>.workers.dev/run?key=$ADMIN_KEY"; echo; done
curl -s https://link-check.<account>.workers.dev/report.md
```

## Vars

| Var | Default | Meaning |
|---|---|---|
| `BASE_URL` | `https://agentsandhumans.ai` | Origin to crawl |
| `BATCH` | `40` | URLs fetched per tick |
| `CHECK_EXTERNALS` | `true` | HEAD-check off-site links |
| `IGNORE` | `/api/,/storybook/iframe.html` | Path prefixes never crawled (POST-only endpoints, embeds) |
| `ALLOW_403_HOSTS` | `chatgpt.com,claude.ai` | Off-site hosts whose 403 is a bot block, not a breakage |

## Tests

```
npm test
```
