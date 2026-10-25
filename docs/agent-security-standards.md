# Security standards for agent work — adopting agent tools and running autonomous agents

*These standards cover two kinds of work. The first is bringing in third-party agent tools: skills, plugins, hooks, MCP servers, agent CLIs and harness packs, many of them found through social posts and trending lists. The second is running agents that write code, read the web or act on your accounts without someone watching each step. Each rule can be checked. A **MUST** rule blocks the install, the run or the merge. A **SHOULD** rule needs a written reason to skip. Companion to `docs/agentic-software-factory.md`.*

## Why these rules exist

Three real incidents show the failure modes:

| Incident | What happened | Rules that stop it |
|---|---|---|
| **Nx "s1ngularity", August 2025** | Attackers stole an npm publishing token through a misconfigured GitHub Action and published malicious versions of a popular build tool. The malware used AI coding CLIs already installed on developers' machines to hunt for secrets. Over 1,700 users had secrets leaked, and stolen GitHub tokens were then used to make private repositories public. | T2, T3, S1, S4, R3 |
| **postmark-mcp, September 2025** | A lookalike MCP server on npm worked normally for several releases. Then version 1.0.16 quietly BCC'd every email it sent to an outside address. It was the first malicious MCP server found in the wild. | T1, T2, T5 |
| **GitLost, disclosed July 2026** | A crafted public GitHub issue led an AI agent with read access to other repositories in the organization to post private repository content in a public comment. The researchers say the flaw can't be fully fixed in code. | I1, I3, P1, O2 |

None of these needed a clever exploit. Each turned a trusted tool, a broad token or untrusted text into access.

## T — Taking in a new tool

These rules apply to skills, plugins, hooks, MCP servers, agent CLIs, harness packs, and GitHub Apps that touch code.

- **T1 MUST: Install only from the source the maintainer names.** That means the repository URL and the package name. Check that the publisher account matches the repository. Lookalikes are common. Agent Reach warns that a different PyPI package uses its name, and ECC warns that re-uploads of its repo may contain malware.
- **T2 MUST: Pin an exact version or commit SHA.**
  - No `latest`, no `@main`, no auto-update.
  - A new version waits at least 7 days before you adopt it, unless it fixes a vulnerability you are exposed to.
  - Enforce the wait where the tool supports it: pnpm's `minimumReleaseAge` (pnpm 10.16 or later), uv's `exclude-newer`, npm's `--before`. Otherwise enforce it by hand.
- **T3 MUST: Read what it executes before it runs.**
  - What to read: install scripts (`preinstall`, `postinstall`), hooks, servers and daemons, and any code that makes network calls or reads environment variables, `~/.ssh`, `~/.config` or browser profiles.
  - Install with `--ignore-scripts` unless a script is required and you've reviewed it.
- **T4 MUST: Prefer text over runtime.** When a tool's value is instructions (skills, checklists, rules, prompts), copy the reviewed text into your repository and own it from then on. Install runtime pieces such as hooks, MCP servers and background processes only when you need their behaviour, and add them one at a time.
- **T5 MUST: Review the diff of every upgrade,** not only the changelog. The postmark-mcp backdoor shipped as an ordinary patch release.
- **T6 SHOULD: Check who maintains it.** Look at:
  - the number of maintainers and whether two-factor authentication is on
  - npm provenance attestations
  - package age and release cadence
  - open security issues

  Stars, view counts and "trending" badges are not evidence of safety. Review a package with a single maintainer twice as carefully.
- **T7 MUST: Trial it in a throwaway sandbox first,** with no secrets, no logged-in sessions, and network access only to what it needs. Watch which hosts it calls. Only then move it into a runner.
- **T8 MUST: Keep a tool register,** with one row per tool, using the intake record below. A tool that isn't in the register doesn't run.
- **T9 MUST: Respect the license.** If you copy text, keep its license notice. If a repository rule forbids naming the source, write your own version from your own rules instead of copying.
- **T10 SHOULD: Check what a security scanner actually covers** before you rely on it. A scanner built for one harness can pass a configuration it never read.

