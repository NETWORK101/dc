# An agentic software factory — proof-of-concept outline

*Agents in cloud sandboxes work the backlog around the clock, and humans approve what ships. This outline covers a working proof of concept you can pitch and then scale. Hermes Agent, Claude Code and other models sit behind one control plane on Cloudflare, and Agent Reach gives the agents read access to the wider internet.*

## The recommendation in one line

Build the control plane yourself and rent everything else. The control plane is the loop that turns a backlog item into a reviewed, tested pull request: intake, dispatch, verify, human gate and metrics. That loop is your product and your pitch. The agent harnesses (Claude Code, Hermes Agent), the sandboxes (Cloudflare) and the research layer (Agent Reach) plug in behind small adapters, so you can swap models and vendors without a rewrite.

## Six design rules

1. **Code runs the loop, and agents make the judgment calls.** The states, retries, budgets and merge rights are ordinary code. Agents handle only scouting, triage, planning, coding and review. A system that runs 24/7 can't rely on an LLM remembering to check the queue.
2. **Each ticket gets its own sandbox and its own pull request.** Every item gets a fresh, isolated container started from a prebuilt image of the repo. Only git commits and the playbook carry over between tickets.
3. **Agents never merge.** They open pull requests, CI and a reviewer agent check them, and a human merges. Branch protection enforces this, so it doesn't depend on a prompt.
4. **The ticket spec matters more than the model.** Write a Definition of Ready and have a triage agent enforce it before you pay for a bigger model.
5. **Human review time is the real limit.** You can run 50 sandboxes at once, but if each PR takes 20 minutes to review, the reviewer sets the pace. Put as much work into the PR the reviewer reads as into the code the agent writes.
6. **Content from outside is data, never instructions.** A Reddit thread, an issue on someone else's repo or a video transcript can carry a prompt injection. Agents that read the internet can draft issues, but only a maintainer can make one `agent-ready`.

## Architecture

```
  Signals: issues on your dependencies' repos, Reddit, X, YouTube, the web
      │  read-only, through Agent Reach on the Reach host
      ▼
  Scout agent drafts issues (labeled "scout", never "agent-ready")
      ▼
  Backlog (GitHub Issues + Projects board)
      │  webhook on the "agent-ready" label, plus a cron sweep every 10 minutes
      ▼
  Control plane on Cloudflare (Workers + Workflows: state machine, queue, budgets, routing)
      │  dispatch: one ticket → one sandbox
      ▼
  Cloudflare Sandbox (a container started from the repo's image)
      │  harness inside: Claude Code headless, Hermes Agent, or another
      │  model calls → AI Gateway (holds keys, enforces spend limits per ticket)
      │  research calls → the Worker → the Reach service
      │  output: branch + pull request with plan, tests, evidence and cost
      ▼
  Verifier (CI + a reviewer agent on a different model + up to 2 fix rounds)
      │
      ▼
  Human gate (GitHub review, or one-tap approve in Slack) → merge

  Reach host (one small always-on VM, linked to Cloudflare by a Tunnel):
    Foreman (Hermes Agent in Slack or Telegram): status, triage, "run #42", morning digest
    Agent Reach + a thin Reach service: read-only GitHub, YouTube, web, Reddit, X and more

  Metrics store (Supabase) + dashboard: cost per PR, autonomy rate, cycle time, review minutes
```

### Ticket lifecycle

`new → triaged → ready → running → pr_open → fixing → in_review → merged`

Issues the Scout drafts enter at `new`, like any other issue. A ticket can also leave the loop three ways:

- `needs_info` sends it back to a human with questions.
- `blocked` means its budget or fix rounds ran out.
- `rejected` means a human closed the PR.

Every state change is a database row, and the dashboard and the pitch numbers come from those rows.

## The team of agents

