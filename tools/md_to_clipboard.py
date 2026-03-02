#!/usr/bin/env python3
"""
Copy markdown to macOS clipboard as clean plain text.

Reads a markdown file (or stdin with '-'), strips trailing whitespace
per line, and copies to clipboard via pbcopy.

Usage:
    md_to_clipboard.py input.md          # copies file to clipboard
    cat notes.md | md_to_clipboard.py -  # reads stdin, copies to clipboard
"""

import sys
import subprocess


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(1)

    input_path = sys.argv[1]
    if input_path == "-":
        text = sys.stdin.read()
    else:
        with open(input_path, "r") as f:
            text = f.read()

    # Clean up: strip trailing whitespace per line, ensure single trailing newline
    lines = [line.rstrip() for line in text.split("\n")]
    cleaned = "\n".join(lines).strip() + "\n"

    proc = subprocess.run(["pbcopy"], input=cleaned, text=True)
    if proc.returncode == 0:
        print("Markdown copied to clipboard — paste with Cmd+V.")
    else:
        print("Error: pbcopy failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
