# An agentic software factory — proof-of-concept outline

*Agents in cloud sandboxes work the backlog around the clock, and humans approve what ships. This outline covers a working proof of concept you can pitch and then scale, with Hermes Agent, Claude Code and other models behind one control plane.*

## The recommendation in one line

Build the control plane yourself and rent everything else. The control plane is the loop that turns a backlog item into a reviewed, tested pull request: intake, dispatch, verify, human gate and metrics. That loop is your product and your pitch. The agent harnesses (Claude Code, Hermes Agent) and the cloud sandboxes (Daytona, Modal, E2B) plug in behind a small adapter, so you can swap models and vendors without a rewrite.

## Five design rules

1. **Code runs the loop, and agents make the judgment calls.** The states, retries, budgets and merge rights are ordinary code. Agents handle only triage, planning, coding and review. A system that runs 24/7 can't rely on an LLM remembering to check the queue.
2. **Each ticket gets its own sandbox and its own pull request.** Every item gets a fresh, isolated VM made from a prebuilt snapshot of the repo. Only git commits and the playbook carry over between tickets.
3. **Agents never merge.** They open pull requests, CI and a reviewer agent check them, and a human merges. Branch protection enforces this, so it doesn't depend on a prompt.
4. **The ticket spec matters more than the model.** Write a Definition of Ready and have a triage agent enforce it before you pay for a bigger model.
5. **Human review time is the real limit.** You can run 50 sandboxes at once, but if each PR takes 20 minutes to review, the reviewer sets the pace. Put as much work into the PR the reviewer reads as into the code the agent writes.

## Architecture

```
  Backlog (GitHub Issues + Projects board)
      │  webhook on the "agent-ready" label, plus a cron sweep every 10 minutes
      ▼
  Control plane (your code: state machine, queue, budgets, routing)
      │  dispatch: one ticket → one sandbox
      ▼
  Sandbox pool (Daytona or Modal microVMs, started from a repo snapshot)
      │  harness inside: Claude Code headless, Hermes Agent, or another
      │  output: branch + pull request with plan, tests, evidence and cost
      ▼
  Verifier (CI + a reviewer agent on a different model + up to 2 fix rounds)
      │
      ▼
  Human gate (GitHub review, or one-tap approve in Slack) → merge

  Alongside:
    Foreman (Hermes Agent in Slack or Telegram): status, triage, "run #42", morning digest
    LLM proxy: holds the API keys, tags every call with its ticket, enforces budgets
    Metrics store + dashboard: cost per PR, autonomy rate, cycle time, review minutes
```

### Ticket lifecycle

`new → triaged → ready → running → pr_open → fixing → in_review → merged`

A ticket can also leave the loop three ways:

- `needs_info` sends it back to a human with questions.
- `blocked` means its budget or fix rounds ran out.
- `rejected` means a human closed the PR.

Every state change is a database row, and the dashboard and the pitch numbers come from those rows.

## The team of agents

| # | Agent | What it does | Runs on | When |
|---|---|---|---|---|
| 1 | **Triage** | Reads each new issue and checks it against the Definition of Ready. Asks clarifying questions in the issue, splits big items, then sizes and labels the rest. | A cheap model: Claude Haiku 5.5 or an open Hermes model | On every new issue, plus a nightly sweep |
| 2 | **Planner** | Reads the code and writes a short plan and test plan into the issue before any code is written. | Same model as the Builder | When a ticket is picked up |
| 3 | **Builder** | Writes the code and tests in the sandbox, runs the test suite and opens the PR. | Claude Code headless with Claude Sonnet 5.5 or Opus 5.5, or Hermes Agent for chores | Once per ticket |
| 4 | **Reviewer** | Checks the diff against the acceptance criteria and the repo's rules, and flags risky files. Uses a different model from the Builder so they don't share blind spots. | A different model family or tier | Once per PR |
| 5 | **Fixer** | Reads CI failures and review comments and pushes fixes. After 2 rounds it hands the ticket back to a human. | The Builder's model | On red CI or review comments |
| 6 | **Foreman** | The always-on front desk. Answers "what's in the queue", starts and stops tickets on request and posts a morning digest. Turns lessons from failed tickets into playbook changes. | Hermes Agent: messaging gateway, cron, memory, skills | 24/7 |

