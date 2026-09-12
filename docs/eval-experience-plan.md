# Bench — an eval experience for agentic design workflows

*A Chromatic-style review gate for agents, staffed by agents and humans. Part of agentsandhumans.ai.*

---

## 1. Why this exists

Chromatic solved a specific problem for UI teams: every commit renders every story, the render is
diffed against an approved baseline, a reviewer accepts or denies each change, and the pull request
cannot merge until the review is complete. The review is the gate, the baseline is the contract, and
the diff makes the change legible to someone who did not write the code.

Agentic experiences in enterprise design workflows have the same shape of problem and none of the
tooling. A design-ops agent that migrates tokens, audits accessibility, localises a screen, or turns a
Figma frame into a component produces output that is:

- **non-deterministic** — the same task on the same input can produce a different trajectory;
- **multi-modal** — a transcript, a set of tool calls, and one or more rendered artifacts (a frame, a
  component, a doc, a PR);
- **consequential** — the agent can write to a source of truth (a Figma library, a repo, a CMS);
- **opaque to the reviewer** — nobody reads a 40-step trajectory unless something is highlighted.

Bench treats an agent run like a story snapshot. A **scenario** is rendered under every relevant
**condition**, the resulting **run** is captured, compared against an approved **baseline**, and the
**drift** is reviewed by a **bench** of evaluators — some of them agents, some of them humans — until
a **verdict** is reached. The verdict gates whether the agent (or the prompt, or the model, or the
tool policy) ships.

### What "like Chromatic" means, concretely

| Chromatic | Bench | Notes |
|---|---|---|
| Story | Scenario | A scripted task the agent performs against a fixture (a Figma file, a repo, a design-system version). |
| Mode (viewport, theme, locale) | Condition | The variant axes: model, prompt version, tool policy, fixture, persona, locale, permission tier, fault injection, memory state, seed. |
| Snapshot | Run | The captured trajectory + artifacts + telemetry for one scenario × condition. |
| Baseline | Baseline | The last accepted run for that scenario × condition. |
| Visual diff | Drift | A structured diff of the trajectory (tool calls, arguments, ordering), the artifacts (rendered output, pixel and semantic), and the telemetry (tokens, latency, cost). |
| Accept / Deny | Verdict | Accept, Deny, or Discuss, plus a reason. Cast by humans and by agent evaluators. |
| Build status check | Gate | Blocks the deploy of an agent config, prompt, or model change until the verdict policy is satisfied. |
| UI Review (assign reviewers) | The bench | A roster of evaluators per scenario, with required approvals and escalation rules. |
| TurboSnap | Selective re-run | Only re-run scenarios whose inputs (prompt, tools, fixtures, design system) changed. |

---

## 2. Who it is for

| Persona | What they need from Bench | What they must never have to do |
|---|---|---|
| **Design-ops lead** | Confidence that the design-system agent will not corrupt the library; a weekly view of drift across scenarios. | Read raw transcripts. |
| **Product designer** | See the rendered artifact before and after, decide if the change is acceptable. | Understand tool-call semantics. |
| **Design engineer** | See exactly which tool calls changed and why the output drifted; reproduce a run locally. | Guess which prompt version produced a build. |
| **Prompt / agent engineer** | Run the full matrix on a prompt change; compare candidate vs baseline; ship behind the gate. | Manually re-check scenarios that did not change. |
| **Accessibility, localisation, brand, legal reviewers** | Be pulled in only when a run touches their domain, with the relevant slice pre-highlighted. | Review every run. |
| **Security / platform** | Audit log of every write an agent made, in every environment, with the policy that allowed it. | Trust a screenshot. |
| **Agent evaluators** | A rubric, a fixture, and a place to file a verdict with evidence. | Be the only line of defence. |

---

## 3. Core concepts

### Scenario
A scripted task with a fixture and a success definition. Example:

```
scenario: localize-de
title:    Produce the de-DE variant of Order Summary
fixture:  figma://Checkout v3 / Order Summary / Desktop (node 12:884)
          tokens@3.2.0, copy-deck@2026-09
task:     Duplicate the frame, translate copy, resolve text expansion
          within the layout rules, hand back a review link.
success:  - Source frame untouched (write-scope policy WS-2)
          - All strings from the approved copy deck
          - No truncation; layout rule L-4 respected
          - Contrast ≥ 4.5:1 on every text node
```

