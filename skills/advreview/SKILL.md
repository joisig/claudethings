---
name: advreview
description: Get an adversarial review from Codex (newest astra model) of what we are working on - the pending code changes, the feature branch against its base, or the plan document in plan mode - then act on the feedback. Use when the user types /advreview or asks for an adversarial or second-opinion review. Also run it without being asked in the cases the global CLAUDE.md lists (first version of a plan; major code changes before reporting them ready).
---

# advreview — adversarial review by Codex

An independent reviewer (Codex, newest "astra" model) looks at the work with no
knowledge of our conversation. You then handle its feedback with the user.

## Tool

```bash
/Users/joi/.claude/skills/advreview/bin/advreview <mode> [argument]
```

Always use that absolute path. Run it from the repository root.

| Mode | What Codex reviews |
|---|---|
| `uncommitted` | Staged, unstaged and untracked changes (Codex `/review`, uncommitted) |
| `base <branch>` | The current branch against `<branch>` (Codex `/review`, against a base) |
| `plan <file>` | The plan or design document at `<file>`, checked against the repository |

A review takes several minutes. Run the tool with `run_in_background: true` and wait
for the notification. Do not poll.

The tool finds the model itself: the newest one in Codex's catalog whose name contains
"astra". It prints the model on the first line of its output.

## Step 1 — choose what to review

1. **Plan mode, or the work is a plan document:** `plan <path to the plan file>`.
2. **Code on a protected branch** (the default branch, a long-lived shared or worktree
   branch, a release branch; the project's instructions and memory say which): the
   work is not committed there, so use `uncommitted`.
3. **Code on a feature branch:** first commit pending changes with the user's commit
   skill (`/commit`). Do not push. Then use `base <branch>`, where `<branch>` is the
   branch the feature branch was cut from. If you do not know it, use the repository's
   main branch.
4. **Anything else** (a design document, other prose): `plan <file>` on that file.

If nothing has changed since the last review of the same thing, say so and do not run
it again.

## Step 2 — give the reviewer no context

The reviewer starts fresh on purpose. Do not add a summary, the reasons for a
decision, or a list of known limits. The tool sends only the review request, and it
has no option for more. Do not work around that.

## Step 3 — handle the feedback

Read the whole review. Check each point against the code or the plan before you act;
the reviewer lacks our context and can be wrong. Then, for each point:

- **Correct and cheap to fix:** fix it.
- **Wrong, or already covered by something the reviewer could not know:** do not
  change anything. Tell the user in one line why.
- **You are not sure:** ask the user.
- **Correct, but the fix adds complexity** (new state, a new mechanism, more
  configuration): do not just add it. The user prefers to keep things simple. Find
  the reasonable tradeoffs, such as a narrower scope, removal of the feature that
  causes the problem, or acceptance of a documented limit. Show the tradeoff, or the
  several tradeoffs, and let the user judge whether to go with one of those, or accept the complexity.
- **Detect complexity spirals**: If you see that multiple review rounds keep poking
  at the same area (usually state management or TOCTTOU or similar issues), flag it
  to the user, again proposing tradeoffs we might make and let the user judge. 

Use `AskUserQuestion` for the questions and tradeoffs. Group them in one call when
you can.

After that, tell the user briefly: what the reviewer found, what you changed, what
you did not change and why. For a plan, update the plan file before you show it.

## When it cannot run

- `advreview-listen is not running`: this session is in a sandbox that cannot read
  `~/.codex`, and the listener that runs Codex outside the sandbox is not started. Ask
  the user to start `~/p/claudethings/tools/dev-services` (or
  `~/.claude/skills/advreview/bin/advreview-listen`) in a normal terminal. Then try
  again.
- `no astra model in the Codex catalog`: show the user the model list from the error.
  `ADVREVIEW_MODEL=<slug>` overrides the choice. It is read where Codex runs, so in a
  sandboxed session the user must set it for the listener, not for your command.
- A network or permission error in the standard Claude Code sandbox: run the tool
  again with the sandbox disabled.

Do not replace a failed review with your own review, and do not report that a review
was done when it was not.
