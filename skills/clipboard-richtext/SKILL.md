---
name: clipboard-richtext
description: Copy markdown to the macOS clipboard as rich text, formatted for pasting into Google Docs. Use when the user wants rich text on clipboard, formatted clipboard content, or says "copy as rich text" or "for Google Docs".
---

# Clipboard — Rich Text

Converts markdown to RTF and places it on the macOS clipboard as rich text. When pasted into Google Docs, it produces native headings, bold text, and bullet lists.

## Tool Location

```bash
/Users/joi/p/claudethings/tools/md_to_rtf.py
```

Always launch the tool using that path. Do not put `python3` in front. This allows the user to "always allow" invocations of just that particular file.

## Workflow

1. Write the content to `/tmp/clipboard_content.md`
2. Run the tool on it:
   ```bash
   /Users/joi/p/claudethings/tools/md_to_rtf.py /tmp/clipboard_content.md
   ```
3. Tell the user: **"Rich text is on your clipboard — paste into Google Docs with Cmd+V."**

## Usage

```bash
# Convert file and copy to clipboard
/Users/joi/p/claudethings/tools/md_to_rtf.py /tmp/clipboard_content.md

# Also write an RTF file
/Users/joi/p/claudethings/tools/md_to_rtf.py /tmp/clipboard_content.md output.rtf

# Read from stdin
cat file.md | /Users/joi/p/claudethings/tools/md_to_rtf.py -
```

## Supported Formatting

- **Headings**: `# H1` and `## H2` — rendered as large bold text with spacing
- **Bold**: `**text**` — rendered as bold inline
- **Bullets**: `- item` or `* item` — rendered as native bullet lists (disc marker)
- **Sub-bullets**: Indent with 2+ spaces — rendered as second-level bullets (circle marker)
- **Paragraphs**: Plain text lines — rendered as normal paragraphs

## Dependencies

Uses PyObjC (`AppKit`) for clipboard access. Falls back to `textutil` + `osascript` if PyObjC is unavailable.
