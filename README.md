# The Future of Work

A Chromatic-style eval experience for agentic design workflows, staffed by agents and humans.
Built for [agentsandhumans.ai](https://agentsandhumans.ai).

Every change to a design-ops agent renders every scenario under every condition that matters. The
run is diffed against an approved baseline, a bench of agent and human evaluators reaches a verdict,
and nothing ships until the gate is satisfied.

## What is here

| Path | What it is |
|---|---|
| `index.html` | The Phase 0 interactive prototype: suite matrix, three-pane run review, the bench with a castable verdict, variant taxonomy, filterable risk register, workflow, and roadmap. Single file, no build step, sample data only. |
| `docs/eval-experience-plan.md` | The detailed plan: positioning, personas, core concepts, the full variant taxonomy, the risk and concern register, the experience spec, architecture, rubrics, metrics, roadmap, and open questions. |

## Run it

Open `index.html` in a browser, or serve the folder:

```
python3 -m http.server 8080
```

The page is static and can be dropped onto any host, including a path on agentsandhumans.ai.
Fonts load from Google Fonts with system fallbacks. The only browser state is the viewer's own
verdict on the sample run, kept in `localStorage`.

## Vocabulary

Scenario · Condition · Run · Baseline · Drift · Bench (the evaluators assigned to a scenario) ·
Verdict · Gate. See the glossary at the end of the plan.
