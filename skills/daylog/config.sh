# daylog configuration — edit this file to add repos, accounts or identities.

# Local git repos to scan. One entry per repo root; worktrees are covered
# automatically because they share the repo's object database (`git log --all`).
REPOS=(
  /Users/joi/w/protos
  /Users/joi/w/cwcompliance
  /Users/joi/w/crankwheel.com
  /Users/joi/q/bboo/main
  /Users/joi/c/somatic
  /Users/joi/snilli/k/kloi
  /Users/joi/q/cardinal
  /Users/joi/p/claudethings
)

# Commit author emails that count as "Joi's work".
# kloi@agent.local is Joi's agent committing on his behalf — it is included but
# tagged as agent work in the output so it can be told apart.
AUTHORS=(
  joi@crankwheel.com
  joi@quarter.is
  kloi@agent.local
)
AGENT_AUTHORS=(
  kloi@agent.local
)

GITHUB_USER=joisig

# Google accounts to pull sent mail + calendar from, in priority order.
# An account only works once `gog auth add <email>` has been run for it —
# see reference/google-accounts-setup.md.
GOOGLE_ACCOUNTS=(
  joi@crankwheel.com
  joi@quarter.is
  joi@bellabooksai.com
  joi.sigurdsson@gmail.com
  joi@grosvenor-holdings.com
)

# Which calendars to read per account. "auto" keeps Joi's own calendars and
# drops other people's and subscribed feeds — he has owner rights on colleagues'
# calendars (e.g. artem@crankwheel.com), so their events would otherwise show up
# as his. Set to "all" to include everything, or list explicit calendar IDs.
GOOGLE_CALENDARS=(auto)

BEAR_READER=/Users/joi/p/claudethings/bear_reader.py

# AI coding sessions. Claude Code writes one JSONL transcript per session under
# <projects>/<encoded-cwd>/, with sub-agent transcripts in a subagents/ subdir;
# Codex writes rollout-*.jsonl under <sessions>/YYYY/MM/DD/.
CLAUDE_PROJECTS_DIR=~/.claude/projects
CODEX_SESSIONS_DIR=~/.codex/sessions
