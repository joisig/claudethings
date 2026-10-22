---
name: projects
description: Joi's project tracker in ~/p/projects - every multi-session project across CrankWheel, Bella Books, Quarter, Snilli, Somatic, Cardinal, Personal and Grosvenor, with briefs to resume from, to-dos, waits on people and dates, and the backlog. Use when Joi asks what is going on, what is next for a project, when the next step can happen, who to nudge, what fits the time Joi has ("I have 40 minutes"), to add something to a project's to-dos or backlog, to start a project, to tidy up or close projects; and for the handoff when we wrap up work that belongs to a project (the global CLAUDE.md says when).
---

# projects — Joi's project tracker

`~/p/projects` is a local git repo of markdown files, one per project, grouped by
theme. Joi is the only user. This skill says how to read and change it.

## Tool

```bash
/Users/joi/.claude/skills/projects/bin/projects <command> ...
```

Always use that absolute path. Commands:

| Command | Use |
|---|---|
| `render` | Write the generated `overview.md` and `<theme>/README.md` |
| `check` | Validate every file. `save` runs it too |
| `next [--date D] [--nudges]` | Actionable items, nudges due, deadlines in 7 days, CrankWheel items on Joi, sessions that ended without a handoff |
| `fit --minutes N [--attention shallow\|normal\|deep] [--repo PATH]... [--no-worktree] [--limit K]` | Ranked shortlist of items that fit the time |
| `find [--repo PATH] [--branch B]` | Which project this repo and branch belong to (default: the current directory) |
| `landed [theme/slug...]` | Has each Work line's commit or PR landed on main/master? |
| `landed --repo PATH (--commit SHA \| --branch B) [--pr URL]` | The same, ad hoc |
| `sessions --since D [--repo PATH]` | Claude Code sessions since D: title, transcript, cwds, branches, active time, first and last prompt |
| `tail ID [-n COUNT]` | Last user and assistant messages of a session |
| `session-time [ID] [--since "YYYY-MM-DD HH:MM"]` | Active minutes of a session; no ID = this session |
| `save -m MSG [--resolves SESSION]... FILE...` | Check, render, then commit only FILE... |

## Rules

- **Edit tracker files only with the Edit and Write tools**, never with shell commands.
  The Edit tool refuses to write a file that changed after you read it, and that keeps
  parallel sessions from overwriting each other.
- **Commit only with `projects save`**, listing every file you changed, moved or
  deleted (for a move, both paths). Never run git in `~/p/projects` yourself.
- `overview.md` and `<theme>/README.md` are generated. Never edit them.
- When `check` or `save` fails, fix the file. Do not work around the format.
- A **project** is work that spans more than one session, or has a wait or a gate. A
  one-session fix is a to-do item of a project; it does not start a project.
- Name projects as `theme/slug`. When Joi's name for a project matches more than one,
  ask.
- Everything here stays on this laptop, so detail is fine. Link email as Superhuman
  thread links, not message IDs.

## Files

```
CLAUDE.md  themes.md  people.md  inbox.md      hand-written
overview.md  <theme>/README.md                 generated
<theme>/<slug>.md                              a project
<theme>/<slug>/README.md (+ notes files)       a project that grew into a folder
archive/<theme>/...                            done and dropped projects
```

- `themes.md`: `## <folder> — <name>`, `Repos:` (main checkouts; worktrees are found
  with git), `Delegation: on|off`.
- `people.md`: `## @handle — Name`, then `- Role:`, `- Delegate:`, `- Access:`,
  `- Email:`, `- GitHub:`. Joi is `@joi`.
- `inbox.md`: things Joi said that have no project yet. Move them out when their
  place is clear.

## A project file

```markdown
---
title: Session diagnostics for reconnect problems
state: active            # active | paused | done | dropped
reentry: medium          # low | medium | high
created: 2026-10-14
touched: 2026-10-22      # last real work on it
---

## Goal
Two or three lines.

## Brief
- Where things stand.
- Plan documents (absolute paths); worktree and session ID of the last session.
- How to start again: what to read first, what to run.
- Traps and decisions that are not obvious from the code.

## Work
- ~/w/protos · branch joi-session-diag · commit 3f2a9c1 · PR https://github.com/CrankWheel/protos/pull/1234

## Waiting on others
- [ ] Fix reconnect bug in session-diag
      Waiting: @rodion since 2026-10-20 · nudge 2026-10-24
      Thread: https://mail.superhuman.com/...
      Then: review the PR, run the soak test

## Ready for me
- [ ] Manual test of Salesforce brand-account switching
      Size: 30 min · shallow · protos, any worktree
      Unblocks: @yuliia

## Later
- [ ] Check 5 days of prod data for the reconnect spike
      Not before: 2026-10-27
      Size: 15 min · shallow · no worktree
      How: run X, look for Y. Good means Z.

## Backlog
- Idea: per-account diag toggle

## Done
- [x] Add diag logging (PR #1234, landed 2026-10-18)

## Log
- 2026-10-22 16:40 · ~70 min (guessed 30) · added the soak-test script; waiting on Rodion
```