In the proof of concept, the Planner and Builder can share one session. Split them later if plans need a human's approval before coding starts.

## Where Hermes fits

[Hermes Agent](https://github.com/NousResearch/hermes-agent) (Nous Research, MIT license) suits the always-on parts of the factory:

- It runs on a $5 VPS or on serverless infrastructure. One gateway process connects it to Slack, Telegram, Discord, WhatsApp and Signal.
- It has a built-in cron scheduler, isolated subagents and persistent memory. After complex tasks it writes skill files it can reuse.
- It has six built-in terminal backends: local, Docker, SSH, Modal, Daytona and Vercel Sandbox. Daytona and Modal hibernate when idle, so the factory can stay available 24/7 without billing 24/7.
- It works with any model: Nous Portal, OpenRouter, OpenAI, Anthropic or your own endpoint.

For the Builder, use whichever harness merges the most PRs on your repo, and measure that in Phase 0. I expect a frontier coding model in a coding harness to win today: Claude Code headless, or the Claude Agent SDK if you want programmatic control. Keep Hermes as a second Builder lane for chores. It also serves customers who need open models. Because of the adapter, switching lanes is a config change.

Write the repo playbook and skills once, in the Agent Skills format ([agentskills.io](https://agentskills.io)). Hermes and Claude Code both read that format, so the playbook doesn't lock you into either harness.

## Recommended stack

| Layer | PoC pick | Why | Swap later for |
|---|---|---|---|
| Backlog and record | GitHub Issues, a Projects board, PRs, and Actions for CI | The code already lives there, and you get a free audit trail | Linear or Jira over a webhook |
| Control plane | A Cloudflare Worker (webhook + cron trigger) with Supabase Postgres for ticket state | You already run both, including the link-check Worker in this repo. The heavy work happens in sandboxes, so the control plane stays light | A durable workflow engine such as Temporal or Inngest, once retries and long waits get complex |
| Sandboxes | Daytona or Modal | Fast starts from snapshots, hibernation when idle, and both are built-in Hermes backends | E2B, or self-hosted Firecracker for customers who bring their own cloud |
| Builder harness | Claude Code headless (`claude -p`) inside the sandbox | File edits, bash, tests and git are all built in | The Claude Agent SDK, Hermes Agent or others, behind the same adapter |
| Foreman | Hermes Agent on a small VPS with the Slack gateway | Always-on chat, cron and memory | — |
| LLM proxy | LiteLLM or Cloudflare AI Gateway | The sandbox never holds real keys, every call is tagged with its ticket, and a ticket is cut off at its budget | Per-tenant gateways |
| Repo access | A GitHub App with short-lived, repo-scoped tokens | Least privilege, and it can't merge | — |
| Dashboard | One static page that reads Supabase | This page is the pitch demo | — |

**The fully managed option.** Claude Managed Agents runs the agent loop and a sandbox for each session on Anthropic's side. It includes scheduled deployments, outcomes graded against a rubric, and credentials injected at egress. That means the least infrastructure to build, but it only runs Claude and is still in beta. Choose it if you'd rather not run sandboxes, and accept that you lose the "any model" story.

## Model routing

| Ticket class | Example | Model | Starting cap |
|---|---|---|---|
| Chore | Dependency bump, lint fix, copy change, docs | Claude Haiku 5.5 or an open Hermes model | $0.50, 15 min |
| Standard | Scoped bug or feature with existing tests | Claude Sonnet 5.5 | $3, 45 min |
| Hard | Multi-file refactor or new module | Claude Opus 5.5 at high effort | $15, 2 hours |
| Not ready | Vague, with no acceptance criteria | No model. It goes back to a human with questions | — |

The caps are starting points; tune them from real runs. Before you build a routing cascade, run one strong model at lower effort on the same tickets. That often wins on cost per merged PR, and a single model keeps prompt caching simple.

List prices when this was written, per million input and output tokens: Haiku 5.5 $0.10 and $0.50, Sonnet 5.5 $2 and $10, Opus 5.5 $4 and $20. Check Nous Portal or OpenRouter for current Hermes model prices. A rough guess is $1 to $5 per standard ticket on Sonnet 5.5 and about twice that on Opus 5.5. Sandbox time is usually cents per ticket. Measure real costs in Phase 0.

## Definition of Ready

An item is `agent-ready` only when it has all five of these:

1. **Goal:** one or two sentences on what changes for the user.
2. **Acceptance criteria:** a checklist a test or a reviewer can verify.
3. **Pointers:** likely files or components, or similar past PRs.
4. **Out of scope:** what not to touch.
5. **How to verify:** the exact commands. For UI work, also the page and state to screenshot.

Ship this as a GitHub issue template. The Triage agent rewrites loose issues into this shape and asks a human to confirm.

## Guardrails

- Agents can't merge, push to `main` or change branch protection. The GitHub App's permissions enforce this.
- Only tickets a maintainer labels `agent-ready` run. Issue text from outsiders is untrusted input and can carry prompt injection.
- Protected paths always need a human reviewer, whatever the Reviewer agent says: auth, billing, infra, database migrations and CI config.
- Every ticket has a token budget, a time limit and a cap of 2 fix rounds. If it hits any of them, the ticket parks as `blocked` with a summary.
- A daily spend cap and a kill switch can stop all dispatching.
- Sandboxes get no production credentials. They can reach only an allowlist of hosts: the git host, package registries and the LLM proxy.
- Every PR states its cost, time and model, and what the agent ran to check its work.

## What to measure

| Number | What it tells you | Starting target |
|---|---|---|
| Autonomy rate | Share of `agent-ready` tickets merged with at most light human edits | Over 50% |
| Cost per merged PR | Model and sandbox spend divided by merges | Under $5 for standard tickets |
| Lead time | Time from `ready` to PR open, and to merge | PR open within 1 hour |
| Human minutes per PR | Review time, which is the real limit | Under 10 |
| First-pass CI green | How good the Builder is before the Fixer steps in | Over 70% |
| Escapes | Reverts or bugs traced to agent PRs within 14 days | Close to zero |
| Throughput | Merged PRs per week compared with your baseline before the factory | A clear multiple |

The targets are rough guesses. Replace them with your Phase 0 baseline.

## Build plan

### Phase 0: prove the loop by hand (days 1 to 3)

1. Pick one real repo you own that has tests and a backlog. The site repo is a candidate.
2. Write the playbook in `AGENTS.md` or `CLAUDE.md`. Cover how to build, test and lint, the coding rules and the protected paths.
3. Write 20 issues in the Definition of Ready format, mixing chores, standard tickets and hard ones.
4. Run each issue without building any infrastructure. Use a Claude Code cloud session per issue, the Claude Code GitHub Action, or Hermes Agent on a VPS with the Daytona backend.
5. Record for each ticket whether it merged, what it cost, how many minutes it took and how much a human had to edit. That record is your baseline and your first pitch slide.

**Exit test:** at least 10 of the 20 merge with light edits. If they don't, fix the specs and the playbook before you build anything.

### Phase 1: the minimum factory (weeks 1 to 2)

1. Set up a GitHub App with scoped permissions, a webhook on the `agent-ready` label and a cron sweep every 10 minutes.
2. Add the ticket table in Supabase and build the state machine in the Worker.
3. Build the sandbox snapshot: a Dockerfile per repo with dependencies installed and the repo cloned. Rebuild it nightly so a ticket starts in seconds.
4. Write the worker adapter. It's one entrypoint script that takes a ticket, runs the harness headless and returns a PR URL and a usage report. Build it for Claude Code first.
5. Put the LLM proxy in front of every model call.
6. Run the Reviewer agent as a GitHub Action on every agent PR, and send a Slack notification with Approve and Request changes buttons.
7. Allow 3 to 5 sandboxes to run at once.

**Exit test:** you label 10 tickets at night and find reviewed PRs with green CI in the morning.

### Phase 2: make it smarter and multi-model (weeks 3 to 4)

1. Add the Triage agent and the issue template.
2. Add the Fixer loop for red CI and review comments.
3. Set up Hermes Agent as the Foreman in Slack: status, start and stop, morning digest.
4. Add a second Builder lane on Hermes Agent for chores, with routing by ticket class.
5. Add the learning loop. After each blocked or rejected ticket, the Foreman proposes a playbook or skill change in its own PR.
6. Build the dashboard with the metrics above, and raise the limit to 10 to 20 sandboxes at once.

### Phase 3: ready to pitch (week 5)

1. Run the factory on your real backlog for at least two weeks and keep the numbers.
2. Add a second repo in a different stack to show the approach generalizes.
3. Write a one-page security model covering isolation, secrets, permissions and the audit trail.
4. Record the demo below as a backup video.

## Scaling past the PoC

| Pressure | What to do |
|---|---|
| More tickets | Allow more sandboxes at once, since sandbox providers scale out. Watch review minutes more than compute. |
| Slow starts | Keep warm pools, and rebuild snapshots nightly with dependency caches. |
| Cost | Put the stable system prompt and playbook first so prompt caching works. Send non-urgent triage through the Batch API at half price. Keep PRs small and run chores on cheap models. |
| Reliability | Move the state machine to a durable workflow engine. Make every step idempotent so you can replay from any state. |
| Enterprise buyers | Offer bring-your-own-cloud: the same control plane, with sandboxes in the customer's account. Run open Hermes models on their hardware where code can't leave. |
| Many repos and teams | Isolate each tenant, give each repo its own playbook and budget, and add SSO and audit log export. |
| Quality at volume | Keep a set of golden tickets from past work. Every change to prompts, models or the harness replays them before it ships. This is the same idea as `docs/agentic-evals.md`. |

## The pitch demo (5 minutes)

1. Show the backlog of 20 real issues.
2. The Triage agent rewrites three loose issues into the ready format and asks a question on one.
3. Label ten issues `agent-ready`. The dashboard lanes fill and ten sandboxes start.
4. Open a finished PR. It shows the plan, the diff, tests, a screenshot, the reviewer's notes, and a line like "$2.14, 23 minutes".
5. Approve it from Slack, and it merges.
6. Close on the two-week numbers: autonomy rate, cost per merged PR, human minutes per PR, and throughput against the baseline.

## The market

Several cloud coding agents already work from issues: Devin, GitHub Copilot's coding agent, OpenAI Codex, Claude Code on the web, Factory, Cursor's background agents and the open-source OpenHands. Agents that write PRs won't carry a pitch on their own, so pick one wedge and show it in the demo:

- **Any model, your cloud.** The factory works with any model and runs in the customer's own cloud, with open Hermes models for teams that can't send code to a vendor.
- **A factory that learns your codebase.** The playbook and skills improve with every blocked ticket, and you measure that week over week.
- **A quality gate you can trust.** Golden-ticket evals and a human gate are core features, which fits the Agents & Humans story.
- **A vertical.** Pick one stack or industry where you know the backlog better than a general tool does.

## Decisions needed

1. Which repo goes first?
2. Which wedge does the pitch lead with? It changes what Phase 2 builds first.
3. Managed or self-hosted for the PoC? Claude Managed Agents is the least infrastructure but runs only Claude. The stack above is more work but runs any model.
4. What's the monthly budget for model and sandbox spend during the PoC?

## Suggested repo layout

```
factory/
  control-plane/   Worker: webhook, cron sweep, state machine, routing
  adapters/
    claude-code/   runs the Builder headless in the sandbox, returns PR + usage
    hermes/        same contract, for Hermes Agent
  sandbox/         snapshot Dockerfile for each target repo
  skills/          playbook and role prompts in the Agent Skills format
  proxy/           LLM gateway config: keys, ticket tags, budgets
  dashboard/       static page that reads the ticket table
```
