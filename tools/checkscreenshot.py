#!/usr/bin/env python3
"""
Check and display the latest screenshots from ~/Desktop.
Copies them to /tmp/screenshots-for-claude/ so sandboxed agents can read them.
Designed to work with Claude Code's checkscreenshot command.
"""

import os
import sys
import glob
import shutil
from pathlib import Path
from datetime import datetime
import argparse

STAGING_DIR = "/tmp/screenshots-for-claude"

def find_screenshots(desktop_path, count=1):
    """Find the most recent screenshot files in the Desktop folder."""

    # Common screenshot patterns on macOS
    patterns = [
        "Screenshot*.png",
        "Screen Shot*.png",
        "Screen Recording*.png",
        "Capture*.png",
        "*.jpg",  # Sometimes screenshots are saved as jpg
        "*.jpeg"
    ]

    # Find all matching files
    all_screenshots = []
    for pattern in patterns:
        files = glob.glob(os.path.join(desktop_path, pattern))
        all_screenshots.extend(files)

    # Also check for any PNG files that might be screenshots
    all_pngs = glob.glob(os.path.join(desktop_path, "*.png"))
    all_screenshots.extend(all_pngs)

    # Remove duplicates and sort by modification time (newest first)
    unique_screenshots = list(set(all_screenshots))
    unique_screenshots.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    # Return the requested number of screenshots
    return unique_screenshots[:count]

def copy_to_staging(screenshots):
    """Copy screenshots to the staging directory for sandbox access."""
    os.makedirs(STAGING_DIR, exist_ok=True)

    # Clean out old files
    for old_file in glob.glob(os.path.join(STAGING_DIR, "*")):
        os.remove(old_file)

    staged_paths = []
    for filepath in screenshots:
        dest = os.path.join(STAGING_DIR, os.path.basename(filepath))
        shutil.copy2(filepath, dest)
        staged_paths.append(dest)

    return staged_paths

def format_file_info(filepath):
    """Format file information for display."""
    stat = os.stat(filepath)
    mod_time = datetime.fromtimestamp(stat.st_mtime)
    size_mb = stat.st_size / (1024 * 1024)

    return {
        'path': filepath,
        'filename': os.path.basename(filepath),
        'modified': mod_time.strftime('%Y-%m-%d %H:%M:%S'),
        'size_mb': f"{size_mb:.2f}"
    }

def main():
    parser = argparse.ArgumentParser(description='Find and display recent screenshots')
    parser.add_argument('count', type=int, nargs='?', default=1,
                       help='Number of screenshots to display (default: 1)')
    parser.add_argument('--json', action='store_true',
                       help='Output in JSON format')

    args = parser.parse_args()

    # Get Desktop path
    desktop_path = os.path.expanduser("~/Desktop")

    if not os.path.exists(desktop_path):
        print(f"Error: Desktop folder not found at {desktop_path}", file=sys.stderr)
        sys.exit(1)

    # Find screenshots
    screenshots = find_screenshots(desktop_path, args.count)

    if not screenshots:
        print("No screenshots found in ~/Desktop")
        sys.exit(0)

    # Copy to staging dir for sandbox access
    staged_paths = copy_to_staging(screenshots)

    # Output results using staged paths
    if args.json:
        import json
        results = [format_file_info(f) for f in staged_paths]
        print(json.dumps(results, indent=2))
    else:
        print(f"Found {len(staged_paths)} recent screenshot(s), copied to {STAGING_DIR}:\n")
        for i, filepath in enumerate(staged_paths, 1):
            info = format_file_info(filepath)
            print(f"{i}. {info['filename']}")
            print(f"   Path: {info['path']}")
            print(f"   Modified: {info['modified']}")
            print(f"   Size: {info['size_mb']} MB")
            print()

if __name__ == "__main__":
    main()