The allowed sections are Goal, Brief, Work, Waiting on others, Ready for me, Later,
Backlog, Done, Log and Notes, in that order. Leave out the ones a project does not
need.

**Item lines.** A `- [ ]` line, then indented `Key: value` lines, all with the same
indent. A line indented deeper continues the previous key.

| Key | Value |
|---|---|
| `Waiting:` | `@handle[, @handle] since <date>`, optionally `· nudge <date>`. Required in "Waiting on others" |
| `Not before:` | a date; `after <theme>/<slug>` (met when that project is done); `after <theme>/<slug>: <start of an item's text>` (met when that item is checked); or free text (never met on its own). Required in "Later" |
| `Due:` | a date, only for a real deadline |
| `Size:` | `<N> min · <deep\|normal\|shallow> · <place>[ · dev server][ · prod]` |
| `Needs:` | access or people, e.g. `@birta or @fridfinnur`, `source access`, `cwstaging deploy` |
| `Unblocks:` | handles of people waiting for this item |
| `Thread:` | Superhuman thread link |
| `PR:` | PR URL |
| `How:` | for a wait: exactly what to check when the wait ends, and what good looks like |
| `Then:` | what follows once it is done |

`<place>` is `no worktree` (email, review, decision), `<repo>, any worktree`, or
`<repo>, branch <name>`. `<repo>` is the repo's folder name from `themes.md`
(`protos`, `cwcompliance`), or its path when the folder name says nothing
(`~/q/bboo/main`). The minutes are the shortest useful session for the item, not the
whole job.

**Rules for items.**
- Every item in "Later" has `Not before:`. Every wait on time or data has `How:`.
  Without it, nobody remembers what "check the data" meant a week later.
- An item moves between sections when its state changes. Done items get `[x]` and go
  to "Done" with a short note (PR, date).
- A "Later" item whose `Not before:` is met counts as ready; move it to "Ready for me"
  at the next handoff or tidy-up.

