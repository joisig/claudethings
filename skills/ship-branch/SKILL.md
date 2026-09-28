---
name: ship-branch
description: For the CrankWheel protos repo and its worktrees. Ship the current work as a pull request for review, then hand the branch off for testing in another worktree. Puts the work on a joi-* feature branch, commits anything uncommitted, pushes, opens a PR with gitradik as reviewer, comments which milestone it is for and that Jói will comment again after local testing, and switches this worktree back to its home branch. Use when the user asks to "ship this", "check out a feature branch, commit, push and make a PR", or similar. Takes an optional milestone name (e.g. M182).
---

# ship-branch

Take the work in this worktree to an open pull request, then free the feature
branch so it can be checked out in another worktree for testing.

## Usage

- `/ship-branch M182` — the PR comment says the work is for M182.
- `/ship-branch` — no milestone; the PR comment only says that Jói will
  comment again after local testing.

## Where we might start

Any step whose result already exists is skipped:

- on the worktree's home branch with uncommitted changes (the full flow);
- already on a `joi-*` feature branch, with or without uncommitted changes;
- everything committed, but not yet pushed;
- pushed, and a PR may or may not exist yet.

## Steps

### 1. Find the home branch

Each worktree under `~/w/wt_protos/<name>` has a home branch named `<name>`
(for example `second`). The main checkout, `~/w/protos`, has `master`. Get
the name with `basename "$(git rev-parse --show-toplevel)"`. If no branch
with that name exists, ask the user which branch to go back to.

### 2. Get onto a feature branch

- If the current branch starts with `joi-`, stay on it.
- If the current branch is the home branch or `master`, create
  `joi-<short-kebab-description-of-the-change>` from the current HEAD with
  `git checkout -b`. Uncommitted changes carry over.
- Any other branch: ask the user before going on.

### 3. Commit

If there are uncommitted changes, commit them with the `commit` skill (its
rules set the author and the message). If the tree is clean, go on.

Do not commit files that are unrelated to the work (scratch files, a
`config/test.secret.exs` copied in for testing, and so on). If you are not
sure whether a file belongs, ask.

### 4. Push

The `pre-push` hook runs the whole `ss` (`mix test`) and `erlfector`
(`mix eunit`) suites for this worktree, which takes several minutes. So run
the push in the background, with the sandbox disabled. SSH push is blocked
from Claude Code, so push over HTTPS with the `gh` credential helper:

```
S=<scratchpad>
export HEX_HOME=$S/hex MIX_HOME=$S/mix REBAR_CACHE_DIR=$S/rebar3cache DEVELOPMENT_URL=joitest.crankwheel.com
git -c credential.helper='!gh auth git-credential' push -u https://github.com/CrankWheel/protos.git <branch>
```

The hook needs this worktree's own `ss/_build`, `ss/deps`,
`ss/config/test.secret.exs` and `erlfector/_build`. See the "Building and
testing" section of the repo's top-level CLAUDE.md, and the memories on
worktree builds.

The hook writes the full test output to `/tmp/ss_test_results.txt` and
`/tmp/erlfector_test_results.txt`, not to the push output. Read the totals
from there, for example
`grep -E "tests, [0-9]+ failure" /tmp/ss_test_results.txt` and
`grep "tests passed" /tmp/erlfector_test_results.txt`.

If the hook fails, stop and report the failing tests. Do not push with
`--no-verify`.

If the branch is already pushed and up to date, skip this step.

### 5. Pull request

If there is no PR for the branch yet (`gh pr view <branch>` fails), create
one against `master`:

```
gh pr create --base master --head <branch> --reviewer gitradik --title "<title>" --body-file <file>
```

- Title: the commit subject; if there are several commits, a summary of them.
- Body: a short summary of what changed and why, then how it was tested.
  Say plainly what was not tested.
- No AI attribution in the title, body or comment (see the repo's CLAUDE.md,
  "Commits and pull requests").

If a PR already exists, make sure `gitradik` is a reviewer
(`gh pr edit <n> --add-reviewer gitradik`).

### 6. Comment

Add one comment to the PR with `gh pr comment <n> --body "..."`:

- with a milestone: `This is for M182. I will comment again after it is tested locally.`
- without one: `I will comment again after this is tested locally.`

### 7. Switch back to the home branch

Run `git checkout <home branch>`. The tree must be clean first; if it is
not, stop and tell the user what is left. When this is done, the feature
branch is free to be checked out in another worktree for testing.

### 8. Report

Give the PR URL, the branch name, the result of the pre-push tests, and the
branch this worktree is now on.
