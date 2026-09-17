# Brief for Tomas Shepherd — dev.to, X, and organic growth for agentsandhumans.ai

*Owner: Tomas Shepherd. Sponsor: DC. Goal: the highest sustainable volume of organic search and social traffic to agentsandhumans.ai, converted into registrations from designers, developers, and product managers. Status: draft for review.*

---

## 1. What we are asking you to do

Three deliverables, in this order:

1. **Set up and run a dev.to presence for agentsandhumans.ai** that is tuned for search: an organisation page, a canonical-URL syndication pipeline from the site, and a publishing cadence that earns backlinks and search rankings for the terms our three audiences actually type.
2. **Set up and run a daily X pipeline** that builds a community around agents-and-humans work and sends people to register.
3. **Become a contributor to the brand repo on GitHub** so that every piece of content, every meta change, and every tracking change goes in as a pull request and gets reviewed before it ships.

Everything below is in service of one number: **registrations per week, by source and by role**. Traffic that does not move that number is not the goal.

## 2. Who we are trying to reach and what they search for

| Audience | What they are trying to do | Search intent to own | Where they hang out |
|---|---|---|---|
| **Product designers** | Learn how to design for and with agents; evaluate agent output; keep craft standards when an agent does the first draft. | "agentic design", "design for AI agents", "agent UX patterns", "evaluating AI design output", "Figma agent workflow" | dev.to (growing), X, LinkedIn, Figma community, Designer News-style communities |
| **Developers** | Build, test, and ship agents; evaluate non-deterministic behaviour; wire agents into design systems and repos. | "agent evals", "how to evaluate LLM agents", "agentic workflow testing", "MCP server design", "Chromatic for agents" | dev.to (core), X, Hacker News, GitHub, Reddit |
| **Product managers** | Decide what to hand to agents, what to gate, how to measure quality and risk. | "AI agent product management", "agent risk register", "agent quality gate", "human in the loop review" | X, LinkedIn, dev.to (lighter), newsletters |

The site's existing material gives us an unusual head start: the eval-experience plan, the risk register, the variant taxonomy, and the agentic-evals essay are all deep, original, and searchable. Most of the first quarter's content is **repurposing what exists** into the formats that rank and spread, not writing from scratch.

## 3. Deliverable 1 — dev.to set up for SEO

### 3.1 Why dev.to

dev.to has a domain that already ranks, pages that get indexed within hours, and an audience of exactly two of our three personas. It is not a replacement for the site. It is a **distribution channel that points search authority and readers back to agentsandhumans.ai**. Used wrongly it competes with the site for the same keywords. Used correctly it wins the long tail and hands the ranking to us via canonical URLs.

### 3.2 Setup checklist

- **Organisation account** named `agentsandhumans` with the brand mark, one-line description that contains the primary phrase ("evals and workflows for agents and humans"), and the site URL. Tomas and DC as admins. Every author publishes under the org.
- **Author profiles** for each contributor with the site link, a role line, and a consistent avatar. Profiles rank and get followed; a bare profile loses follows.
- **Canonical URL on every post.** Each article is published on agentsandhumans.ai first, then cross-posted to dev.to with `canonical_url` set to the site page. This is the single most important SEO decision here. dev.to supports it natively in the front matter. Without it we split ranking signal across two domains and dev.to wins.
- **RSS-based syndication.** dev.to can import from an RSS feed. Point it at the site's essay feed so every new essay lands as a draft on dev.to with canonical set, and you only add the dev.to-specific intro and tags. If the site feed does not exist yet, request it as an issue in the site repo (NETWORK101/future-of-work-main).
- **Series.** Use dev.to series for multi-part content ("Agent evals from scratch", "Designing with agents"). Series pages are internally linked and rank as a cluster.
- **Tags.** Four per post, chosen by traffic and fit. Start with `ai`, `webdev`, `design`, `productivity`, `devops`, `testing`, `ux`, `productmanagement`, `opensource`, `tutorial`. Check each tag's follower count on dev.to before choosing.
- **Cover image.** Every post gets a 1000×420 cover in the house style. Posts with covers get roughly twice the click-through on the dev.to feed and on social previews.
- **Embeds.** Use dev.to's embeds for GitHub repos and CodePen or similar for anything interactive. Embeds keep readers on the page longer, which is a ranking signal on dev.to's own feed.
- **Call to action.** One CTA per post, at the end, always to a registration page with UTM parameters: `?utm_source=devto&utm_medium=article&utm_campaign=<slug>`.
- **Comments.** Reply to every comment within 24 hours for the first week of a post. Comment count drives the dev.to feed ranking.

### 3.3 Content plan for dev.to

Formats that reliably rank and get shared on dev.to, in rough order of return:

1. **Long-form tutorials with code** (2,000 to 3,500 words). "How to build a Chromatic-style eval gate for an agent" is the flagship. Developers search for these, bookmark them, and link to them.
2. **Opinionated explainers** built from the agentic-evals essay. "Why agent evals are not automation tests" as a standalone post with one diagram.
3. **Reference lists** built from the plan. "The nine enterprise agent use cases and an eval prompt for each", "A risk register for agents you can copy". Lists get linked to from other posts and get republished on aggregators.
4. **Comparison and glossary posts**. "Scenario, condition, run, baseline, drift, bench, verdict, gate: a vocabulary for agent review". Glossaries capture definitional searches for years.
5. **Build logs**. Short, honest posts about what shipped on agentsandhumans.ai this fortnight and what was learned. These build a following more than they build search.

Cadence: **two posts per week for the first eight weeks**, then one per week plus one build log per fortnight. Front-load the flagship tutorial and the glossary in week one because they will take the longest to rank.

### 3.4 On-site SEO that dev.to depends on

The dev.to work only pays off if the canonical target is in good shape. Raise these as PRs in the site repo:

- Every essay page has a unique title under 60 characters, a meta description under 155, an `og:image`, and a `canonical` tag that points to itself.
- An XML sitemap and an RSS feed for essays, both submitted to Google Search Console and Bing Webmaster Tools.
- Structured data: `Article` on essays, `Organization` on the home page, `FAQPage` where a page answers questions. This gets us rich results and is cheap.
- A registration page with a short, descriptive URL and a single form. Every CTA on every channel points here.
- Internal links between the plan, the essay, the prototype, and the registration page. Search engines follow the links we give them.
- Core Web Vitals in the green on mobile. The pages are static, so this is mostly image sizes and font loading.

## 4. Deliverable 2 — a daily X pipeline

### 4.1 What the account is for

The X account is the community's front door. Its job is to make designers, developers, and PMs feel that agents-and-humans work is a real movement with a home, and that registering is how they join it. Traffic to the site is the outcome, not the content.

### 4.2 Setup

- **Account**: `@agentsandhumans` (or the closest available), brand mark, header image with the tagline, bio with the site link and one sentence that names all three audiences, pinned post that explains what we do and links to registration.
- **Scheduling tool**: Typefully or Buffer, whichever you prefer, connected to the account. Queue a week at a time, review on Friday.
- **Tracking**: every link uses `?utm_source=x&utm_medium=social&utm_campaign=<theme>`. Use the site's analytics, not X's, as the source of truth.
- **Community layer**: create an X Community for "agents and humans" once the account has 500 followers. Communities get their own feed placement and are the cheapest way X gives us to build a group rather than an audience.

### 4.3 Daily cadence

One primary post every weekday, plus replies. Suggested weekly rhythm, so each persona gets served at least once:

| Day | Post type | Persona |
|---|---|---|
| Monday | A thread built from a dev.to post or essay, six to eight posts, first post is the hook, last post links out. | Developers |
| Tuesday | A single visual: a diagram, a screenshot of the prototype, a before-and-after of an agent run. | Designers |
| Wednesday | A question or a poll about how people are handling agents at work. Reply to every answer. | PMs |
| Thursday | A build log: what shipped, one screenshot, one lesson. | All |
| Friday | A curated roundup: three links from other people in the space, with one line each on why they matter. Tag the authors. | All |

Weekend: schedule one repost of the week's best-performing post with a new hook.

### 4.4 What builds a community rather than a broadcast

- **Reply more than you post.** For the first three months, spend 30 minutes a day replying to people talking about agent workflows, evals, and design tooling. Replies are where followers come from.
- **Tag and quote generously.** Every roundup names real people. People share things they are named in.
- **Run a recurring event.** A monthly "agent run review" on X Spaces or a live stream where we walk through a real eval on the prototype. Announce it on Monday, run it, post the recap Thursday.
- **Show work in progress.** The prototype and the plan are interesting because they are unfinished. Post drafts, ask for opinions, credit the people whose opinions changed the work.
- **Never post a link without a reason to click.** A bare link with a title is the worst-performing format on X. Lead with the insight, link at the end or in the first reply.

## 5. Other tactical, proven methods

These are the channels and mechanics that have consistently driven organic and social traffic for developer and design tools. Do them in the order listed; each one feeds the next.

