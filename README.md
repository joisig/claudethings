Random tools I use with Claude.

Run `./install.sh` to symlink the skills into `~/.claude/skills` and add the
matching permissions to `~/.claude/settings.json`.

| Skill | What it does |
|---|---|
| `bear-notes` | Read and search Bear notes (read-only) |
| `clipboard-markdown` | Copy markdown to the clipboard as plain text |
| `clipboard-richtext` | Copy markdown to the clipboard as rich text, for Google Docs |
| `checkscreenshot` | Pull the latest screenshots from ~/Desktop into context |
| `daylog` | Reconstruct what I was doing on a given day or week |
| `advreview` | Adversarial review by Codex (newest astra model) of the current code changes or plan |
| `visualexplain` | Draw a plan, a code change or a subsystem as a local HTML page on a pan-and-zoom canvas |
| `wtconsolidate` | Merge finished work from a repo's parallel worktrees into main, then write a test plan (linked into bboo only) |

`daylog` combines Google Calendar and sent mail (via `gog`), git commits across
my repos, GitHub activity, and my Bear WPlan/DPlan notes. Repos and accounts are
configured in `skills/daylog/config.sh`; Google authorization is per-account and
documented in `skills/daylog/reference/google-accounts-setup.md`.

`advreview` runs `codex review` (uncommitted changes, or the branch against its base)
or reviews a plan document. Codex needs `~/.codex`. A session in a sandbox that cannot
read it sends the request to `skills/advreview/bin/advreview-listen`, which
`tools/dev-services` starts outside the sandbox. The rules for when Claude runs it
without being asked are in `~/.claude/CLAUDE.md`.

`visualexplain` writes one HTML file to the `tmp/<date>-<subject>/` folder of the repo
it runs in (or to the session scratchpad when `tmp/` is not git-ignored there). The
page links the canvas shell, `skills/visualexplain/canvas.css` and `canvas.js`, by
absolute `file://` URL through `~/.claude/skills`, so a page works on this machine
only. Simple diagrams are Mermaid: `skills/visualexplain/bin/visualexplain
mermaid-cache <repo>/tmp` keeps a copy of the library in `<repo>/tmp/visualexplain/`
(downloaded again after 30 days), and the page falls back to the jsDelivr CDN.
`skills/visualexplain/example.html` is the reference page and the test page for the
shell. The rule for when Claude builds a page without being asked is in
`~/.claude/CLAUDE.md`.

`wtconsolidate` is not installed globally. `install.sh` links it into
`~/q/bboo/main/.claude/skills`, so it is run from a session in that worktree. Its
read-only helper, `skills/wtconsolidate/bin/wtsurvey`, reports each worktree's state,
its Claude Code sessions and the predicted merge conflicts. To use the skill in
another repo, link it there the same way and see "Other repositories" in its SKILL.md.

`global/CLAUDE.md` is my global instructions file. `install.sh` links it to
`~/.claude/CLAUDE.md`. `commands/commit.md` is my `/commit` command, linked to
`~/.claude/commands/commit.md` in the same way.