**Work lines.** One per repo: the main checkout's path, and when known `branch`,
`commit` (the last relevant commit: what `landed` checks) and `PR` (full URL, can
repeat; the last one is the current chunk's, and only it counts for `landed`). Write the SHA at each handoff, at `ship-branch` and at `wtconsolidate`. A
branch name alone proves nothing: home branches get reused. A project that lands in
chunks keeps the SHA of its latest chunk.

**Derived, never written:** status (`ready`, `waiting`, `idle`, or the state when
paused), next date (earliest open `Not before:` date, nudge or `Due:`), and who holds
the ball (`Waiting:` handles).

## What Joi says, and what you do

| Joi says | You do |
|---|---|
| "Add X to the backlog / to-dos of Y" | Add it in the right section with the keys you can fill in (CrankWheel: the delegation question first). Save |
| "What's next for Y?" / "When can we take the next step?" | Read the project; answer from its items and dates |
| "What's going on?" / "Overview of CrankWheel" | `render`, then read `overview.md` or the theme README, and summarize |
| "What can I do today?" | `next`, then summarize |
| "I have 40 minutes" / "three worktrees, 15 min shallow each" | See "Fitting work to time" |
| "Who do I need to nudge?" | `next --nudges`, then offer drafts (see "Nudges") |
| "Let's wrap up" / a natural end point of work on a project | The handoff |
| "Start a project for this" | Create the file from what this session knows, with a full brief. Save |
| "Tidy up projects" | The tidy-up run |
| Something with no project yet | `inbox.md`, or ask which project |

## Delegation (themes with `Delegation: on`: CrankWheel)

Joi wants out of CrankWheel's day-to-day work. When an item or project is added there
and nobody else is in `Waiting:`, ask "who other than you could do this?" and suggest
someone from `people.md`, by role and by access. Say when it needs Birta's or
Fridfinnur's access, source access, or the cwstaging deploy. When Joi delegates, the
item goes to "Waiting on others" with `Waiting:` and a nudge date.

`next` lists the open CrankWheel items that are on Joi. Read that list against
`people.md` now and then and raise the ones that look delegable. The tool does not
judge; you do. No delegation prompts for other themes.

## The handoff

Required when we stop work on a project, and when work we are wrapping up becomes a
new project. Find the project with `projects find` (or Joi names it). Then:

1. **Rewrite the brief** so that a new session in any worktree can start cold:
   where things stand, plan documents, how to start again, traps.
2. **Items:** check off what is done and move it to "Done"; move items between
   sections; add new items with `Size:`. Every wait gets `Waiting:` or `Not before:`,
   and `How:` where it applies.
3. **Frontmatter and Work:** renew `reentry` and `touched`; update the Work lines
   (branch, last relevant commit SHA, PR URLs).
4. **Log line:** `- <YYYY-MM-DD HH:MM> · ~<N> min (guessed <G>) · <what happened>`.
   N is `projects session-time --since "<time of this project's previous log line>"`
   (whole session if there is none). G is your guess for this same piece of work,
   when you made one; leave out "(guessed G)" otherwise. The time comes from the
   transcript and can include agent work that ran unattended, hence the `~`.
5. `projects save -m "<message>" <the project file> [other files]`.

Prefer a branch for projects that do not land on main in chunks, and say so when such
work starts on a protected or home branch. Then the branch is where work resumes.

## Re-entry, sizes and calibration

- `reentry` is your guess at how much re-reading and remembering it takes to start
  again: low (5 min), medium (15), high (30). Base it on the brief and on how tangled
  the work is. `fit` raises it one level when the project is untouched for more than
  21 days.
- Before starting a piece of work, state your guess of how long it takes. At the
  handoff the log line records guess against actual.
- When you estimate a `Size:` or a guess, read the recent log lines of similar work
  and adjust.

## Fitting work to time

Run `fit` with the minutes and what Joi said about attention and place:
`--attention shallow` for low-attention work, `--repo` for the repos or worktrees Joi
has free, `--no-worktree` for away-from-code time. Then choose from the shortlist
with judgment and say why (unblocks someone, ready since a date, cheap to re-enter).
For several worktrees, assign items to the worktrees that are really free: check that
two items do not need the same branch, a dev server or another shared resource, and
that the worktree is clean (`git status`).

## Nudges

When a nudge date has passed, offer to draft reminders. For each: find the thread
(the `Thread:` link, or search the person's email address from `people.md` with the
subject) and create a **Superhuman reply draft in that thread**. Never send. Use the
account the thread lives in (CrankWheel mail for CrankWheel people, joi@bellabooksai.com
for Erla). Without a thread, draft a new mail and say so. Then set the next nudge date.

## The tidy-up run

Projects are not closed eagerly. On "tidy up projects":

1. `projects landed`: per Work line, whether the commit is on main/master (local and
   origin) or the PR is merged. `unknown` is never "not landed": say what is unknown.
2. `projects sessions --since <oldest touched date among open projects>` and
   `projects tail` for sessions in the projects' repos, to see work that happened
   without a handoff.
3. `projects next` for pending handoffs (sessions that ended without one).
4. Email threads only when Joi asks.

Then propose one list, project by project: **close** (state `done`, move to
`archive/<theme>/`), **chunk landed** (check items, keep open), **stale** (ask), or
**leave open**. Shipped with `ship-branch` and landed on main means done; shipped
alone does not, because review and follow-ups remain. After Joi confirms, make the
changes and save, with the moved files' old and new paths.

## Pending handoffs (from the SessionEnd hook)

A session in a theme repo that changed files and ended without a handoff is listed by
`next`. To handle one: read it (`projects tail <id>`, more of the transcript when
needed), write the handoff into the project (or start one, or decide it needs none),
and save with `--resolves <id>`. A save of the matched project resolves it too.
Only a save that includes a project file (or `--resolves`) counts as a handoff for
the hooks; saving `inbox.md` or `people.md` alone does not.

## Hooks

`projects hook stop` and `projects hook session-end` are installed in
`~/.claude/settings.json` by `install.sh`. They act only for sessions whose cwd is in a
repo listed in `themes.md`.

- **Stop:** when the session changed files there (or committed) and has no handoff
  since, it asks you, at most once per 60 minutes of active time, to offer the handoff
  in one line *if* the work belongs to a project and we are at a stopping point. When
  that is not the case, say nothing about it.
- **SessionEnd:** records a session that ended without a handoff (see above).

Known limit: an edit that was rejected, or a `git commit` that failed, still counts
as a change, so such a session can get the reminder or a pending record it does not
need. Dismiss it.

`PROJECTS_HOOKS=off` in the environment turns both off.

## Tests

```bash
python3 -m unittest discover /Users/joi/p/claudethings/skills/projects/tests
```
