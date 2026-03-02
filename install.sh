#!/bin/bash
#
# install.sh - Install Claude Code skills from claudethings
#
# Skills installed:
# - bear-notes: Read and search Bear notes
# - clipboard-markdown: Copy markdown to clipboard as plain text
# - clipboard-richtext: Copy markdown to clipboard as rich text (for Google Docs)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

echo "Installing claudethings skills for Claude Code..."

# ---------------------------------------------------------------------------
# 1. Make tools executable
# ---------------------------------------------------------------------------
echo "Making tools executable..."
chmod +x "$SCRIPT_DIR/bear_reader.py"
chmod +x "$SCRIPT_DIR/tools/md_to_clipboard.py"
chmod +x "$SCRIPT_DIR/tools/md_to_rtf.py"

# ---------------------------------------------------------------------------
# 2. Create skill directories and symlinks
# ---------------------------------------------------------------------------
echo "Linking skills..."

for skill in bear-notes clipboard-markdown clipboard-richtext; do
    skill_dir="$CLAUDE_DIR/skills/$skill"
    mkdir -p "$skill_dir"
    rm -f "$skill_dir/SKILL.md"
    ln -s "$SCRIPT_DIR/skills/$skill/SKILL.md" "$skill_dir/SKILL.md"
    echo "  $skill -> $skill_dir/SKILL.md"
done

# ---------------------------------------------------------------------------
# 3. Backup and update settings.json with permissions
# ---------------------------------------------------------------------------
echo "Updating Claude Code permissions..."

if [ -f "$SETTINGS_FILE" ]; then
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.bak"
    echo "  Backed up settings.json to settings.json.bak"
fi

python3 << 'PYTHON_SCRIPT'
import json
import os

settings_file = os.path.expanduser("~/.claude/settings.json")
tools_dir = os.path.expanduser("~/p/claudethings/tools")
bear_reader = os.path.expanduser("~/p/claudethings/bear_reader.py")

# Permissions to add
new_permissions = [
    # bear-notes
    "Read(/tmp/bearnotes/**)",
    "Write(/tmp/bearnotes/**)",
    "Edit(/tmp/bearnotes/**)",
    "Bash(mkdir -p /tmp/bearnotes)",
    f"Bash(python {bear_reader}:*)",
    f"Bash({bear_reader}:*)",
    "Skill(bear-notes)",
    # clipboard-markdown
    f"Bash({tools_dir}/md_to_clipboard.py:*)",
    "Skill(clipboard-markdown)",
    # clipboard-richtext
    f"Bash({tools_dir}/md_to_rtf.py:*)",
    "Skill(clipboard-richtext)",
    # shared temp file
    "Write(/tmp/clipboard_content.md)",
]

# Read existing settings
settings = {}
if os.path.exists(settings_file):
    try:
        with open(settings_file, 'r') as f:
            settings = json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: Could not parse {settings_file}, starting fresh")
        settings = {}

# Ensure permissions structure exists
if "permissions" not in settings:
    settings["permissions"] = {}
if "allow" not in settings["permissions"]:
    settings["permissions"]["allow"] = []

# Add new permissions (avoid duplicates)
existing = set(settings["permissions"]["allow"])
for perm in new_permissions:
    if perm not in existing:
        settings["permissions"]["allow"].append(perm)
        print(f"  Added: {perm}")
    else:
        print(f"  Already exists: {perm}")

# Write updated settings
with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)

print(f"Updated {settings_file}")
PYTHON_SCRIPT

# ---------------------------------------------------------------------------
# 4. Create working directories
# ---------------------------------------------------------------------------
echo "Creating working directories..."
mkdir -p /tmp/bearnotes

echo ""
echo "Installation complete!"
echo ""
echo "Skills installed:"
echo "  - bear-notes:          Read and search Bear notes"
echo "  - clipboard-markdown:  Copy markdown to clipboard as plain text"
echo "  - clipboard-richtext:  Copy markdown to clipboard as rich text"
echo ""
echo "Tools:"
echo "  - $SCRIPT_DIR/bear_reader.py"
echo "  - $SCRIPT_DIR/tools/md_to_clipboard.py"
echo "  - $SCRIPT_DIR/tools/md_to_rtf.py"
echo ""
echo "Try: 'Copy this to my clipboard' or 'Put this on clipboard as rich text for Google Docs'"