### Condition
One point in the variant space. Bench declares axes per suite; the product of chosen values is the
matrix. See §4 for the full taxonomy.

### Run
The captured evidence for one scenario × condition:

- **Trajectory** — ordered tool calls with arguments, results, and reasoning summaries.
- **Artifacts** — rendered outputs. Figma frames and components are rendered to PNG + a semantic
  tree; code is rendered via Storybook/Playwright; documents are rendered to HTML.
- **Telemetry** — tokens in/out, wall-clock latency, cost, retries, tool errors.
- **Provenance** — model ID, prompt hash, tool policy hash, fixture hash, seed, git SHA.

### Baseline
The most recently accepted run for that scenario × condition. Baselines are per-branch, inherit from
the base branch (as in Chromatic), and can be pinned.

### Drift
The diff between a run and its baseline, computed on three layers:

1. **Trajectory drift** — added / removed / reordered tool calls; changed arguments; changed
   write targets. Classified by severity: a new *write* is always at least "review", a write outside
   the declared scope is "critical".
2. **Artifact drift** — pixel diff (with anti-aliasing tolerance) and semantic diff (token usage,
   layer names, text content, component instances, ARIA tree).
3. **Telemetry drift** — cost, latency, tokens vs baseline with per-suite thresholds.

### The bench
The set of evaluators assigned to a scenario. Each evaluator is one of:

- **Rule grader (agent)** — deterministic checks: write-scope policy, token allow-list, contrast,
  string source, layout rules. Cheap, fast, runs on every run.
- **Rubric judge (agent)** — an LLM grader scoring against a written rubric with evidence quotes.
  Runs on every run with drift.
- **Human reviewer** — pulled in by routing rules (domain touched, severity, sampling rate).
- **Human owner** — required for verdict on critical drift; can override an agent verdict with a
  recorded reason.

### Verdict and gate
Each evaluator casts Accept / Deny / Discuss. The suite's **verdict policy** turns individual verdicts
into a gate state:

```
gate = BLOCKED   if any rule grader is critical and no owner override
gate = BLOCKED   if any required human has not voted
gate = BLOCKED   if any human denies
gate = REVIEW    if any rubric judge < threshold and no human accept
gate = PASSED    otherwise
```

Accepting a run promotes it to baseline for that scenario × condition on that branch.

---

## 4. Variant taxonomy

The point of the matrix is to make non-determinism *legible*. Every axis below is one Bench should
be able to declare; each suite picks the subset that matters. Cost grows multiplicatively, so the
taxonomy also records what each axis costs and how to prune it.