## S — Secrets and credentials

- **S1 MUST: No long-lived production secrets where an agent runs commands.** Agents get short-lived, scoped tokens. Where possible, model keys are injected at a gateway or proxy (for example AI Gateway with stored provider keys), so the sandbox holds only a revocable, spend-limited gateway token.
- **S2 MUST: Give each agent model key a hard spend limit and one runner.** A leak is then contained and you can tell which runner it came from.
- **S3 MUST: Give agents GitHub access through a machine user with fine-grained tokens.**
  - One repository, the fewest permissions, a 90-day expiry, no admin.
  - The machine user is never on a branch-protection bypass list.
  - Never connect an agent to your personal account if that account can bypass branch protection. That includes hosted agents and routines that act through "your GitHub connection".
- **S4 MUST: Assume any command the agent runs can read everything in its environment:** environment variables, `/proc`, dotfiles, mounted volumes. Decide what may live in that environment on that basis.
- **S5 MUST: Keep secrets out of prompts, issues, PR bodies, logs, screenshots and skill files.** Scan every diff for secrets in CI, with gitleaks or an equivalent, and before pushing.
- **S6 SHOULD: Rotate agent credentials every 90 days,** and at once after any suspected prompt injection or unexplained agent behaviour.

## R — Running agents

- **R1 MUST: One task, one isolated sandbox.** Destroy or reset it afterwards. Tasks don't share a home directory, except for deliberate memory you've reviewed.
- **R2 MUST: Allowlist outbound network traffic.** Allow only the model gateway, the git host, package registries and named services. Open no inbound ports; reach private services through a tunnel with a service token.
- **R3 MUST: Never turn off an agent's permission checks on a machine that holds secrets or your logged-in browser sessions.** That covers `--dangerously-skip-permissions`, `--yolo` and their equivalents. In a disposable sandbox with scoped tokens it's acceptable. The Nx malware abused AI CLIs on exactly those machines.
- **R4 MUST: Agents can't merge, deploy, change CI workflows, change branch protection or touch production data.** Permissions enforce this: the machine user, rulesets and token scopes. Deny-lists in prompts or agent config are a second guard, not the boundary.
- **R5 MUST: Set hard limits per run** on time, spend and fix rounds. Also keep a daily spend cap for everything, and a kill switch that stops new runs within minutes.
- **R6 SHOULD: Test against a separate preview environment and database** whenever a test writes data. Never use production for this.

## I — Untrusted input (prompt injection)

- **I1 MUST: Treat untrusted text as data, never as instructions.** That includes:
  - issue and PR text from anyone without write access
  - comments
  - web pages, transcripts and social posts
  - the files of a PR under review
  - tool output
  - skill text you haven't reviewed

  Only maintainers can mark work as ready for an agent.
- **I2 MUST: Pin the task text when work starts** by storing a hash of it, and stop if the text changes.
- **I3 MUST: Never give one agent all three risky abilities at once:** access to private data, exposure to untrusted content, and a way to send data out. Simon Willison calls this the "lethal trifecta". Split the work: the agent that reads untrusted content drafts, and a separate step with different credentials acts.
- **I4 MUST: Rules that govern a review come from the protected branch,** never from the change under review.
- **I5 SHOULD: Keep web and social access read-only.** Logged-in scraping uses burner accounts, never your main ones. Anything customer-facing moves to official APIs or licensed data.

## P — Permissions for hosted services

- **P1 MUST: Give an agent or app the narrowest repository scope.** A single repository, not the whole organization. GitLost depended on an agent that could read other repositories.
- **P2 MUST: Review data handling before a hosted reviewer, GitHub App or hosted agent gets a private repository.** Read its retention, training use and sub-processors, then record it in the register.
- **P3 SHOULD: Know where each model provider sends your prompts.** Aggregators route to many backends. Use zero- or limited-retention options for private code where they're offered.

## O — Output and oversight

