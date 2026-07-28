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

`daylog` combines Google Calendar and sent mail (via `gog`), git commits across
my repos, GitHub activity, and my Bear WPlan/DPlan notes. Repos and accounts are
configured in `skills/daylog/config.sh`; Google authorization is per-account and
documented in `skills/daylog/reference/google-accounts-setup.md`.
