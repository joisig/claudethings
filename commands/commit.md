---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
description: Create a git commit using my rules
---

## Context

- Current git status: !`git status`
- Current git diff (staged and unstaged changes): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`

## Your task

Based on the above changes, create a single git commit with a sensible message. The first
line should be a concise summary (or highlight the most important change and say "and more"
at the end) and should be 80 characters or less, followed by a blank line, followed by
the rest of the commit description if needed.

Preview the commit and then push it.

Do not include a "co-authored by Claude" or any other references to Claude the tool (although if the CLAUDE.md file or similar is being modified, you can mention that if it's relevant).

If the project directory is 'protos' or is part of the CrankWheel organization on GitHub, make sure the author is "Joi Sigurdsson <joi@crankwheel.com>"
If the project directory is under ~/q, ~/w, ~/p, ~/c or ~/snilli make sure the author is "Joi Sigurdsson <joi@quarter.is>"
For other project directories, ask me