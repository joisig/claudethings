---
name: wtconsolidate
description: Consolidate completed work from a repo's parallel worktrees into the main worktree - survey every worktree and its Claude Code sessions, ask about the doubtful ones, merge the finished ones into main (most conflict-prone first, tests after each merge), bring the worktrees back in line, tag the start and the end, then write a light HTML test plan and start the automated tests. Written for the bboo worktrees under ~/q/bboo. Use when the user types /wtconsolidate or asks to consolidate, gather or merge up the worktrees.
---

# wtconsolidate — gather finished worktree work on main

Several worktrees carry work in parallel, each with its own Claude Code sessions.
A consolidation moves everything that is finished onto the trunk, brings the
worktrees back in line with it, and leaves the user with a short plan of what is
still to test by hand.

This file describes the bboo setup. "Other repositories" at the end says what to
replace elsewhere.

| | bboo |
|---|---|
| Trunk | `~/q/bboo/main`, branch `main` |
| Worktrees | `secondary`, `tertiary`, `quaternary`, `quinary`, `senary`, `septary`, each in `~/q/bboo/<name>` with a home branch of the same name |
| Never touched | `BRelDemo`, `BRelProd` (release worktrees), scratch worktrees |
| Tests | `MIX_TEST_PARTITION=_main mix test` after a merge, `MIX_TEST_PARTITION=_main mix precommit` at the end |
| Test database | Always the trunk's private one (`MIX_TEST_PARTITION=_main` → `bboo_test_main`). The shared `bboo_test` carries columns from other worktrees' unmerged migrations, and that makes schema-checking tests fail for reasons outside the consolidation |
| Commits on the trunk | `main` is a protected branch: every commit you make on it (a collision fix, a `mix precommit` change) needs the user's OK. Show the diff and the commit message first |
| Fetch | `git fetch` over SSH can fail in Claude's shell (no key). Then ask the user to run `! git -C ~/q/bboo/main fetch origin` |
| Known collision | Every new column or table needs an entry in `lib/bboo/readonly_grants/spec.ex`, or `Bboo.ReadonlyGrantsTest` fails. A branch that adds a migration meets this as soon as it merges with a trunk that has the spec |
| Browser QA | Dev server on port 4001, started from the trunk with `./devprod.sh`. The QA user (`joi@quarter.is`) is only a viewer on account 16, so admin-only UI is checked on an account where the user is owner (92, 93) |

Run the skill from a session in the trunk worktree. To consolidate into another
worktree instead (for example when main is busy or carries unfinished work), see
"Consolidating into another worktree" near the end.

## Rules for the whole run

- **Positive evidence only.** A worktree is consolidated when there is evidence
  that its work is complete: the session says so, or the user says so. No evidence
  is doubt, and doubt goes to the user.
- **Other sessions' work is theirs.** Do not commit, stash, discard or edit
  uncommitted changes in another worktree unless the user says so for that worktree.
- **Do not delete branches.** Do not push, and do not push tags, before Step 9.
- **Commits on a protected trunk** need the user's OK, one by one (see the setup
  table). The user can give that OK in advance at Step 3 for small collision fixes.
- **No force.** No `reset --hard`, `checkout -f` or `--no-verify` on anything
  except undoing a merge you just made yourself on the trunk, and that only after
  the user agreed.
- Fail fast: when a step does not go as described here, stop and tell the user.
  Do not improvise a different end state.

## Tool

```bash
~/p/claudethings/skills/wtconsolidate/bin/wtsurvey survey --repo ~/q/bboo/main --only secondary,tertiary,quaternary,quinary,senary,septary
~/p/claudethings/skills/wtconsolidate/bin/wtsurvey tail <worktree dir> [-n 40] [--sessions 2]
```

`--only` is the list of worktrees that take part. Everything else (release
worktrees, scratch worktrees) is skipped and never touched.

`survey` is read-only. It prints, per worktree: branch, home branch, dirty files,
commits ahead of and behind the trunk, and the Claude Code sessions with their
status. Then the predicted result of each merge into the trunk, the same for each
pair of worktrees (with the commits two of them have in common that the trunk
lacks), the last commit all of them share, and the `consolidate-*` tags
with the next number.

