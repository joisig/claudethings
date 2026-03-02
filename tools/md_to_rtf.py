#!/usr/bin/env python3
"""
Convert Markdown to RTF and place on macOS clipboard as rich text.

The generated RTF uses proper list table structures (\listtable,
\listoverridetable, \ls, \ilvl) so that when pasted into Google Docs
via macOS, Cocoa converts the RTF to <ul>/<li> HTML and Google Docs
creates native bullet lists.

Usage:
    md_to_rtf.py input.md                # copies to clipboard
    md_to_rtf.py input.md output.rtf     # writes file AND copies to clipboard
    md_to_rtf.py input.md --no-clipboard # writes file only (output.rtf)
    cat notes.md | md_to_rtf.py -        # reads stdin, copies to clipboard
"""

import sys
import re
import os
import tempfile
import subprocess


def escape_rtf(text):
    """Escape RTF special characters: backslash, braces."""
    text = text.replace("\\", "\\\\")
    text = text.replace("{", "\\{")
    text = text.replace("}", "\\}")
    return text


def process_inline(text):
    """Process bold (**text**) and return RTF with inline formatting."""
    parts = re.split(r"(\*\*.*?\*\*)", text)
    result = ""
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            inner = escape_rtf(part[2:-2])
            result += "{\\b " + inner + "}"
        else:
            result += escape_rtf(part)
    # Unicode: emit \uN with a plain-ASCII fallback byte after it
    for char, code in [
        ("\u2014", 8212),  # em dash
        ("\u2013", 8211),  # en dash
        ("\u00f3", 0xF3),  # ó
        ("\u00ed", 0xED),  # í
        ("\u00e9", 0xE9),  # é
        ("\u00e1", 0xE1),  # á
        ("\u00fa", 0xFA),  # ú
        ("\u00f1", 0xF1),  # ñ
        ("\u00fc", 0xFC),  # ü
    ]:
        if char in result:
            result = result.replace(char, f"\\uc0\\u{code} ")
    return result


# ---------------------------------------------------------------------------
# RTF list table boilerplate.  Two levels: disc (level 0), circle (level 1).
# The {\*\levelmarker ...} is an Apple/Cocoa extension that tells the
# NSAttributedString RTF importer which CSS list-style-type to use when
# converting to HTML for the clipboard — this is what makes Google Docs
# see native <ul>/<li> elements on paste.
# ---------------------------------------------------------------------------
RTF_LIST_TABLES = (
    "{\\*\\listtable{\\list\\listtemplateid1\\listhybrid\n"
    "{\\listlevel\\levelnfc23\\leveljc0\\levelstartat1\\levelfollow0\n"
    "{\\*\\levelmarker \\{disc\\}}\n"
    "{\\leveltext\\'01\\uc0\\u8226;}{\\levelnumbers;}\\fi-360\\li720}\n"
    "{\\listlevel\\levelnfc23\\leveljc0\\levelstartat1\\levelfollow0\n"
    "{\\*\\levelmarker \\{circle\\}}\n"
    "{\\leveltext\\'01\\uc0\\u9702;}{\\levelnumbers;}\\fi-360\\li1440}\n"
    "{\\listname ;}\\listid1}}\n"
    "{\\*\\listoverridetable{\\listoverride\\listid1\\listoverridecount0\\ls1}}\n"
)


