---
name: daylog
description: Reconstruct what Joi was doing on a given day, or day-by-day across a week (Mon-Sun), by combining Google Calendar and sent mail, git commits across his repos, GitHub activity, and his Bear WPlan/DPlan notes. Use when asked "what was I doing on <date>", "what did I do last week", "recap my week", "fill in my WPlan DONE", or any request to reconstruct past working days.
---

# Daylog — reconstruct a working day or week

Answers "what was I doing?" for a past day or week by pulling four independent
sources and reconciling them into a per-day narrative.

## Tool

```bash
/Users/joi/.claude/skills/daylog/bin/daylog <subcommand> <spec> [flags]
```

Always invoke it by that absolute path (so a single "always allow" rule covers
it). Subcommands: `range`, `git`, `gh`, `google`, `bear`, `all`.

`<spec>` accepts:

| spec | meaning |
|---|---|
| `today`, `yesterday` | single day |
| `2026-07-27` | single day |
| `this-week`, `last-week` | Mon–Sun week |
| `week:2026-07-23` | the Mon–Sun week containing that date |
| `W31`, `2026-W31` | ISO week number (Mon–Sun) |
| `2026-07-20..2026-07-24` | explicit inclusive range |

Weeks always run **Monday → Sunday**, matching how the WPlan notes are titled.

### Normal usage

Start with one call and read everything:

```bash
/Users/joi/.claude/skills/daylog/bin/daylog all 2026-07-27
/Users/joi/.claude/skills/daylog/bin/daylog all last-week --stat
```

`--stat` adds per-day/per-repo churn (files, +/- lines), useful for judging
how heavy a coding day was. `--received` adds inbound mail (noisy; only when
sent mail alone leaves the day unexplained). Run individual subcommands only
when following up on one source.

Every source degrades independently. A `NOTE:` line means that source was
unavailable — carry that into the answer rather than silently omitting it.

## What each source is good for

- **Bear (`bear`)** — Joi's own account, the highest-value source. `## Plan` is
  what he *intended* that week; `## DONE` is what he says he *did*. Prefer it
  over inference whenever it covers the day.
- **Google (`google`)** — calendar shows meetings; sent mail shows who he was
  dealing with and about what. This is the only source for non-code work.
- **git (`git`)** — ground truth for code, including unpushed work and repos
  with no GitHub remote (cardinal). Covers all worktrees automatically.
- **GitHub (`gh`)** — adds what local git cannot see: PR reviews, issue
  comments, branch creation, and repos not cloned locally.

Repo → context: `protos` = CrankWheel, `bboo` = BellaBooks, `cardinal` =
Quarter (local only, no remote), `kloi` = Klói agent (snilli-com), `somatic` =
personal.

## Reading the output correctly

These matter — getting them wrong produces confident, wrong recaps.

- **WPlan `## DONE` is not always day-labelled.** Some weeks use `Mon` / `Tue`
  headers; others are free-form prose covering the whole week (often in
  Icelandic). With prose, attribute items to the week, not to a specific day,
  unless the text itself dates them.
- **DPlan is a live rolling doc.** Its `# DONE` is recent — today, or the last
  few days — and is *not* reliably dated. Treat it as weak evidence for the
  most recent days only, and never as evidence about a day weeks ago.
- **Agent commits.** `who=agent` marks commits authored by `kloi@agent.local`,
  i.e. work Joi directed his agent to do rather than typed himself. Count it as
  his activity but describe it as agent-driven.
- **Calendar events are *scheduled*, not necessarily attended.** Declined and
  skipped meetings still appear, and much of the "Work Reminders" calendar is
  recurring self-reminders ("Check system load", "láta reikna laun") rather than
  meetings. Treat a calendar entry as an intention; corroborate with sent mail
  or commits before asserting it happened.
- **The same meeting appears under several accounts.** A BellaBooks meeting
  shows on both `joi@crankwheel.com` and `joi@bellabooksai.com`. Dedupe on
  date+time+summary and count it once; which accounts it appeared on is not
  itself interesting.
- **Not all sent mail is hand-written.** Automated reports post from his
  accounts and carry the SENT label — Klói triage digests, "No new CERT-IS
  vulnerabilities", CrankWheel billing renewal notices. These show routine
  automation ran, not that he sat and wrote them.
- **GitHub events expire.** The events feed retains only ~30–90 days and caps
  at 300 events. For older dates it prints a NOTE and you should lean on git
  and the PR/issue searches, which have no retention limit.
- **Commits are filtered on author date** (when the work was written), not
  commit date, so rebased work lands on the day it was actually done.
- **Timezone is GMT year-round** (Iceland), so timestamps need no conversion.
- **`bb` / `cw` prefixes** in plan notes mean BellaBooks and CrankWheel.
  `bbb`/`bbs`/`bbc` are BellaBooks sub-tags — don't over-read them.

## How to answer

1. Resolve the spec and run `daylog all <spec>`.
2. For each day in range, write a short narrative that **leads with what he was
   actually working on**, not with a list of sources. Group by project
   (CrankWheel / BellaBooks / Quarter / personal), since that is how he plans.
3. Reconcile rather than concatenate. Meetings, mail, commits and PRs on the
   same theme are one thread of work — say so once. A branch name like
   `joi-avoidTrackingBotsForVideoShares` plus a matching PR and commit is a
   single item.
4. Note the shape of the day where it's visible: mostly meetings vs mostly
   heads-down coding, which project dominated, anything that spilled across
   days.
5. Distinguish **evidence from inference.** Say "no calendar data (token
   expired)" rather than implying the day had no meetings. Never invent
   meetings, mail, or commits to fill a gap.
6. If the WPlan `## DONE` already covers the day, say what it already records
   and add only what the other sources contribute beyond it.

For a week request, give a per-day section plus a short "themes of the week"
summary at the end.

## Writing back to Bear

`bear_reader.py` is **read-only**; this skill cannot edit notes. If Joi wants
the recap filed into a WPlan `## DONE`, produce the text and let him paste it,
or offer to put it on the clipboard via the `clipboard-markdown` skill.

## Setup

Google is the one source needing per-account authorization; the others work out
of the box. See `reference/google-accounts-setup.md` — it covers adding the
three additional accounts and re-authorizing an expired token.

Repos, accounts, author identities and the GitHub username live in
`config.sh` next to this file. Add a repo by adding its path to `REPOS`;
worktrees need no separate entry.
