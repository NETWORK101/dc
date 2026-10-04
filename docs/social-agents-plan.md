# Growing Agents & Humans on social media with a team of agents

*Plain-English plan. Builds on `docs/devto-social-brief.md` and on tools the site already has: the dev.to desk, the propagators with Slack approval, the SEO audit, and the subscribe form.*

## The idea in one line

Agents do the repetitive work: finding conversations, drafting posts, scheduling, and measuring. A person approves every public post with one tap in Slack. Each week the numbers tell the agents what to do more of.

## The five agents

| # | Agent | What it does | When |
|---|---|---|---|
| 1 | **Listener** | Searches X, Reddit, Hacker News, LinkedIn and dev.to for people talking about AI agents, evals, agent UX or human-in-the-loop. It picks the 10 best threads and drafts a helpful reply to each. The reply links to a site page only when that page really answers the question. | Every morning |
| 2 | **Repurposer** | Turns each new essay, note or daily edition into one draft per channel: an X thread, a LinkedIn post, a Reddit post and a dev.to article. Every link carries a tracking tag (UTM). | When something publishes |
| 3 | **Publisher** | Posts approved drafts at each channel's best time, within each channel's rate limits. It uses the existing propagators and dev.to desk. | All day |
| 4 | **Analyst** | Pulls the numbers every day: visits by source, sign-ups by source, dev.to views and comments, and search rankings. It writes one short weekly report on what brought sign-ups and what didn't. | Daily, plus a Monday report |
| 5 | **Optimizer** | Reads the Analyst's report and changes next week's plan. It reposts the top performers with a new opening line and drops formats that brought no sign-ups. It proposes new posts for searches where the site is close to page one (positions 8 to 25). It tests two opening lines against each other. | Weekly |

The loop runs in this order: **Listen, then Draft, then a person approves, then Post, then Measure, then Adjust, and back to Listen.**

## Rules the agents never break

- **A person approves every public post and reply.** This uses the existing Slack GO / EDIT / SKIP buttons. Agents only draft.
- **No auto-DMs, no fake accounts, no mass-following, no buying engagement.** These get accounts banned and hurt trust.
- **Follow each platform's rules.** That means each subreddit's self-promotion rules, X's label for automated accounts, and the rate limits already in the propagators.
- **Reply to help first.** Most replies should carry no link at all.
- **Sign-ups are the scorecard, not likes.** Every link is tagged so you can see which posts actually brought people in.

## How to start (two weeks)

**Week 1: set up and draft only**
1. Make sure the dev.to desk, the propagators and the Slack approval channel are switched on.
2. Add the tracking-tag rule to every link: `?utm_source=<channel>&utm_medium=social&utm_campaign=<topic>`.
3. Turn on the **Repurposer** and **Listener** in draft-only mode. Spend about 15 minutes a day approving or editing in Slack.

**Week 2: publish and measure**
4. Turn on the **Publisher** for approved items.
5. Turn on the **Analyst** and read the first Monday report.
6. Pick the one channel that brought the most sign-ups and double down on it.

**Week 3 onward: let it learn**
7. Turn on the **Optimizer**. Every Monday, read its suggestions and approve or reject them.
8. After 6 weeks, cut any channel that brought no sign-ups.

## What to measure

| Number | Good sign |
|---|---|
| Sign-ups per week, by source | Going up most weeks |
| Share of sign-ups from search plus dev.to | Over 50% by week 12 |
| Replies that got a response back | Most of them |
| Searches where the site is on page one | 20 by week 12 |
| Time you spend approving | Under 20 minutes a day |

## Decisions needed from DC

1. Who taps GO in Slack each day: you, Tom, or both?
2. Which channels to start with? The suggestion is X and dev.to first, then LinkedIn, then Reddit.
3. Should the sign-up form ask for a role (designer, developer, product manager), so the report can show which audience is growing?
4. Can the Analyst get read access to Search Console and the site's analytics?
