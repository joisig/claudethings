---
name: clipboard-markdown
description: Copy text or markdown to the macOS clipboard as plain text. Use when the user wants to copy something to clipboard, put markdown on clipboard, or says "copy this to my clipboard".
---

# Clipboard — Markdown (Plain Text)

Copies markdown content to the macOS clipboard as clean plain text via `pbcopy`.

## Tool Location

```bash
/Users/joi/p/claudethings/tools/md_to_clipboard.py
```

Always launch the tool using that path. Do not put `python3` in front. This allows the user to "always allow" invocations of just that particular file.

## Workflow

1. Write the content to `/tmp/clipboard_content.md`
2. Run the tool on it:
   ```bash
   /Users/joi/p/claudethings/tools/md_to_clipboard.py /tmp/clipboard_content.md
   ```
3. Tell the user: **"Markdown is on your clipboard — paste with Cmd+V."**

## Usage

```bash
# Copy a file to clipboard
/Users/joi/p/claudethings/tools/md_to_clipboard.py /tmp/clipboard_content.md

# Read from stdin
cat file.md | /Users/joi/p/claudethings/tools/md_to_clipboard.py -
```

## What It Does

- Reads the markdown file (or stdin with `-`)
- Strips trailing whitespace per line
- Copies the cleaned text to the macOS clipboard via `pbcopy`
- No formatting conversion — the clipboard gets clean plain text