| Axis | Example values | Why it matters in a design workflow | Cost / pruning |
|---|---|---|---|
| **Model** | claude-opus-5, claude-sonnet-5, claude-haiku-4-5 | Cheaper models drift on layout judgement and tool discipline; upgrades change behaviour silently. | Run the full matrix on the primary model; sample 20% on secondaries. |
| **Prompt version** | v14 (baseline), v15 (candidate) | The unit of change most agent engineers ship. | Only candidate vs baseline; never the whole history. |
| **Tool policy** | full-write, duplicate-only, read-only | The single largest source of consequential risk. | Always run duplicate-only; run full-write only in isolated fixtures. |
| **Fixture state** | seed, empty cart, 40-line order, unpublished library, stale tokens | Edge fixtures expose truncation, overflow, and fallback behaviour. | Curate 3–5 named fixtures per scenario. |
| **Locale** | en-US, de-DE, ja-JP, ar-SA | Text expansion, script, RTL mirroring, number/date formats. | de-DE (expansion) and ar-SA (RTL) catch most layout issues. |
| **Persona / role** | viewer, editor, admin, contractor | Permission tier changes what tools succeed and what the agent tries instead. | Run viewer and editor; admin only for admin scenarios. |
| **Fault injection** | none, Figma API 503, rate-limited, partial token fetch | Retry loops, silent fallbacks, and hallucinated results appear only under failure. | One fault per scenario per week, rotating. |
| **Memory state** | cold, warm (previous task in context), stale (outdated library in memory) | Warm memory can carry over a wrong assumption; stale memory is a real enterprise condition. | Cold on every run; warm/stale on a schedule. |
| **Seed / temperature** | seed 1–5 at t=0; t=0.7 | Quantifies flakiness; separates "the change caused it" from "the dice caused it". | 3 seeds on drift only. |
| **Turn budget** | 20, 40, 80 steps | Agents behave differently near a budget: skip steps, summarise, or fabricate completion. | Test at the production budget and at 50%. |
| **Interruption** | none, human interjects at step N, cancel at step N | Whether the agent resumes cleanly, re-does writes, or loses state. | Manual scenarios only. |
| **Input ambiguity** | precise brief, vague brief, contradictory brief | Whether the agent asks, assumes, or invents. | One ambiguity variant per scenario. |
| **Adversarial input** | prompt injection in a Figma layer name, in a copy deck, in a PR comment | Design files are untrusted content; agents read them. | Weekly, red-team owned. |
| **Design-system version** | tokens@3.1 vs 3.2, component lib major bump | The thing that changes most in enterprise design orgs. | Run on every DS release. |
| **Device / viewport** | desktop, tablet, mobile | For artifacts rendered as UI, the classic Chromatic axis still applies. | As per Chromatic modes. |
| **Concurrency** | one agent, two agents on the same file | Write conflicts, lock behaviour, last-writer-wins damage. | Monthly. |

**Matrix explosion guard.** A suite of 6 scenarios × 16 axes at 2–3 values each is millions of
runs. Bench requires each suite to declare a *primary slice* (the cells that run on every change),
*scheduled slices* (nightly/weekly), and *on-demand slices*. Selective re-run (§7) further prunes by
input hash.

---

## 5. Risk and concern register

Each risk names who is best placed to catch it. "Agent" means a rule grader or rubric judge; "Human"
means it needs judgement, accountability, or context that is not in the run; "Both" means an agent
detects and a human decides.

### 5.1 Consequential actions

| Risk | Severity | Caught by | Mitigation in Bench |
|---|---|---|---|
| Agent writes to the source of truth (library frame, main branch, CMS) instead of a copy | Critical | Agent | Write-scope policy (WS-*) rule grader on every run; any out-of-scope write is critical drift; runs execute against forked fixtures. |
| Destructive operations (delete, detach instance, unpublish) | Critical | Agent | Destructive-op allow-list; runs in isolated fixture; verdict requires owner. |
| Agent completes the task by disabling a constraint (removes auto-layout, overrides a token, skips a lint) | High | Both | Semantic artifact diff flags constraint removals; rubric judge asked explicitly. |
| Partial writes on failure (half-migrated tokens) | High | Agent | Fault-injection variants; rule grader checks atomicity. |
| Actions in the wrong environment (prod vs staging design file) | Critical | Agent | Provenance check: fixture hash must match declared fixture. |

### 5.2 Output quality and fidelity

| Risk | Severity | Caught by | Mitigation |
|---|---|---|---|
| Design-system drift: hard-coded values instead of tokens, off-system components | High | Agent | Token allow-list grader; component-instance diff. |
| Text truncation / overflow under expansion (de-DE +30%, fi-FI +40%) | High | Both | Locale variants; pixel diff; layout rule graders. |
| Accessibility regressions (contrast, focus order, missing labels) | High | Agent | Contrast grader on artifact semantic tree; ARIA-tree diff for code artifacts. |
| Brand voice drift in generated copy | Medium | Both | Rubric judge with voice guide; human brand reviewer on sampled runs. |
| Hallucinated content (invented copy not in the deck, invented token names) | High | Agent | String-source grader; token existence check. |
| RTL mirroring errors | High | Both | ar-SA variant; human localisation reviewer required. |
| Visual near-misses a pixel diff misses (wrong icon, semantically wrong component) | Medium | Human | Semantic diff + human review on sampled "unchanged" runs. |

### 5.3 Evaluation integrity