`tail` prints the last messages of the sessions that ran in one worktree, live
sessions first.

```bash
~/p/claudethings/skills/wtconsolidate/bin/wtsurvey tests --repo ~/q/bboo/main
```

`tests` prints the test log (see "Records"), newest first. For each entry it says
how many commits changed how many files in the entry's paths since the commit it
was tested on.

## Records

All consolidations of a repository share one folder in the trunk's gitignored
`tmp/`: `tmp/<date>-wtconsolidate/`, where the date is the day of the first
consolidation. If a `tmp/*-wtconsolidate/` folder exists, use it. Do not create a
second one.

```
tmp/2026-10-02-wtconsolidate/
  test-log.jsonl                  every test result, from all consolidations
  consolidate-N/summary.md        what this consolidation did
  consolidate-N/test-plan.html    the plan from Step 9
  consolidate-N/logs/             output of the automated runs
```

### summary.md

The record of one consolidation. Write each section at the step that produces it,
and show the same section to the user in the chat at that moment.

The first line is `Status: <the step that was completed last>`, updated at every
step, and `Status: finished` only after the final report. The tags mark git
states; this line says how far the run came.

The sections:

| Section | Written at | Contents |
|---|---|---|
| **Decision** | end of Step 3 | Every worktree: branch, group (consolidate / leave / receives main only), the evidence or the user's answer behind it |
| **Merges** | Step 5, after each merge | Branch and its worktree, the sha that was merged, the trunk HEAD before and after, conflicts and how each was resolved, what the semantic check found, collision fixes with their commits, the test result. Say where it was difficult |
| **Worktrees after** | Step 6 | Each worktree: branch before → after, sha before → after, or why it was left alone. Sessions that were told |
| **Feature branches merged** | Step 6 | Each feature branch that is now on main, and that it still exists |
| **Changes by theme** | Step 8 | The overview, and the range it covers |
| **Automated tests** | Steps 5 and 10, as results arrive | What ran, on which commit, the result, where the log is |
| **Manual tests** | Step 8 and "Recording manual results" | What the user reported |
| **Open** | the end | Failing tests, worktrees left out, runs not approved, themes not tested yet |

### test-log.jsonl

One JSON object per line, appended, never rewritten. One line per thing that was
tested, at the grain of a theme or a named part of a theme, not of a single
assertion.

```json
{"at": "2026-10-02T21:14:00Z", "consolidation": 3, "commit": "<full sha that was tested>",
 "kind": "automated", "theme": "Payment-method vendors", "what": "mix precommit",
 "result": "pass", "paths": ["lib/bboo/payment_vendors", "lib/bboo_web/live/vendor"],
 "notes": "", "evidence": "consolidate-3/logs/precommit.log"}
```

| Field | Rule |
|---|---|
| `commit` | The commit the test ran on. For a manual test: the trunk HEAD at the time the user tested. For work the user tested in its worktree before the consolidation: the commit it was tested on, if the user or the session transcript can place it. When the commit is not known, write `null` and say so in `notes`. Do not guess a newer commit than the evidence supports |
| `kind` | `automated`, `manual`, or `manual-before-merge` (tested in the worktree, before the merge) |
| `result` | `pass`, `fail`, `partial` or `blocked`. Say in `notes` what `partial` leaves out |
| `paths` | The files or directories this theme lives in, relative to the repo root, taken from the theme's diff. They are how a later reader measures what changed since the test. Keep them narrow: a path that every commit touches makes every test look stale |
| `what` | For a suite-wide run such as `mix precommit`, write one line per theme with the same `what`, so that each theme carries its own paths. A green suite only proves what the suite covers: say in `notes` what it leaves out for this theme (in bboo the default run excludes the integration and `expensiveintegration` tests) |

A later failure does not remove an earlier pass: append the new line. The newest
line for a theme and `what` is the current state.

## Step 1 — survey

