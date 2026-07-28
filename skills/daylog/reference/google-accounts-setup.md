# Google account setup for daylog

`daylog google` reads calendar events and sent mail through the `gog` CLI. Each
account must be authorized once. Everything else in the skill works without it.

The OAuth client lives in Google Cloud project **`gog-auth-joi`**:
<https://console.cloud.google.com/auth/audience?project=gog-auth-joi>

## The two things that break this

### 1. Test users (causes `Error 403: access_denied`)

The app's publishing status is **Testing** with user type **External**, so only
accounts listed under *Audience → Test users* can authorize. Any other account
fails with:

> gog has not completed the Google verification process… can only be accessed by
> developer-approved testers. **Error 403: access_denied**

Fix: add the account under *Audience → Test users → Add users* and Save. The cap
is 100 users, counted over the app's lifetime.

### 2. The 7-day refresh-token expiry (causes `invalid_grant`)

**While publishing status is "Testing", Google expires refresh tokens after 7
days.** This is why an account that worked last week starts failing with
`invalid_grant` / "Token has been expired or revoked" — nothing was revoked, the
token simply aged out. Left in Testing, every account needs re-authorizing
roughly weekly.

Fix: click **Publish app** on the Audience page. In production the 7-day expiry
no longer applies. Because the app is unverified you will see a "Google hasn't
verified this app" screen once per account — proceed via *Advanced → Go to gog
(unsafe)*. Verification is only needed to remove that warning or to go past 100
users, neither of which matters for personal use.

If Google refuses to issue the restricted Gmail scope to an unverified
production app, the fallback is to stay in Testing and re-authorize weekly, or
to drop `gmail` from `--services` and run calendar-only.

**"Make internal" is not an option here** — internal restricts the app to a
single Workspace organization, and these five accounts span five different
domains.

## Authorizing an account

Each command opens a browser for Google's consent screen, so run it yourself —
in Claude Code, prefix with `!` so the output lands in the session:

```
gog auth add joi@crankwheel.com --services calendar,gmail --readonly
gog auth add joi@quarter.is --services calendar,gmail --readonly
gog auth add joi@bellabooksai.com --services calendar,gmail --readonly
gog auth add joi@grosvenor-holdings.com --services calendar,gmail --readonly
gog auth add joi.sigurdsson@gmail.com --services calendar,gmail --readonly
```

`--readonly` keeps the skill unable to send mail or modify the calendar even by
accident. Re-authorizing an expired account uses the same command; it replaces
the stored refresh token in place. `gog` keys tokens by account email, so all
accounts coexist under one OAuth client and `-a <email>` selects between them.

Verify with:

```
gog auth list
/Users/joi/.claude/skills/daylog/bin/daylog google yesterday
```

`daylog google` prints the exact command needed for whichever accounts are not
working, so running it is the quickest way to see current state.

## Which calendars get read

`joi@crankwheel.com` has owner rights on colleagues' calendars (e.g.
`artem@crankwheel.com`), so reading *all* calendars would report their meetings
as Joi's. `GOOGLE_CALENDARS=(auto)` in `config.sh` therefore keeps only:

- calendars whose ID is one of `GOOGLE_ACCOUNTS`
- `@group.calendar.google.com` calendars Joi owns (Work Reminders, Family
  Calendar, Jói's reminders, Savvycal slots)

and drops colleagues, meeting rooms (`faxifundarherbergi@`), holiday feeds and
read-only subscriptions. Set `GOOGLE_CALENDARS=(all)` to disable the filter, or
list explicit calendar IDs.

Note that the crankwheel account's calendar list already includes the other four
accounts' calendars, so some cross-account events are visible even before those
accounts are individually authorized. Gmail always requires per-account auth.

## Troubleshooting

**Keyring or "ensure keyring dir" errors** — `gog` keeps its config under
`~/Library/Application Support/gogcli`, which macOS protects. If the shell
running Claude Code lacks Full Disk Access, every `gog` call fails before it
reaches the network. Grant Full Disk Access to the terminal app (System
Settings → Privacy & Security → Full Disk Access), or point `gog` at a readable
root with `export GOG_HOME=/Users/joi/.claude/gogcli-home`.

The same restriction affects Bear: `bear_reader.py` reads
`~/Library/Group Containers/…/database.sqlite`, so a shell without Full Disk
Access reports "Bear database not found" even though the file exists.

## Scope of what is collected

- **Calendar** — events overlapping the range, from the calendars selected
  above. Attendance is not filtered: a declined or skipped meeting still appears,
  so treat events as *scheduled* and prefer sent mail or commits as evidence of
  what actually happened.
- **Sent mail** — message-level (`gmail messages search`), not thread-level, so
  each message carries its own date and sender. Subject/recipient metadata only.
- **Received mail** — only with `--received`; promotions and social are
  excluded. Off by default because volume drowns the signal.