| Risk | Severity | Caught by | Mitigation |
|---|---|---|---|
| Agent grading agent: shared blind spots, same model family | High | Human | Rubric judges use a different model family from the agent under test; humans sample 10% of agent-accepted runs. |
| Goodharting: the agent learns to satisfy the grader, not the task | High | Human | Rubrics are versioned and rotated; hidden holdout scenarios. |
| Baseline poisoning: a bad run gets accepted and becomes the contract | High | Both | Accepting critical-drift runs requires an owner + reason; baseline history is revertible. |
| Reviewer fatigue and rubber-stamping | High | Human (process) | Triage ranks by severity; bulk-accept is disabled for critical drift; per-reviewer accept-rate is visible. |
| Flakiness misread as regression (or the reverse) | Medium | Agent | Multi-seed reruns on drift; flake score per scenario; "accept as flaky" is a distinct verdict. |
| Rubric ambiguity leading to inconsistent scores | Medium | Both | Every rubric item requires an evidence quote; inter-rater agreement is tracked. |
| Grader prompt injection via the artifact under review | High | Agent | Graders see structured evidence, never raw untrusted strings as instructions. |
| Review comments treated as instructions by the agent on the next run | High | Agent | Reviews are data; the agent never reads Bench comments as input. |

### 5.4 Data, privacy, and governance

| Risk | Severity | Caught by | Mitigation |
|---|---|---|---|
| PII or customer data in fixtures leaks into transcripts, screenshots, or grader prompts | Critical | Agent | Fixture scanning; redaction on capture; synthetic fixtures by default. |
| Unreleased product designs visible to third-party graders | High | Human (policy) | Grader models run inside the enterprise boundary; data-residency declared per suite. |
| Auditability: who accepted what, on which evidence, with which policy | High | Both | Immutable verdict log with evidence hashes; export to SIEM. |
| Consent and disclosure: reviewers do not know a verdict was agent-cast | Medium | Human (policy) | Every verdict is labelled with its evaluator type; agent verdicts never appear as human. |
| Retention of screenshots and transcripts beyond policy | Medium | Agent | Per-suite retention; artifacts stored with fixture classification. |
| IP: generated assets derived from third-party fonts, images, or libraries | Medium | Human | Asset provenance in the artifact semantic tree; legal reviewer routing rule. |

### 5.5 Cost, latency, and operations

| Risk | Severity | Caught by | Mitigation |
|---|---|---|---|
| Matrix explosion makes the suite too slow to gate a PR | High | Both | Primary slice + selective re-run; budget per suite; the gate reports "partial" honestly. |
| Cost drift: a prompt change doubles tokens without changing output | Medium | Agent | Telemetry drift thresholds; cost is a first-class diff layer. |
| Latency drift crossing a UX threshold | Medium | Agent | p95 latency per scenario with thresholds. |
| Third-party rate limits (Figma, GitHub) during a suite run | Medium | Agent | Cached fixtures; fault-injection variants make the fallback path visible. |
| Vendor lock-in of the eval format | Low | Human | Open run/verdict schema (JSON); export everything. |

### 5.6 Human factors

| Risk | Severity | Caught by | Mitigation |
|---|---|---|---|
| Over-automation: humans stop looking because agents "have it" | High | Human (process) | Mandatory human sampling; the gate shows the human-coverage ratio. |
| Under-automation: every run needs a human, so nobody runs it | High | Human (process) | Rule graders clear the obvious; humans see ranked drift only. |
| Reviewer bias: accepting the agent's framing of its own work | Medium | Human | Diff view leads with evidence, not the agent's summary; the agent's self-report is collapsed by default. |
| Accountability gap: "the agent accepted it" | High | Human (policy) | Every gate pass names a human owner. |
| Loss of design craft: reviewers evaluate rubric boxes, not the work | Medium | Human | The artifact render is the primary view; the rubric is secondary. |

---

## 6. The experience

### 6.1 Surfaces

1. **Suite overview** — every scenario × condition as a matrix. Cells encode state: unchanged,
   drift (needs review), accepted, denied, error, flaky, new. The matrix is the Chromatic "build" page.