1. **Hacker News, Show HN.** Post the prototype as a Show HN once the registration page is ready. One shot, on a Tuesday or Wednesday morning US time, title under 80 characters, plain description, be present in the comments all day. A good Show HN is worth a quarter of dev.to posts in one afternoon and the backlinks last for years.
2. **Reddit.** r/ProductManagement, r/UXDesign, r/artificial, r/MachineLearning, r/webdev. Post the content, not the link, and link in a comment. Read each subreddit's rules on self-promotion first. Reddit threads now rank on Google for long-tail questions, so a well-answered thread is search content.
3. **LinkedIn**, for the PM and design personas that X under-serves. Repost the Monday thread as a LinkedIn article and the Thursday build log as a native post. LinkedIn rewards native text with no outbound link; put the link in the first comment.
4. **Newsletter swaps and guest posts.** Identify ten newsletters in agent tooling, design ops, and product. Offer a guest post or a short "what we learned" section in exchange for a link. Backlinks from real newsletters are the highest-quality links we can get.
5. **A GitHub presence.** Make the prototype and the eval prompt set public on GitHub with a good README that links back to the site. GitHub READMEs rank, get starred, and get linked. Add a "Used by" section as adopters appear.
6. **Product Hunt**, once registration is open and there is something to try. Launch on a Tuesday, line up twenty supporters in advance, have the first comment ready. Treat it as a social event, not a search event.
7. **Directories and listings.** Submit to AI tool directories, "awesome" lists on GitHub (awesome-llm-agents, awesome-design-tools), and the dev.to and Hashnode listings. Each one is a small backlink and a trickle of referrals that adds up.
8. **Search Console as a content source.** After four weeks, export the queries where the site ranks between position 8 and 25. Each one is a page that nearly ranks. Write or expand a page for each. This is the highest-return SEO loop there is and it needs no new ideas.
9. **Embeddable assets.** The variant taxonomy and the risk register are the kind of thing other people put in their own decks and docs. Publish them as clean images and a copyable table with a "source: agentsandhumans.ai" line. Attribution links follow.
10. **Registration-page conversion.** None of the above matters if the page leaks. One form, three fields at most, a clear statement of what you get by registering, social proof once we have it, and a thank-you page that asks the new registrant to share on X with a pre-written post.

## 6. Measurement

Report weekly, in a single table, in the brand repo under `reports/`:

| Metric | Source | Target after 12 weeks |
|---|---|---|
| Registrations per week, by role | Site analytics plus the registration form's role field | Set after the first two weeks' baseline |
| Registrations by source (organic, dev.to, X, LinkedIn, HN, Reddit, other) | UTM parameters | Organic and dev.to combined above 50% |
| Organic sessions | Search Console and site analytics | Month-on-month growth every month |
| Ranking pages and queries in the top 10 | Search Console | 20 queries |
| dev.to followers, post views, reactions | dev.to dashboard | 1,000 followers |
| X followers, reply rate, link clicks | X analytics and UTMs | 2,000 followers, replies on every post |
| Backlinks from unique domains | Search Console links report | 50 domains |

Any tactic that has not moved registrations after six weeks gets cut or changed. Say so in the report.

## 7. Deliverable 3 — contributor access and the review flow

- **Request**: DC adds Tomas as a contributor on the brand repo in the NETWORK101 GitHub organisation, and on the site repo (NETWORK101/future-of-work-main) for the on-site SEO changes in section 3.4. Write access to branches, no direct pushes to `main`. Confirm the exact brand repo name with DC; this brief assumes it is the repo that holds the brand assets and voice guidelines.
- **Every change is a pull request.** Content drafts, meta tag changes, tracking changes, cover images, and the weekly report all go in as PRs from a branch named `content/<slug>` or `seo/<slug>`. DC reviews. Nothing publishes on dev.to or X before the PR that holds its source is merged.
- **PR template.** Each content PR carries: the target persona, the primary search phrase, the canonical URL, the UTM campaign name, the intended publish date and channel, and the cover image. This keeps review fast and makes the archive searchable later.
- **Where things live.** `content/devto/` for article sources in markdown with dev.to front matter, `content/x/` for weekly post queues, `reports/` for the weekly metrics table, `assets/covers/` for images.
- **The link checker.** The site repo already has a link checker under `workers/link-check`. Run it before every content PR so we never publish a dead link.

## 8. First two weeks

| Week | Tomas | DC |
|---|---|---|
| 1 | Accept contributor invite. Create the dev.to org and X account. Draft the flagship tutorial and the glossary post as PRs. Set up the scheduling tool and the UTM convention. | Send the invites. Confirm the registration page URL and the brand repo name. Review the two drafts. |
| 2 | Publish both posts on the site then dev.to with canonical set. Start the daily X cadence. Open the on-site SEO PRs (meta, sitemap, RSS, structured data). Submit the sitemap to Search Console. | Review and merge. Share the posts from personal accounts. Agree the 12-week targets. |

## 9. Open questions for DC

1. Exact name of the brand repo and who else reviews there.
2. Is the registration page live, and what does a registrant get today? The CTA copy depends on the answer.
3. Is there a budget for a scheduling tool and for one cover-image template from a designer?
4. Do we want the dev.to and X accounts under a shared login vault, and who owns them if Tomas moves on?
