#!/bin/bash
#
# install.sh - Install Bear Notes skill for Claude Code
#
# This script:
# 1. Creates the skill directory and symlinks SKILL.md
# 2. Updates ~/.claude/settings.json with required permissions
# 3. Makes bear_reader.py executable
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
SKILLS_DIR="$CLAUDE_DIR/skills/bear-notes"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

echo "Installing Bear Notes skill for Claude Code..."

# 1. Make bear_reader.py executable
echo "Making bear_reader.py executable..."
chmod +x "$SCRIPT_DIR/bear_reader.py"

# 2. Create skill directory
echo "Creating skill directory..."
mkdir -p "$SKILLS_DIR"

# 3. Create symlink for SKILL.md (remove existing if present)
echo "Linking SKILL.md..."
rm -f "$SKILLS_DIR/SKILL.md"
ln -s "$SCRIPT_DIR/skills/bear-notes/SKILL.md" "$SKILLS_DIR/SKILL.md"

# 4. Backup and update settings.json with permissions
echo "Updating Claude Code permissions..."

# Backup existing settings.json
if [ -f "$SETTINGS_FILE" ]; then
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.bak"
    echo "  Backed up settings.json to settings.json.bak"
fi

python3 << 'PYTHON_SCRIPT'
import json
import os
import sys

settings_file = os.path.expanduser("~/.claude/settings.json")
script_dir = os.path.dirname(os.path.abspath("__file__"))

# Permissions to add
new_permissions = [
    "Read(/tmp/bearnotes/**)",
    "Write(/tmp/bearnotes/**)",
    "Edit(/tmp/bearnotes/**)",
    f"Bash(python {os.path.expanduser('~/p/claudethings/bear_reader.py')}:*)",
    f"Bash({os.path.expanduser('~/p/claudethings/bear_reader.py')}:*)",
    "Skill(bear-notes)",
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

# 5. Create /tmp/bearnotes directory
echo "Creating /tmp/bearnotes directory..."
mkdir -p /tmp/bearnotes

echo ""
echo "Installation complete!"
echo ""
echo "The following have been set up:"
echo "  - Skill installed at: $SKILLS_DIR/SKILL.md"
echo "  - Tool at: $SCRIPT_DIR/bear_reader.py"
echo "  - Permissions added to: $SETTINGS_FILE"
echo ""
echo "You can now use Claude to read your Bear notes!"
echo "Try: 'Show me my pinned Bear notes'"