2. **Run review** — three panes:
   - *Trajectory* — baseline vs candidate, step by step, with added/removed/changed markers and
     write targets highlighted. Agent reasoning is collapsed by default.
   - *Artifact* — rendered before/after with pixel diff overlay and a semantic diff list (tokens,
     components, strings, contrast).
   - *The bench* — every evaluator, their verdict, their evidence; the viewer's own verdict controls;
     the gate state and what would change it.
3. **Risk register** — the living list above, filterable by category, severity, and detector; each
   risk links to the graders and routing rules that address it.
4. **Baseline history** — who accepted what, when, with which policy; one-click revert.
5. **Suite settings** — axes, slices, verdict policy, routing rules, rubrics, retention.

### 6.2 Interaction principles

- **Evidence before narrative.** The agent's own summary of what it did is never the first thing a
  reviewer sees.
- **Severity sets the order.** Critical drift at the top, unchanged cells collapsed.
- **Agent verdicts are labelled and second-class.** They can block; they cannot pass the gate alone.
- **Every verdict carries a reason.** Deny and Discuss require text; Accept on critical drift requires
  an owner.
- **The gate is honest.** Partial matrix runs say so; skipped slices are listed.
- **Reproduce in one click.** Every run has a command that re-runs it locally with the same
  provenance.

### 6.3 Where agents and humans sit

| Task | Agent | Human |
|---|---|---|
| Run the matrix, capture, render, diff | ● | |
| Rule checks: scope, tokens, contrast, strings, atomicity | ● | |
| Rubric scoring with evidence quotes | ● | samples |
| Triage ranking | ● | |
| Accept unchanged cells | ● | samples 10% |
| Accept low-severity drift | ● | samples |
| Accept / deny medium drift | proposes | decides |
| Accept / deny critical drift | blocks | decides, with reason |
| Override an agent verdict | | ● owner only |
| Change a rubric or policy | proposes | ● |
| Promote a baseline | | ● |

---

## 7. Architecture

```
┌─────────────┐   ┌─────────────┐   ┌──────────────┐   ┌──────────────┐
│  Trigger    │──▶│  Runner     │──▶│  Capture     │──▶│  Renderer    │
│ PR / cron / │   │ scenario ×  │   │ trajectory,  │   │ Figma → PNG  │
│ manual      │   │ condition   │   │ artifacts,   │   │ + semantic   │
└─────────────┘   │ in forked   │   │ telemetry,   │   │ tree; code → │
                  │ fixtures    │   │ provenance   │   │ Storybook;   │
                  └─────────────┘   └──────────────┘   │ docs → HTML  │
                                                       └──────┬───────┘
┌─────────────┐   ┌─────────────┐   ┌──────────────┐          │
│  Gate       │◀──│  Bench      │◀──│  Differ      │◀─────────┘
│ PR check,   │   │ rule graders│   │ trajectory / │
│ deploy hook,│   │ rubric judge│   │ artifact /   │
│ baseline    │   │ human route │   │ telemetry    │
│ promotion   │   │ verdict log │   │ drift + rank │
└─────────────┘   └─────────────┘   └──────────────┘
```

- **Runner** executes the agent under test inside an isolated fixture: a forked Figma file, a
  throwaway branch, a sandboxed CMS. Tool policies are enforced at the tool-proxy layer, not by
  asking the agent nicely.
- **Capture** records every tool call and result as structured JSON (open schema), with hashes of
  every input that could change behaviour.
- **Renderer** produces a viewable artifact for each output type. Figma outputs render via the REST
  image API plus a node-tree export; code renders through the existing Storybook + Playwright
  pipeline (this is where Chromatic itself can plug in); documents render to HTML.
- **Differ** computes drift on the three layers and ranks it.
- **Bench** runs rule graders, then rubric judges (different model family from the agent under
  test), then applies routing rules to request human review. Verdicts land in an immutable log.
- **Gate** exposes a status check (GitHub, GitLab), a webhook for deploy pipelines, and baseline
  promotion.
- **Selective re-run** hashes the inputs of each scenario × condition (prompt, tool policy, fixture,
  design-system version, model) and re-runs only cells whose hash changed.

### Integrations for enterprise design workflows