1. Run `git -C ~/q/bboo/main fetch origin`. If it fails, ask the user to run it
   (see the setup table) and compare again. If the trunk is behind its upstream,
   stop and ask the user: merging on top of a stale trunk makes the push harder.
2. Run `wtsurvey survey`. Call `ListAgents` too: it is the authority on which
   sessions are live, and it gives the names you need for Step 7.
3. A consolidation is unfinished when the survey says `UNFINISHED` (a start tag
   without an end tag), or when the newest `consolidate-N/summary.md` does not
   say `Status: finished`. Read that summary and the start tag's message
   (`git tag -l -n99 consolidate-start-N`), work out how far it came, and ask the
   user whether to continue it or to start a new one.
4. The trunk must be clean and on its branch. If it is dirty, or another live
   session in the trunk is `busy`, stop and ask.
5. **Baseline test of the trunk.** Start the trunk's test run in the background
   now (`MIX_TEST_PARTITION=_main mix test`); it runs while Step 2 runs. A red
   trunk is reported in Step 3, and the user decides whether to go on. Without
   this baseline, a failure after the first merge cannot be blamed on the merge
   or on the trunk.

## Step 2 — where does each worktree stand?

**The trunk's own work takes part too.** Work is often committed straight to the
trunk between two consolidations. List it: `git log --first-parent --no-merges
--oneline <summary base>..main`, where the summary base is `consolidate-end-(N-1)`,
or the survey's **last aligned** commit on the first run. When that list is not
empty, give the trunk a sub-agent of its own, with the same instructions as below
(its sessions are the other sessions in the trunk; leave out your own). That work
is on the trunk already, so it cannot be left out. Its verdict decides something
else: "in progress" or "unclear" goes to **Ask** in Step 3, with the options to go
on and mark those themes as unfinished in the plan, to stop, or to consolidate
into another worktree instead (see "Consolidating into another worktree").

For each worktree that has commits ahead of the trunk or dirty files, start one
sub-agent. Start them all in one message so that they run in parallel. Give each:

- the worktree path, and its block from the survey;
- the instruction to run `wtsurvey tail <dir>`, plus `git status`, `git log
  <trunk>..HEAD --oneline` and `git diff --stat` in that worktree, and to read
  more of a transcript only when the tail does not settle the question;
- the instruction to change nothing;
- the question to answer, in this form:

  > **Verdict:** complete / in progress / unclear.
  > **Work:** two or three lines on what the branch and the dirty files contain.
  > **Evidence:** the quotes or facts the verdict rests on, with their time.
  > **Left to do**, according to the session.

"Complete" means: what is left is only of the kind "move this to main, run the
migrations, run the tests again, test by hand". An open plan, a failing test, a
question to the user that has no answer yet, a half-done refactor, or dirty files
that belong to the work all mean "in progress". A session with status `busy` or
`waiting` is never "complete" on the sub-agent's word alone.

Then sort the worktrees into three groups:

| Group | When |
|---|---|
| **Consolidate** | Verdict complete, clean tree, no session `busy` or `waiting` |
| **Leave** | Verdict in progress |
| **Ask** | Everything else: unclear, complete but dirty, complete but a session is waiting, a home branch with commits that are not on the trunk while the worktree is on a feature branch, a detached HEAD, no session record at all |

**Work that travels together.** Worktrees merge each other. When the survey shows
that a worktree you would consolidate contains another one, or has `COMMON
COMMITS` with it, merging the first brings that part of the second onto the trunk
too. If the second is not in **Consolidate**, the first goes to **Ask**: the user
decides between both, neither, or accepting that the shared commits go in. Name
the shared commits (`git log --oneline <merge base of the two> ^main`).

A worktree with no commits ahead and a clean tree is neither: it only receives the
trunk in Step 6.

## Step 3 — ask the user