| # | Agent | What it does | Runs on | When |
|---|---|---|---|---|
| 1 | **Scout** | Uses Agent Reach to read new issues on the repos you depend on, the last day of Reddit and X threads about your product, and relevant talks or docs. Drafts an issue for each real problem or request, with links to the source. | A cheap model on the Reach host | Nightly |
| 2 | **Triage** | Reads each new issue and checks it against the Definition of Ready. Asks clarifying questions in the issue, flags duplicates, splits big items, then sizes and labels the rest. | A cheap model: Claude Haiku 5.5 or an open Hermes model | On every new issue, plus a nightly sweep |
| 3 | **Planner** | Reads the code and writes a short plan and test plan into the issue before any code is written. Uses Agent Reach to check upstream issues, changelogs and docs for the libraries involved. | Same model as the Builder | When a ticket is picked up |
| 4 | **Builder** | Writes the code and tests in the sandbox, runs the test suite and opens the PR. | Claude Code headless with Claude Sonnet 5.5 or Opus 5.5, or Hermes Agent for chores | Once per ticket |
| 5 | **Reviewer** | Checks the diff against the acceptance criteria and the repo's rules, and flags risky files. Uses a different model from the Builder so they don't share blind spots. | A different model family or tier | Once per PR |
| 6 | **Fixer** | Reads CI failures and review comments and pushes fixes. After 2 rounds it hands the ticket back to a human. | The Builder's model | On red CI or review comments |
| 7 | **Foreman** | The always-on front desk. Answers "what's in the queue", starts and stops tickets on request, and posts a morning digest that includes what the Scout found. Turns lessons from failed tickets into playbook changes. | Hermes Agent on the Reach host: messaging gateway, cron, memory, skills | 24/7 |

In the proof of concept, the Planner and Builder can share one session. Split them later if plans need a human's approval before coding starts.

## Where Hermes fits