- **O1 MUST: A human approves before anything ships:** a merge, deploy, publish, email, post or spend.
- **O2 MUST: Check outward output for leaked content.** When an agent with private access writes something that leaves the system (a public comment, post or email), check it first.
- **O3 MUST: Log every run** and keep the logs for at least 30 days. Record:
  - who or what started it
  - the task and the runner
  - the model and the tools used
  - the files touched
  - the cost and the outcome
- **O4 SHOULD: Alert on anomalies:**
  - spend spikes
  - runs that touch protected paths
  - new outbound hosts
  - a token used from somewhere new

## If something goes wrong

Use this when an agent misbehaves or a tool you use is reported compromised:

1. **Stop new runs** with the kill switch.
2. **Revoke and rotate** every model key, GitHub token and cloud token the affected runners could read.
3. **Check what was touched.** Read the run log and git history. On GitHub, look for:
   - new public repositories
   - new deploy keys or tokens
   - changes to workflows or branch protection
4. **Pin back** to the last reviewed version, or remove the tool.
5. **Write it up.** Record what happened and which rule would have stopped it. If no rule would have, add one.

## Intake record

Fill one in for each tool before it runs anywhere with access to your code or accounts.

```
Tool:
Found via:          link (a social post is a lead, not evidence)
Official source:    repository URL, package name, publisher account
Pinned version:     exact version or commit SHA
License:
What it executes:   install scripts, hooks, servers, background processes
Network calls:      hosts, and why
Credentials it sees: environment variables, tokens, files it can read
Runs where:         sandbox, runner, laptop
Maintainers:        count, two-factor and provenance, package age
Decision:           adopt as text / adopt runtime / trial only / reject, and why
Owner, review date:
```

## The tools in this plan, under these rules

| Tool | Verdict |
|---|---|
| **Hermes Agent** | Runtime. Pin the image by digest, keep its deny rules as a second guard, give it a spend-limited key on one runner, and allowlist its outbound traffic (R2). |
| **Claude Code and the Agent SDK** | Runtime. Keep permission checks on outside disposable sandboxes (R3). Hosted routines must act as the machine user, not as an account that can bypass branch protection (S3). |
| **Agent Reach** | Runtime with a logged-in browser. Install only from its GitHub release, never the lookalike PyPI package (T1). Pin a tagged release, keep it read-only on burner accounts, and run it on the Reach host only, never in builder sandboxes (I5). |
| **ECC** | Adopt as text only (T4): write or copy the checklists you want, pinned to a reviewed commit. Keep its hooks out of unattended runners, and note it has one maintainer (T6). |
| **AgentShield** | Check its coverage first (T10). It reads Claude Code configuration, not a Hermes setup. |

## Checks you can automate

| Check | Where |
|---|---|
| Secret scan on every PR (gitleaks or equivalent) | CI |
| Frozen lockfile installs, with no `latest` or branch references in agent configs | CI |
| Container images pinned by digest | CI or a test |
| Changes to workflows, rulesets and deploy config need the owner's review | Rulesets or CODEOWNERS |
| Token expiry dates, spend against caps, and the tool register | Monthly review |
| A dependency cooldown of at least 7 days | Package manager setting or update-bot config |

## Sources

- [Wiz: s1ngularity's aftermath](https://www.wiz.io/blog/s1ngularitys-aftermath)
- [StepSecurity: Nx compromised with data-stealing malware](https://www.stepsecurity.io/blog/supply-chain-security-alert-popular-nx-build-system-package-compromised-with-data-stealing-malware)
- [Snyk: malicious MCP server on npm, postmark-mcp](https://snyk.io/blog/malicious-mcp-server-on-npm-postmark-mcp-harvests-emails/)
- [CSO Online: GitHub AI agent leaks private repositories via prompt injection](https://www.csoonline.com/article/4194448/github-ai-agent-leaks-private-repositories-via-prompt-injection.html)
- [CSA research note: when a GitHub issue steals CI secrets](https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-coding-agent-ci-prompt-injection-202608/)