Figma (REST + plugin for fixture forking), Storybook/Chromatic (code artifacts), GitHub/GitLab
(status checks, PR comments), Jira/Linear (Discuss verdicts open tickets), Slack (routing
notifications), SSO/SCIM, SIEM export of the verdict log.

---

## 8. Rubrics

Rubric judges score against written rubrics with mandatory evidence quotes. A starting set for
design-ops agents:

- **Scope discipline** — did the agent do what was asked and nothing else? Writes only to declared
  targets; no side-effects.
- **System fidelity** — tokens, components, and patterns from the design system; no hard-coded
  values; correct variants.
- **Layout integrity** — auto-layout preserved; no truncation; responsive rules respected.
- **Content fidelity** — strings from the approved source; no invented content; correct locale rules.
- **Accessibility** — contrast ≥ 4.5:1 (3:1 for large text), focus order, labels, target sizes.
- **Communication** — the agent's hand-back is accurate; it flagged what it could not do; it did not
  claim completion it did not achieve.
- **Efficiency** — within token and latency budgets; no redundant tool calls.

Scores are 1–5 with a per-item threshold; "Communication" is scored by comparing the agent's
self-report against the captured trajectory, which is the single best detector of fabricated
completion.

---

## 9. Metrics

| Metric | Why |
|---|---|
| Drift rate per scenario per week | Stability of the agent under test. |
| Critical-drift catch rate (agent vs human first-detector) | Are rule graders doing their job? |
| Human coverage ratio (runs a human looked at / runs gated) | Guards against over-automation. |
| Inter-rater agreement (agent judge vs human on sampled runs) | Calibrates the rubric judge. |
| Time-to-verdict, p50 / p95 | The gate must not become the bottleneck. |
| Flake score per scenario | Separates dice from regressions. |
| Baseline reverts per month | Detects baseline poisoning. |
| Cost per gated change | Keeps the matrix affordable. |
| Reviewer accept-rate distribution | Surfaces rubber-stamping. |

---

## 10. Roadmap

**Phase 0 — Prototype (this repository).** A static, interactive prototype of the run review and
suite matrix with realistic sample data, living at agentsandhumans.ai. Purpose: align designers,
engineers, and reviewers on the shape of the experience and collect the risk register.

**Phase 1 — Capture and diff.** Runner + capture in isolated Figma and repo fixtures for three
scenarios; trajectory and telemetry drift; rule graders for write-scope, tokens, contrast, strings.
Verdicts are human-only. Output is a GitHub status check.

**Phase 2 — The bench.** Rubric judges on a different model family; routing rules; the three-pane
review; baseline history; Discuss → ticket.

**Phase 3 — Matrix and pruning.** Declared axes and slices; selective re-run; flake scoring; fault
injection; scheduled slices.

**Phase 4 — Governance.** SSO, audit export, retention, data-residency per suite, red-team
scenarios, human-coverage reporting.

---

## 11. Open questions

1. **Who owns the baseline** when a scenario spans design and engineering? Proposed: the scenario
   declares an owner role; the routing rule names the person.
2. **How much of the agent's reasoning to capture.** Full reasoning is useful for debugging and a
   liability for retention. Proposed: capture summaries by default, full reasoning on critical drift
   only, with per-suite retention.
3. **Should agent verdicts ever pass a gate alone?** Proposed: only for unchanged cells and only
   with a human sampling floor.
4. **Pixel diff tolerance for generated design artifacts.** Font rendering and anti-aliasing differ
   between Figma exports; semantic diff should lead and pixel diff should support.
5. **Rubric drift.** Rubrics need versioning and their own review gate.
6. **Adversarial fixtures.** Who maintains the prompt-injection corpus for design files, and how is
   it kept out of the agent's training data?

---

## 12. Glossary

**Scenario** a scripted task and fixture · **Condition** one point in the variant space · **Run** the
captured evidence for a scenario × condition · **Baseline** the last accepted run · **Drift** the
diff between a run and its baseline · **Bench** the evaluators assigned to a scenario · **Verdict**
Accept / Deny / Discuss with a reason · **Gate** the status that blocks or allows a change ·
**Slice** a named subset of the matrix · **Rule grader** a deterministic agent check · **Rubric
judge** an LLM grader with a written rubric · **Owner** the human who can override and promote.