[Hermes Agent](https://github.com/NousResearch/hermes-agent) (Nous Research, MIT license) suits the always-on parts of the factory:

- It runs on a $5 VPS or on serverless infrastructure. One gateway process connects it to Slack, Telegram, Discord, WhatsApp and Signal.
- It has a built-in cron scheduler, isolated subagents and persistent memory. After complex tasks it writes skill files it can reuse.
- It has six built-in terminal backends: local, Docker, SSH, Modal, Daytona and Vercel Sandbox.
- It works with any model: Nous Portal, OpenRouter, OpenAI, Anthropic or your own endpoint.

For the Builder, use whichever harness merges the most PRs on your repo, and measure that in Phase 0. I expect a frontier coding model in a coding harness to win today: Claude Code headless, or the Claude Agent SDK if you want programmatic control. Keep Hermes as a second Builder lane for chores, installed in the sandbox image just like Claude Code. It also serves customers who need open models. Because of the adapter, switching lanes is a config change.

Write the repo playbook and skills once, in the Agent Skills format ([agentskills.io](https://agentskills.io)). Hermes and Claude Code both read that format, so the playbook doesn't lock you into either harness.

## Where Agent Reach fits

[Agent Reach](https://github.com/Panniantong/Agent-Reach) (MIT, Python) gives any shell-capable agent read access to platforms its built-in web tools can't reach well. It works with Claude Code, Codex, Hermes Agent and OpenClaw. Agents call `agent-reach <channel> <action>`, and every command returns one JSON object. Each platform has an ordered list of backends: if one breaks, the next is tried. For example, web reading tries Jina Reader first, then Exa.

| Channel | Level | What it can do | Needs |
|---|---|---|---|
| GitHub | Default | Search repos; read READMEs, issues and PRs with comments | Nothing |
| Web | Default | Search and read pages | Nothing |
| YouTube | Default | Search, video info, subtitles, speech-to-text | Nothing; speech-to-text needs a Groq or OpenAI key |
| Bilibili, V2EX | Default | Search and read | Nothing |
| Reddit | Optional | Search posts, read posts and comments, browse subreddits | A logged-in account |
| LinkedIn | Optional | Search jobs and read job details | Public jobs need no login; site search does |
| Xiaohongshu, Xueqiu, Boss, Xiaoyuzhou | Optional | Chinese social, finance, jobs and podcasts | Login or a Groq key |
| X, Facebook, Instagram | Experimental | Search and read profiles and posts | Login. May break at any time |

**Its jobs in the factory:**

- **Scout:** turn outside signals into draft issues. That includes a breaking change reported on a dependency's GitHub, a bug complaint on Reddit, or a feature people keep asking for on X.
- **Triage and Planner:** check whether a bug is already known upstream, read the library's issue thread and changelog, and pull the transcript of the talk that explains an API.
- **Foreman:** put "what people said about us overnight" in the morning digest.
- **Social growth:** the same Reach host can serve the Listener agent in `docs/social-agents-plan.md`. Reddit and X have their own channels. Hacker News and dev.to are read through the web channel.

**How to run it:**

- **Not in every builder sandbox.** Logged-in channels keep a browser profile and site sessions under `~/.agent-reach/`, and a human logs in once in a browser window (`agent-reach login <channel>`). That fits one persistent machine, not throwaway containers.
- **On the Reach host,** next to the Hermes Foreman. It needs about 2 vCPU and 4 GB of RAM for the headless browser, plus a persistent disk. For the one-time logins, it also needs a remote desktop, or you can start with only the no-login channels.
- **Behind a thin Reach service.** This is a small HTTP endpoint on the Reach host. It runs only allowlisted read commands on the channels you turned on, caches results and returns the JSON. Cloudflare Tunnel exposes it with an Access service token, so only your Worker can call it. Sandboxes reach it through the Worker's outbound handler. The sandbox allowlist stays tight, and every research call is logged against its ticket.
- **Respect its limits.** By design, it runs at most 2 queries at once per platform and 4 in total, with at least 10 seconds between searches on the same platform. The control plane queues research calls to match. `RATE_LIMITED` means wait, never switch accounts. `NEED_LOGIN` means park the call and ping a human in Slack.

**Its rules:**

- It's read-only. It never posts, comments, likes or sends messages, which matches the rule that agents draft and humans publish.
- Use burner accounts for logged-in channels, never your main ones. Platforms may restrict accounts used for automated access.
- Install it only from the GitHub release URL, and pin a tagged version. A different package on PyPI uses the name `agent-reach` and is not this project.
- Don't build the demo on the experimental channels.
- For internal research it's fine. For anything you sell, move each logged-in platform to its official API or licensed data before customers rely on it. Scripted access to logged-in sites can break those sites' terms, and many platforms block cloud IP ranges.

## Recommended stack

| Layer | PoC pick | Why | Swap later for |
|---|---|---|---|
| Backlog and record | GitHub Issues, a Projects board, PRs, and Actions for CI | The code already lives there, and you get a free audit trail | Linear or Jira over a webhook |
| Control plane | Cloudflare Workers + Workflows, with Supabase Postgres for ticket state | You already run both. Workflows gives durable steps, retries, cron schedules and `waitForEvent` for human approval | Cloudflare D1 for one vendor, or Temporal if you leave Cloudflare |
| Sandboxes | Cloudflare Sandboxes on Containers | Generally available since April 2026, billed on active CPU, with snapshots and per-hostname outbound rules. There's an official guide for running Claude Code on a GitHub repo in one | Daytona or Modal (Hermes-native backends, and Modal has GPUs), or Firecracker in a customer's cloud |
| Builder harness | Claude Code headless (`claude -p`) inside the sandbox | File edits, bash, tests and git are all built in | The Claude Agent SDK, Hermes Agent or others, behind the same adapter |
| LLM gateway | Cloudflare AI Gateway | The sandbox never holds real keys. Spend limits can be scoped by metadata, so each ticket gets its own budget. It also logs every call | LiteLLM if you leave Cloudflare |
| Research | Agent Reach behind the Reach service | Read access to GitHub, YouTube, the web, Reddit and X without per-platform API fees | Official APIs or licensed data, channel by channel |
| Reach host | One small VM running Hermes Agent (Foreman) and Agent Reach | A persistent disk and browser, plus an always-on Slack gateway | A second host per tenant |
| Private link | Cloudflare Tunnel + Access | The Reach host has no open inbound ports, and only the Worker can call it | — |
| Repo access | A GitHub App with short-lived, repo-scoped tokens | Least privilege, and it can't merge | — |
| Dashboard | Cloudflare Pages reading Supabase | This page is the pitch demo | — |

**The fully managed option.** Claude Managed Agents runs the agent loop and a sandbox for each session on Anthropic's side. It includes scheduled deployments, outcomes graded against a rubric, and credentials injected at egress. That means the least infrastructure to build, but it only runs Claude and is still in beta. Choose it if you'd rather not run sandboxes, and accept that you lose the "any model" story. Cloudflare also has a template that runs Managed Agents sessions in your own Cloudflare sandboxes.

## Cloud providers you need

Cloudflare covers most of the backbone. You still need a code host, model providers and one small always-on VM.

| Provider | What it does in the factory | Needed? | Rough PoC cost |
|---|---|---|---|
| **Cloudflare** | Workers + Workflows for the control plane and cron. Sandboxes for the builder containers. AI Gateway for keys, spend limits and logs. KV and R2 for caches and logs. Tunnel + Access for the private link to the Reach host. Pages for the dashboard | Required: it's the backbone | Workers Paid starts at $5 a month, plus usage. Sandboxes bill on active CPU, so time spent waiting on the model costs little |
| **GitHub** | Backlog, code, PRs, Actions CI and the GitHub App | Required | Free, or Team per user |
| **Anthropic** | Claude models for the Builder, Reviewer and Triage | Required, or another frontier model provider | Usage, and the biggest line item |
| **Nous Portal or OpenRouter** | Hermes and other open models for the Foreman, the Scout and the chore lane | Required for the Hermes lane | Usage or a subscription |
| **A small VM provider** (Hetzner, DigitalOcean, Fly.io, Lightsail or similar) | The Reach host: Hermes Foreman, Agent Reach, its browser and its sessions | Required | About $5 to $25 a month for 2 vCPU and 4 GB |
| **Supabase** | Postgres for tickets, runs and metrics, with realtime updates for the dashboard | Optional: Cloudflare D1 can replace it | Free tier, or $25 a month for Pro |
| **Slack** | Approvals and chat with the Foreman | Recommended | Free |
| **Groq or OpenAI** | Speech-to-text for YouTube and podcast transcripts in Agent Reach | Optional | Usage |
| **Daytona or Modal** | Alternative sandboxes: Hermes-native backends, and Modal has GPUs | Optional | Usage, with free credits to start |

**Why not put everything on Cloudflare?** You could, but two parts fit a plain VM better for now. Agent Reach needs a persistent, logged-in browser profile and a one-time human login. Hermes's messaging gateway is a long-running process with local memory. Both are a few commands on a VM and real work in containers.

**The fewest-vendors version** is GitHub, Cloudflare, Anthropic and one VM. Add Nous Portal or OpenRouter when you turn on the Hermes lane.

**You don't need AWS, Google Cloud or Azure for the PoC.** They come in later, when an enterprise customer wants the sandboxes in its own cloud account.

**Rough monthly total for the PoC:** about $30 to $100 for infrastructure. Model spend is extra and dominates. For example, 300 tickets at $1 to $5 each is $300 to $1,500. Treat all of these as guesses until Phase 0 gives you real numbers.

## Model routing

| Ticket class | Example | Model | Starting cap |
|---|---|---|---|
| Chore | Dependency bump, lint fix, copy change, docs | Claude Haiku 5.5 or an open Hermes model | $0.50, 15 min |
| Standard | Scoped bug or feature with existing tests | Claude Sonnet 5.5 | $3, 45 min |
| Hard | Multi-file refactor or new module | Claude Opus 5.5 at high effort | $15, 2 hours |
| Not ready | Vague, with no acceptance criteria | No model. It goes back to a human with questions | — |

The caps are starting points; tune them from real runs. AI Gateway enforces them through spend limits keyed on the ticket ID. Before you build a routing cascade, run one strong model at lower effort on the same tickets. That often wins on cost per merged PR, and a single model keeps prompt caching simple.

List prices when this was written, per million input and output tokens: Haiku 5.5 $0.10 and $0.50, Sonnet 5.5 $2 and $10, Opus 5.5 $4 and $20. Check Nous Portal or OpenRouter for current Hermes model prices. A rough guess is $1 to $5 per standard ticket on Sonnet 5.5 and about twice that on Opus 5.5. Measure real costs in Phase 0.

## Definition of Ready

An item is `agent-ready` only when it has all five of these:

1. **Goal:** one or two sentences on what changes for the user.
2. **Acceptance criteria:** a checklist a test or a reviewer can verify.
3. **Pointers:** likely files or components, similar past PRs, or the source link the Scout found.
4. **Out of scope:** what not to touch.
5. **How to verify:** the exact commands. For UI work, also the page and state to screenshot.

Ship this as a GitHub issue template. The Triage agent rewrites loose issues into this shape and asks a human to confirm.

## Guardrails

- Agents can't merge, push to `main` or change branch protection. The GitHub App's permissions enforce this.
- Only tickets a maintainer labels `agent-ready` run. Scout drafts and issues from outsiders are untrusted input and can carry prompt injection.
- Protected paths always need a human reviewer, whatever the Reviewer agent says: auth, billing, infra, database migrations and CI config.
- Every ticket has a token budget, a time limit and a cap of 2 fix rounds. If it hits any of them, the ticket parks as `blocked` with a summary.
- A daily spend cap and a kill switch can stop all dispatching.
- Sandboxes get no production credentials. Outbound traffic goes only to AI Gateway, the git host, package registries and the Reach service, and the Worker enforces that per hostname.
- Agent Reach stays read-only, on burner accounts, within its rate limits, and pinned to a tagged release from GitHub.
- Every PR states its cost, time and model, what the agent ran to check its work, and any outside sources it read.

## What to measure

| Number | What it tells you | Starting target |
|---|---|---|
| Autonomy rate | Share of `agent-ready` tickets merged with at most light human edits | Over 50% |
| Cost per merged PR | Model and sandbox spend divided by merges | Under $5 for standard tickets |
| Lead time | Time from `ready` to PR open, and to merge | PR open within 1 hour |
| Human minutes per PR | Review time, which is the real limit | Under 10 |
| First-pass CI green | How good the Builder is before the Fixer steps in | Over 70% |
| Escapes | Reverts or bugs traced to agent PRs within 14 days | Close to zero |
| Scout yield | Share of Scout drafts a human accepts into the backlog | Over 30% |
| Throughput | Merged PRs per week compared with your baseline before the factory | A clear multiple |

The targets are rough guesses. Replace them with your Phase 0 baseline.

## Build plan

### Phase 0: prove the loop by hand (days 1 to 3)

1. Pick one real repo you own that has tests and a backlog. The site repo is a candidate.
2. Write the playbook in `AGENTS.md` or `CLAUDE.md`. Cover how to build, test and lint, the coding rules and the protected paths.
3. Write 20 issues in the Definition of Ready format, mixing chores, standard tickets and hard ones.
4. Install Agent Reach on your own machine with the default channels. Have an agent use it to draft five issues from your dependencies' GitHub issues and recent discussion of your product. That's the Scout, done by hand.
5. Run each issue without building any infrastructure. Use a Claude Code cloud session per issue, the Claude Code GitHub Action, or Hermes Agent on a VPS.
6. Record for each ticket whether it merged, what it cost, how many minutes it took and how much a human had to edit. That record is your baseline and your first pitch slide.

**Exit test:** at least 10 of the 20 merge with light edits. If they don't, fix the specs and the playbook before you build anything.

### Phase 1: the minimum factory on Cloudflare (weeks 1 to 2)

1. Start from Cloudflare's "Build a coding agent runner" guide. It covers a Worker that starts a sandbox, runs Claude Code on a GitHub repo, sends model calls through AI Gateway without the token entering the sandbox, and lets the sandbox reach only the gateway and `github.com`.
2. Set up a GitHub App with scoped permissions, a webhook on the `agent-ready` label and a Workflows cron schedule every 10 minutes.
3. Add the ticket table in Supabase. Build the state machine as a Workflow, using `waitForEvent` for the human approval.
4. Bake each repo's sandbox image with its dependencies and the pinned harness version, because the locked-down sandbox can't download packages at run time. Use snapshots so a ticket starts from a warm workspace.
5. Write the worker adapter. It's one entrypoint that takes a ticket, runs the harness headless and returns a PR URL and a usage report. Build it for Claude Code first.
6. Turn on AI Gateway spend limits keyed on the ticket ID, plus a daily cap.
7. Run the Reviewer agent as a GitHub Action on every agent PR, and send a Slack notification with Approve and Request changes buttons.
8. Allow 3 to 5 sandboxes to run at once.

**Exit test:** you label 10 tickets at night and find reviewed PRs with green CI in the morning.

### Phase 2: research, the Foreman and more models (weeks 3 to 4)

1. Stand up the Reach host: a small VM with Hermes Agent and Agent Reach on a pinned release, and burner accounts for Reddit and the other channels you choose.
2. Add the Reach service and connect it through Cloudflare Tunnel + Access. Route sandbox research calls through the Worker.
3. Turn on the Scout nightly, and give the Planner and Triage agents the research tool.
4. Add the Triage agent, the issue template and the Fixer loop.
5. Set up Hermes Agent as the Foreman in Slack: status, start and stop, morning digest.
6. Add a second Builder lane on Hermes Agent for chores, with routing by ticket class.
7. Add the learning loop. After each blocked or rejected ticket, the Foreman proposes a playbook or skill change in its own PR.
8. Build the dashboard with the metrics above, and raise the limit to 10 to 20 sandboxes at once.

### Phase 3: ready to pitch (week 5)

1. Run the factory on your real backlog for at least two weeks and keep the numbers.
2. Add a second repo in a different stack to show the approach generalizes.
3. Write a one-page security model covering isolation, secrets, permissions, outside content and the audit trail.
4. Record the demo below as a backup video.

## Scaling past the PoC

| Pressure | What to do |
|---|---|
| More tickets | Allow more sandboxes at once. Cloudflare Containers now allow thousands at once. Watch review minutes more than compute. |
| Slow starts | Use snapshots and nightly image rebuilds with dependency caches. |
| Cost | Put the stable system prompt and playbook first so prompt caching works. Send non-urgent triage and Scout work through the Batch API at half price. Keep PRs small and run chores on cheap models. |
| Reliability | Workflows already gives durable steps. Make every step idempotent so you can replay from any state. |
| Research volume | Agent Reach is rate-limited by design and depends on logged-in accounts. Cache results, keep it for low-volume research, and move high-volume channels to official APIs or licensed data. |
| Enterprise buyers | Offer bring-your-own-cloud: the same control plane, with sandboxes in the customer's AWS, Google Cloud or Azure account. Run open Hermes models on their hardware where code can't leave. |
| Many repos and teams | Isolate each tenant, give each repo its own playbook and budget, and add SSO and audit log export. |
| Quality at volume | Keep a set of golden tickets from past work. Every change to prompts, models or the harness replays them before it ships. This is the same idea as `docs/agentic-evals.md`. |

## The pitch demo (5 minutes)

1. Show the backlog of 20 real issues.
2. Show what the Scout found overnight: a breaking change reported on a dependency's GitHub and a user complaint on Reddit, each drafted as an issue with its source link.
3. The Triage agent rewrites three loose issues into the ready format and asks a question on one.
4. Label ten issues `agent-ready`. The dashboard lanes fill and ten sandboxes start.
5. Open a finished PR. It shows the plan, the diff, tests, a screenshot, the reviewer's notes, and a line like "$2.14, 23 minutes".
6. Approve it from Slack, and it merges. If it's one of the Scout's issues, that's the whole loop from signal to shipped fix.
7. Close on the two-week numbers: autonomy rate, cost per merged PR, human minutes per PR, and throughput against the baseline.

## The market

Several cloud coding agents already work from issues: Devin, GitHub Copilot's coding agent, OpenAI Codex, Claude Code on the web, Factory, Cursor's background agents and the open-source OpenHands. Agents that write PRs won't carry a pitch on their own, so pick one wedge and show it in the demo:

- **From signal to shipped.** The factory finds its own work, such as user complaints and dependency breakages, and turns it into reviewed PRs. Agent Reach makes this possible.
- **Any model, your cloud.** The factory works with any model and runs in the customer's own cloud, with open Hermes models for teams that can't send code to a vendor.
- **A factory that learns your codebase.** The playbook and skills improve with every blocked ticket, and you measure that week over week.
- **A quality gate you can trust.** Golden-ticket evals and a human gate are core features, which fits the Agents & Humans story.
- **A vertical.** Pick one stack or industry where you know the backlog better than a general tool does.

## Decisions needed

1. Which repo goes first?
2. Which wedge does the pitch lead with? It changes what Phase 2 builds first.
3. Should the sandboxes run on Cloudflare (one vendor) or on Daytona or Modal (native Hermes backends)? I recommend Cloudflare.
4. Which Agent Reach channels do you turn on, and whose burner accounts do the logged-in ones use?
5. Managed or self-hosted for the PoC? Claude Managed Agents is the least infrastructure but runs only Claude. The stack above is more work but runs any model.
6. What's the monthly budget for model and sandbox spend during the PoC?

## Suggested repo layout

```
factory/
  control-plane/   Worker + Workflows: webhook, cron, state machine, routing, sandbox outbound rules
  adapters/
    claude-code/   runs the Builder headless in the sandbox, returns PR + usage
    hermes/        same contract, for Hermes Agent
  sandbox/         container image for each target repo, with dependencies and the harness baked in
  reach/           Reach service: allowlisted agent-reach commands, cache, Tunnel config
  foreman/         Hermes Agent config, skills and Slack gateway for the Reach host
  skills/          playbook and role prompts in the Agent Skills format
  gateway/         AI Gateway config: providers, spend limits, ticket metadata
  dashboard/       Pages site that reads the ticket table
```

## Sources

- [Hermes Agent](https://github.com/NousResearch/hermes-agent)
- [Agent Reach](https://github.com/Panniantong/Agent-Reach)
- [Cloudflare: run coding agents in a sandbox](https://developers.cloudflare.com/sandbox/coding-agents/)
- [Cloudflare: build a coding agent runner](https://developers.cloudflare.com/sandbox/get-started/build-a-coding-agent-runner/)
- [Cloudflare: Containers and Sandboxes are generally available](https://developers.cloudflare.com/changelog/post/2026-04-13-containers-sandbox-ga/)
- [Cloudflare: AI Gateway spend limits](https://developers.cloudflare.com/ai-gateway/features/spend-limits/)
- [Cloudflare: Workflows](https://developers.cloudflare.com/workflows/)