Show one table: worktree, branch, group, and the one-line reason. Include a row
for the trunk's own work and one for the baseline test result. Then ask about
the **Ask** group with `AskUserQuestion`, one question per worktree, grouped in as
few calls as possible. A red baseline is one more question: go on, or stop. Typical options: consolidate it; do not consolidate it (it still receives main in
Step 6 if it is clean); do not touch it at all; commit the
dirty files first and then consolidate (name the files); consolidate the committed
part and leave the dirty files where they are.

The user can also move a worktree between **Consolidate** and **Leave**. Go on
only when every worktree has a group. If nothing is left to consolidate, say so
and stop before the start tag.

Then write the **Decision** section of `summary.md` and show it: this is the
statement of what is about to happen, before any merge starts.

## Step 4 — start tag

Use the next number N from the survey. Create an annotated tag on the trunk tip.
The message records what is needed to undo the consolidation, and what the
summary in Step 8 starts from:

```bash
git -C ~/q/bboo/main tag -a consolidate-start-N -F <file>
```

```
Consolidation N, started <date and time>
trunk main <sha>
consolidate secondary  joi-reglaMatchingAndSuperMcp <sha>
consolidate tertiary   tertiary <sha>
leave       quaternary quaternary <sha> (dirty)
summary-base <sha> (<consolidate-end-(N-1), or "last aligned" on the first run>)
```

## Step 5 — merge into the trunk

**Order.** Use the predictions from the survey. When one approved branch contains
another approved one, merge only the containing branch: the contained one arrives
with it, and its worktree is brought in line in Step 6. After that, the branches
with predicted conflicts and the most shared files go first, the ones that touch
nothing in common last. The hard merges then happen on the simplest base, and a
late surprise is unlikely.

For each branch, in that order:

1. **Check again.** Other sessions keep working while you do. The branch tip must
   still be the sha in the start tag, the worktree must still be clean, and no
   session in it may be `busy` (run the survey again, or `git rev-parse` and
   `git status`). If the tip moved, stop and ask: the new commits were not part
   of the decision.
2. Note the trunk HEAD. Then merge the approved sha, always with a merge commit:
   `git -C ~/q/bboo/main merge --no-ff -m "Merge branch '<branch>' (consolidation N)" <sha>`.
3. **Conflicts:** resolve them with both sides' intent in mind. Read the commits
   of both sides for the conflicted files. When the right resolution is a product
   decision and not a mechanical one, ask the user. Commit the merge.
4. **Semantic check**, sized to the overlap:
   - *Shared files, a conflict, or the same module or schema touched from both
     sides:* read the combined result. Look for a function that one side changed
     and the other side calls in the old way, two migrations for the same table,
     duplicate routes or config keys, a prompt or a fixture edited by both, a
     renamed thing still used under its old name.
   - *Nothing in common:* no scan. The tests are the check.
   - *Always:* list the migrations that this merge adds. Their timestamps must be
     unique and must sort after the migrations the trunk had already. If one sorts
     earlier than a migration that already ran on the dev database, say so in the
     report; do not rename it without asking.
5. **Tests:** `MIX_TEST_PARTITION=_main mix test` in the trunk. Run it in the
   background with the tool's own background option, not a shell `&`, and wait for
   the notification.
