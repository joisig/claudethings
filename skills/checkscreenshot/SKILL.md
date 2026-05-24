---
allowed-tools: Bash(~/p/claudethings/tools/checkscreenshot.py:*), Read(/tmp/screenshots-for-claude/*.png), Read(/tmp/screenshots-for-claude/*.jpg), Read(/tmp/screenshots-for-claude/*.jpeg)
description: Add the last N screenshots to context
---

# checkscreenshot

Allows you (Claude) to take a look at the latest N screenshots in ~/Desktop where N is an optional parameter that defaults to 1.

The script copies screenshots to /tmp/screenshots-for-claude/ so they are accessible inside a sandbox.

## Usage
- `/checkscreenshot` - Take a look at latest screenshot
- `/checkscreenshot 3` - Take a look at the latest 3 screenshots

## Implementation

1. Run `~/p/claudethings/tools/checkscreenshot.py N` (where N is the parameter, default 1)
2. Parse the output to get the file paths (these will be in /tmp/screenshots-for-claude/)
3. For each file path:
   - Use the Read tool to look at the file and add it to context, then ask the user for more details about your task