def md_to_rtf(md_text):
    lines = md_text.split("\n")
    rtf_body = []
    in_list = False  # track whether we're inside a bullet sequence

    for line in lines:
        stripped = line.rstrip()
        raw_stripped = stripped.lstrip()

        # Blank line
        if not raw_stripped:
            if in_list:
                in_list = False
            rtf_body.append("\\pard\\par")
            continue

        # Heading 1: # Title
        if raw_stripped.startswith("# ") and not raw_stripped.startswith("## "):
            in_list = False
            content = process_inline(raw_stripped[2:])
            rtf_body.append(
                "{\\pard\\sb400\\sa200\\f0\\fs40\\b " + content + "\\b0\\par}"
            )
            continue

        # Heading 2: ## Title
        if raw_stripped.startswith("## "):
            in_list = False
            content = process_inline(raw_stripped[3:])
            rtf_body.append(
                "{\\pard\\sb300\\sa120\\f0\\fs32\\b " + content + "\\b0\\par}"
            )
            continue

        # Bullet: starts with * or - (with possible leading spaces)
        bullet_match = re.match(r"^(\s*)[*\-]\s+(.*)", stripped)
        if bullet_match:
            in_list = True
            indent_spaces = len(bullet_match.group(1))
            content = process_inline(bullet_match.group(2))
            if indent_spaces >= 2:
                # Sub-bullet (ilvl1)
                rtf_body.append(
                    "{\\pard\\ls1\\ilvl1\\fi-360\\li1440\\f0\\fs24\\sb40\\sa40 "
                    + content + "\\par}"
                )
            else:
                # Top-level bullet (ilvl0)
                rtf_body.append(
                    "{\\pard\\ls1\\ilvl0\\fi-360\\li720\\f0\\fs24\\sb80\\sa40 "
                    + content + "\\par}"
                )
            continue

        # Plain paragraph
        in_list = False
        content = process_inline(raw_stripped)
        rtf_body.append("{\\pard\\f0\\fs24\\sb60\\sa60 " + content + "\\par}")

    rtf = (
        "{\\rtf1\\ansi\\ansicpg1252\\deff0\n"
        "{\\fonttbl{\\f0\\fswiss\\fcharset0 Helvetica Neue;}}\n"
        "{\\colortbl;\\red0\\green0\\blue0;}\n"
        + RTF_LIST_TABLES
        + "\\f0\\fs24\n"
    )
    rtf += "\n".join(rtf_body)
    rtf += "\n}"
    return rtf


def copy_rtf_to_clipboard(rtf_string, plain_text):
    """Place RTF and plain text on the macOS clipboard using PyObjC."""
    try:
        from AppKit import NSPasteboard, NSData, NSPasteboardTypeString

        rtf_data = rtf_string.encode("ascii", errors="replace")
        ns_rtf_data = NSData.dataWithBytes_length_(rtf_data, len(rtf_data))

        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        pb.setData_forType_(ns_rtf_data, "public.rtf")
        pb.setString_forType_(plain_text, NSPasteboardTypeString)
        return True
    except ImportError:
        # Fallback: write RTF to temp file, use osascript to set clipboard
        return copy_rtf_to_clipboard_fallback(rtf_string, plain_text)


def copy_rtf_to_clipboard_fallback(rtf_string, plain_text):
    """Fallback clipboard method using osascript + textutil."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".rtf", mode="w", delete=False) as f:
            f.write(rtf_string)
            tmp_path = f.name
        # Convert RTF to HTML, then set clipboard via osascript
        html_result = subprocess.run(
            ["textutil", "-convert", "html", "-stdout", tmp_path],
            capture_output=True, text=True
        )
        if html_result.returncode == 0:
            html = html_result.stdout
            # Use hex-encoded HTML data for osascript
            hex_html = html.encode("utf-8").hex()
            apple_script = (
                f'set the clipboard to '
                f'{{text:"{plain_text[:200]}...", '
                f'«class HTML»:«data HTML{hex_html}»}}'
            )
            subprocess.run(["osascript", "-e", apple_script], capture_output=True)
        os.unlink(tmp_path)
        return True
    except Exception:
        return False


def strip_markdown(md_text):
    """Produce a plain-text version by stripping markdown formatting."""
    text = md_text
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # bold
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)  # headings
    return text


def main():
    args = sys.argv[1:]
    no_clipboard = "--no-clipboard" in args
    args = [a for a in args if a != "--no-clipboard"]

    if len(args) < 1:
        print(__doc__.strip())
        sys.exit(1)

    input_path = args[0]
    if input_path == "-":
        md_text = sys.stdin.read()
        output_path = args[1] if len(args) > 1 else None
    else:
        with open(input_path, "r") as f:
            md_text = f.read()
        if len(args) > 1:
            output_path = args[1]
        else:
            output_path = None

    rtf = md_to_rtf(md_text)

    if output_path:
        with open(output_path, "w") as f:
            f.write(rtf)
        print(f"Written to {output_path}")

    if not no_clipboard:
        plain = strip_markdown(md_text)
        if copy_rtf_to_clipboard(rtf, plain):
            print("Rich text copied to clipboard — paste into Google Docs with Cmd+V")
        else:
            # Last resort: write file if we haven't already
            if not output_path:
                fallback_path = "/tmp/release_notes.rtf"
                with open(fallback_path, "w") as f:
                    f.write(rtf)
                print(f"Could not access clipboard. Written to {fallback_path}")
    elif not output_path:
        # --no-clipboard and no output file: write to default location
        default_path = os.path.splitext(input_path)[0] + ".rtf" if input_path != "-" else "/tmp/release_notes.rtf"
        with open(default_path, "w") as f:
            f.write(rtf)
        print(f"Written to {default_path}")


if __name__ == "__main__":
    main()