6. **A failure:** work out from the failure and the two diffs whether the
   combination caused it or the branch brought it. Do not check out a parent to
   run the tests there: `mix test` migrates the shared test database, so an older
   commit would run against a newer schema and prove nothing. Fix what the
   combination broke, in a separate commit on the trunk that says which two pieces
   of work collided (on a protected trunk, after the user's OK). Check the known
   collisions in the setup table first. If the fix is not small, or the branch itself is broken, stop
   and ask: fix here, or undo this merge (back to the HEAD noted in point 2) and
   move the worktree to **Leave**. If the undone merge added migrations, tell the
   user that the test database is now ahead of the code and needs a reset; do not
   reset it yourself.
7. Add this merge to the **Merges** section of `summary.md`, and tell the user in
   two or three lines how it went.

Do not start the next merge while the tests of the previous one are red.

**After the last merge**, run `MIX_TEST_PARTITION=_main mix precommit` in the trunk. This is the full check
of the end state. It can change files (it unlocks unused dependencies): if the
tree is dirty afterwards, show the change, commit it on the trunk, and run it
again. Go on only when it is green and the tree is clean. Keep the output in
`consolidate-N/logs/` and note the HEAD it ran on, for the test log (Step 8).

## Step 6 — bring the worktrees in line

Call `ListAgents` again first: new sessions start while the merges run. Check
each worktree again right before you change it (tip, clean tree, no `busy`
session), as in Step 5. A worktree the user said not to touch is skipped. A
consolidated worktree whose session is busy now is left on its branch: its work
is on the trunk already, and only the switch back to the home branch waits.

**Consolidated worktrees** end on their home branch, equal to the trunk:

1. If the worktree is on a feature branch, `git checkout <home branch>`. The
   feature branch stays; it is not deleted.
2. `git merge --ff-only main`. If that fails, the home branch has commits that
   the trunk lacks. Stop and ask.
3. If the worktree was merged with dirty files left in place (the user's choice in
   Step 3) and the checkout or the merge refuses, leave the worktree as it is and
   report it.

**The other worktrees** receive the trunk only when all of this holds: the tree
is clean, no session in it is `busy`, and the survey's kind of prediction
(`git merge-tree --write-tree <head> main`) says the merge is clean. Then
`git merge --no-edit main` in that worktree. Otherwise leave it alone and name it
in the report with the reason. Do not resolve conflicts inside work that is still
in progress.

Run no `mix` commands in the other worktrees.

Write the **Worktrees after** and **Feature branches merged** sections of
`summary.md` (add the sessions after Step 7).

## Step 7 — tell the live sessions

For each live session in a worktree that changed in Step 6 (not your own), send
one message with `SendMessage`, to the name `ListAgents` shows:

> wtconsolidate: consolidation N merged <the themes, one line> into main, and main
> was merged into this worktree (<old sha> → <new sha>). <If so: this worktree was
> switched from <feature branch> to <home branch>; the feature branch still
> exists.> Nothing else here was touched. Re-read files before you edit them, and
> keep this in mind when you continue. No reply needed.

To a session in a worktree that was left alone, send nothing, except when the
trunk now contains something that will collide with its work (a predicted
conflict). Then one line that says which files.

## Step 8 — end tag, migrations, summary

1. `git -C ~/q/bboo/main tag -a consolidate-end-N -m "<worktrees consolidated, worktrees left>"`.
2. Run `mix ecto.migrate` in the trunk (bboo runs migrations only from `main`).
   If a migration fails, stop and report; do not roll back on your own.
3. Give the user an overview of what is new on the trunk, **theme by theme, not
   commit by commit**: what each theme changes for the user of the product, where
   it came from, and anything it needs (a migration, a setting, a toggle, a key).

   The range is `<summary base>..consolidate-end-N`:
   - normally the base is `consolidate-end-(N-1)`, so the range also covers work
     that was committed straight to the trunk between two consolidations;
   - on the first run, or when that tag is missing, the base is the survey's
     **last aligned** commit, the last moment the trunk and the worktrees were
     the same. Say which base you used and its date. If it looks too old (one
     neglected worktree can pull it back), ask the user for a better one.
4. Ask which of the themes the user remembers testing already, and how far
   (`AskUserQuestion`, multi-select, plus free text). Work that was tested before
   a conflict resolution or a collision fix touched it counts as not tested for
   that part.
5. Write the **Changes by theme** section of `summary.md`. Now that the themes
   are named, append the `mix precommit` result to `test-log.jsonl`, one
   `automated` line per theme, with the HEAD it ran on. Append one
   `manual-before-merge` line to `test-log.jsonl` for each theme the user says
   was tested, with the branch tip from the start tag as `commit`, and what was
   and was not covered in `notes`. For the trunk's own work, `commit` is the
   trunk commit it was tested on, or `null` when the user does not say.

## Step 9 — the consolidation test plan

Write one self-contained HTML file and open it:

```
~/q/bboo/main/tmp/<date>-wtconsolidate/consolidate-N/test-plan.html
```

This is a memory aid for the user, who worked on these changes in the last few
days. It is not a QA sign-off document, and `TEST_PLAN_GUIDELINES.md` does not
bind it: no docx, no sign-off table, no step-by-step scripts for flows the user
knows. Take from that file only what protects against mistakes: its environment
rules (never post to a live DK+ vendor), and its dual-environment rule when the
range touches the files it lists.

Contents, in this order:

1. **Header:** consolidation N, the date, the range, the worktrees that went in
   and the ones that were left.
2. **Setup:** checklists and runbooks for what the changes need before testing:
   migrations (already run, say which), new settings or secrets, toggles under
   `/super`, seed data, services to restart. Commands in copyable blocks.
3. **One section per theme:** what to try, as checkboxes of a line or two each;
   then **gotchas**: where two pieces of work met, what a conflict resolution
   changed, what the tests cannot see, known limits. Mark what the user already
   tested as done, with a note of what was tested.
4. **Covered automatically:** what the runs of Step 10 check, so that the user
   does not repeat it by hand.
5. **Left out:** worktrees that were not consolidated, and why.

Checkbox state is kept in `localStorage`, so that a reload does not lose it. Plain
styling, readable in light and dark mode, no external resources.

Each checkbox has a stable id (`A1`, `A2`, `B1`, ...) and each theme has a small
notes field. A **Copy results** button puts the state on the clipboard as plain
text: a first line with the repository, the consolidation number and the sha of
`consolidate-end-N`, then one line per item with its id, title, done or not, and
the notes. The page
cannot write to the log itself; the user pastes that text to you (see "Recording
manual results").

## Step 10 — automated tests

Work out everything that can be tested without the user, tell the user the list,
and start it while they read the plan:

- **Free, start at once, in the background:** `bboo-browser-qa` flows for the new
  themes, including the trunk's own work, that meet that skill's conditions and
  spend nothing: they only read and click through existing data. (`mix precommit`
  already ran in Step 5.) The dev server must run the trunk's code. When the range
  changes `lib/bboo/application.ex` or `config/`, a server started before the
  merges does not have the change; ask the user to restart `./devprod.sh` first.
  Do not restart it yourself. Run the flows in a background sub-agent, so that
  the screenshots stay out of your context.
- **Costs API money, ask first:** browser flows that upload or ingest a document,
  digitize, or make the agent run; the `expensiveintegration` tests and the
  reliability run from `TEST_PLAN_GUIDELINES.md`, for the themes that touch what
  they guard (agent prompts, tools, the data the agent sees). List each with its
  expected cost and time, and start only what the user approves. When you cannot
  tell whether a flow spends money, it belongs here.

Keep each run's output in `consolidate-N/logs/`. When a result arrives: report it,
append its lines to `test-log.jsonl` (the commit is the trunk HEAD the run started
on), add it to the **Automated tests** section of `summary.md`, and update the
"covered automatically" section of the plan if the run failed or found something.
The `mix test` runs after the single merges are not logged: they ran on
intermediate commits, and the `mix precommit` on the end state replaces them.

When the free runs are done, ask whether to push the trunk to origin. Push only
on a yes. The `consolidate-*` tags stay local unless the user asks for them to be
pushed.

## Final report

When the free runs are done, complete `summary.md` (the **Open** section) and show
the user the whole of it in the chat, in short form: which worktrees were
consolidated and which were left and why; which feature branches are now on main;
how each merge went and where it was difficult; what was tested automatically and
the results; what the user has tested by hand so far; sessions that were told;
what is still running or open. End with the paths of `summary.md` and the test
plan.

## Recording manual results

The user tests by hand after the skill has finished, often in the same session,
sometimes days later (`/wtconsolidate log`, or "log my test results"). When the
user reports results, in their own words or as text from the plan's **Copy
results** button:

1. Find the consolidation the results belong to: the first line of pasted **Copy
   results** text names it. Without that line, ask, unless the user tested in
   this same session right after the consolidation. Match each item to a theme in
   that consolidation's `summary.md`, and ask about what you cannot match.
2. Append one `manual` line per theme or named part to `test-log.jsonl`, with the
   trunk HEAD as `commit`. If the trunk has moved since the consolidation, ask
   whether the test was done on the current state.
3. Add them to the **Manual tests** section of that consolidation's `summary.md`.
4. A reported failure is logged as `fail` with the user's description. Do not
   start to fix it unless asked.

When the session that ran the consolidation is about to end and no manual results
came, say once that they can be logged later this way.

## Use by a full test plan

The log is there for the release test plan. Whoever writes one runs
`wtsurvey tests` first and sorts each area of the release:

- **Tested at consolidation, no drift:** a candidate for lighter testing.
- **Tested, but its paths changed since:** test it again, with a focus on what
  changed.
- **Never logged, only `fail`, `partial` or `blocked`, or the commit unknown:**
  test it in full.

The drift figure is a hint, not proof. It only sees the paths the entry lists, so
a change in a shared caller, the configuration, a dependency or a prompt does not
show. Read the `notes` for what a test did not cover, and look at what else
changed in the release before you reduce the testing of an area.

A `manual-before-merge` pass is weaker than a `manual` one: it says nothing about
the combination with the other work.

## Consolidating into another worktree

Sometimes the trunk is busy or carries unfinished work, and the user asks to
consolidate into another worktree, for example `secondary`. The flow is the same,
with that worktree as the target in place of the trunk. What changes:

- **Run from the target worktree**, and check it like the trunk in Step 1: clean,
  on its home branch, no other live session `busy` in it.
- **`wtsurvey` always measures against the first worktree (`main`).** Use its
  sessions, dirt and pairwise predictions as they are, but compute the merge
  predictions against the target yourself: `git merge-tree --write-tree --name-only
  <target> <branch>`, and `git log --oneline <target>..<branch>` for what each
  branch brings.
- **The target's home branch is not protected** (unless it is `main`), so collision
  fixes are committed without asking. Say each one in the report.
- **Tests** use the target's private database: `MIX_TEST_PARTITION=_<target>`.
- **No migrations.** In bboo they run only from `main`. In Step 8, list the
  migrations the consolidation brings and say that they run when the target
  reaches `main`.
- **Tags and records** keep the same names and the same folder in the trunk's
  `tmp/` (the numbering is shared). Write `target <worktree> <branch> <sha>` in
  the start tag's message in place of the `trunk` line, and the target in the
  header of `summary.md` and of the plan.
- **Step 6:** consolidated worktrees end on their home branch, equal to the
  target. The trunk itself is a worktree that was left out: it receives nothing.
- **Browser QA** needs the dev server to run the target's code, and the dev
  server normally runs from `main`. Ask the user before Step 10.
- **Bringing it to `main` later** is a normal consolidation that has the target
  in its **Consolidate** group.

## Other repositories

The flow is the same; replace the setup facts. Find them in the repository's
CLAUDE.md and the project memory before you start, and ask for what is missing.

| Fact | Where it is used |
|---|---|
| The trunk worktree and its branch (protos: `~/w/protos`, `master`) | everywhere; `wtsurvey` takes the first entry of `git worktree list` as the trunk |
| Where the other worktrees are and what their home branches are called (protos: `~/w/wt_protos/<name>`, branch `<name>`) | Steps 2 and 6; `wtsurvey` assumes the home branch is named after the directory |
| Which worktrees take part | `--only` (or `--exclude` for the ones that never do) |
| The test command after a merge, and the full check at the end | Steps 5 and 10 |
| Whether and where migrations run | Step 8 |
| Which automated runs cost money | Step 10 |
| Rules for pushing (protos pushes through a pre-push hook and pull requests) | the push question in Step 10 |
| Whether the trunk is protected (commits on it need the user's OK) | Steps 5 and 6 |
| How to keep the tests off a shared test database, if there is one | Steps 1, 5 and 10 |
| Collisions that this repository is known for | Step 5, point 6 |
| How the dev server is started, and for which user, for browser QA | Step 10 |
