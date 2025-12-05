#!/usr/bin/env python3
"""
bear_reader.py - Read-only access to Bear notes database

Provides safe, read-only access to the Bear note-taking app's SQLite database
and associated image files. Only SELECT queries are allowed.
"""

import argparse
import csv
import io
import json
import os
import re
import shutil
import sqlite3
import sys
from pathlib import Path


# Bear database and files locations
BEAR_DB_PATH = os.path.expanduser(
    "~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/database.sqlite"
)
BEAR_IMAGES_PATH = os.path.expanduser(
    "~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/Local Files/Note Images"
)
BEAR_FILES_PATH = os.path.expanduser(
    "~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/Local Files/Note Files"
)

# Default filters for non-deleted, non-archived, non-encrypted notes
DEFAULT_FILTERS = "ZTRASHED = 0 AND ZARCHIVED = 0 AND ZENCRYPTED = 0"


def is_safe_query(sql: str) -> bool:
    """
    Check if a SQL query is safe (read-only).
    Returns True only for SELECT statements.
    """
    # Normalize whitespace and convert to uppercase for checking
    normalized = " ".join(sql.upper().split())

    # List of forbidden SQL keywords that indicate modification
    forbidden = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
        "TRUNCATE", "REPLACE", "MERGE", "UPSERT", "ATTACH", "DETACH",
        "VACUUM", "REINDEX", "ANALYZE", "PRAGMA"  # PRAGMA can modify settings
    ]

    # Check if it starts with SELECT (after stripping whitespace)
    if not normalized.lstrip().startswith("SELECT"):
        return False

    # Check for forbidden keywords (could be in subqueries or CTEs doing modifications)
    for keyword in forbidden:
        # Match keyword as a whole word
        if re.search(rf'\b{keyword}\b', normalized):
            return False

    return True


def get_db_connection() -> sqlite3.Connection:
    """Get a read-only connection to the Bear database."""
    if not os.path.exists(BEAR_DB_PATH):
        print(f"Error: Bear database not found at {BEAR_DB_PATH}", file=sys.stderr)
        sys.exit(1)

    # Open in read-only mode using URI
    uri = f"file:{BEAR_DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def format_output(rows: list, columns: list, format_type: str) -> str:
    """Format query results in the specified format."""
    if format_type == "json":
        data = [dict(zip(columns, row)) for row in rows]
        return json.dumps(data, indent=2, default=str)

    elif format_type == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(rows)
        return output.getvalue()

    elif format_type == "text":
        if not rows:
            return ""
        # Simple text format: tab-separated
        lines = ["\t".join(columns)]
        for row in rows:
            lines.append("\t".join(str(v) if v is not None else "" for v in row))
        return "\n".join(lines)

    else:
        raise ValueError(f"Unknown format: {format_type}")


def cmd_query(args):
    """Execute a raw SELECT query."""
    sql = args.sql

    if not is_safe_query(sql):
        print("Error: Only SELECT queries are allowed", file=sys.stderr)
        sys.exit(1)

    conn = get_db_connection()
    try:
        cursor = conn.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        print(format_output(rows, columns, args.format))
    except sqlite3.Error as e:
        print(f"SQL Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


def cmd_note(args):
    """Get a note by exact title."""
    conn = get_db_connection()
    try:
        sql = f"""
            SELECT ZUNIQUEIDENTIFIER, ZTITLE, ZTEXT, ZCREATIONDATE, ZMODIFICATIONDATE
            FROM ZSFNOTE
            WHERE ZTITLE = ? AND {DEFAULT_FILTERS}
        """
        cursor = conn.execute(sql, (args.title,))
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        if not rows:
            print(f"Note not found: {args.title}", file=sys.stderr)
            sys.exit(1)

        print(format_output(rows, columns, args.format))
    finally:
        conn.close()


def cmd_search(args):
    """Search notes by title pattern (SQL LIKE pattern). Results sorted by modification date (newest first)."""
    conn = get_db_connection()
    try:
        sql = f"""
            SELECT ZUNIQUEIDENTIFIER, ZTITLE, ZMODIFICATIONDATE
            FROM ZSFNOTE
            WHERE ZTITLE LIKE ? AND {DEFAULT_FILTERS}
            ORDER BY ZMODIFICATIONDATE DESC
        """
        cursor = conn.execute(sql, (args.pattern,))
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        print(format_output(rows, columns, args.format))
    finally:
        conn.close()


def cmd_pinned(args):
    """List all pinned notes. Results sorted by modification date (newest first)."""
    conn = get_db_connection()
    try:
        # ZPINNED column indicates pinned status (1 = pinned)
        sql = f"""
            SELECT ZUNIQUEIDENTIFIER, ZTITLE, ZMODIFICATIONDATE
            FROM ZSFNOTE
            WHERE ZPINNED = 1 AND {DEFAULT_FILTERS}
            ORDER BY ZMODIFICATIONDATE DESC
        """
        cursor = conn.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        print(format_output(rows, columns, args.format))
    finally:
        conn.close()


def cmd_images(args):
    """List all images in a note."""
    conn = get_db_connection()
    try:
        # First get the note's Z_PK
        note_sql = f"""
            SELECT Z_PK FROM ZSFNOTE
            WHERE ZTITLE = ? AND {DEFAULT_FILTERS}
        """
        cursor = conn.execute(note_sql, (args.title,))
        row = cursor.fetchone()

        if not row:
            print(f"Note not found: {args.title}", file=sys.stderr)
            sys.exit(1)

        note_pk = row[0]

        # Get all files associated with this note
        files_sql = """
            SELECT ZUNIQUEIDENTIFIER, ZFILENAME
            FROM ZSFNOTEFILE
            WHERE ZNOTE = ? AND ZUNUSED = 0
        """
        cursor = conn.execute(files_sql, (note_pk,))
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        # Filter to image files only
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.heic', '.tiff', '.bmp'}
        image_rows = []
        for row in rows:
            filename = row[1] if row[1] else ""
            ext = os.path.splitext(filename)[1].lower()
            if ext in image_extensions:
                image_rows.append(row)

        print(format_output(image_rows, columns, args.format))
    finally:
        conn.close()


def cmd_image(args):
    """Read an image file by guid and filename."""
    guid = args.guid
    filename = args.filename

    # Construct the path
    image_path = os.path.join(BEAR_IMAGES_PATH, guid, filename)

    # Also check in files path if not found in images
    if not os.path.exists(image_path):
        image_path = os.path.join(BEAR_FILES_PATH, guid, filename)

    if not os.path.exists(image_path):
        print(f"Image not found: {guid}/{filename}", file=sys.stderr)
        sys.exit(1)

    if args.stdout:
        # Copy to stdout as binary
        with open(image_path, 'rb') as f:
            sys.stdout.buffer.write(f.read())
    elif args.output:
        # Copy to specified output file
        output_path = os.path.expanduser(args.output)
        # Create parent directory if needed
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        shutil.copy2(image_path, output_path)
        print(f"Copied to: {output_path}")
    else:
        # Just print the path
        print(image_path)


def cmd_schema(args):
    """Show database schema information."""
    conn = get_db_connection()
    try:
        if args.table:
            # Show specific table schema
            sql = "SELECT sql FROM sqlite_master WHERE type='table' AND name=?"
            cursor = conn.execute(sql, (args.table,))
        else:
            # Show all tables
            sql = "SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"
            cursor = conn.execute(sql)

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        print(format_output(rows, columns, args.format))
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Read-only access to Bear notes database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s query "SELECT ZTITLE FROM ZSFNOTE WHERE ZTRASHED=0 LIMIT 10"
  %(prog)s note "WPlan 2024-12-02 (W49)"
  %(prog)s search "WPlan%%"
  %(prog)s pinned
  %(prog)s images "My Note Title"
  %(prog)s image ABC123 photo.png --output /tmp/bearnotes/photo.png
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Parent parser for --format option (shared by subcommands)
    format_parent = argparse.ArgumentParser(add_help=False)
    format_parent.add_argument(
        "--format", "-f",
        choices=["json", "csv", "text"],
        default="json",
        help="Output format (default: json)"
    )

    # query command
    query_parser = subparsers.add_parser("query", help="Execute a SELECT query", parents=[format_parent])
    query_parser.add_argument("sql", help="SQL SELECT query to execute")
    query_parser.set_defaults(func=cmd_query)

    # note command
    note_parser = subparsers.add_parser("note", help="Get a note by exact title", parents=[format_parent])
    note_parser.add_argument("title", help="Exact note title")
    note_parser.set_defaults(func=cmd_note)

    # search command
    search_parser = subparsers.add_parser("search", help="Search notes by title pattern", parents=[format_parent])
    search_parser.add_argument("pattern", help="SQL LIKE pattern (use %% for wildcard)")
    search_parser.set_defaults(func=cmd_search)

    # pinned command
    pinned_parser = subparsers.add_parser("pinned", help="List pinned notes", parents=[format_parent])
    pinned_parser.set_defaults(func=cmd_pinned)

    # images command
    images_parser = subparsers.add_parser("images", help="List images in a note", parents=[format_parent])
    images_parser.add_argument("title", help="Note title")
    images_parser.set_defaults(func=cmd_images)

    # image command (no format option - outputs binary or path)
    image_parser = subparsers.add_parser("image", help="Read an image file")
    image_parser.add_argument("guid", help="Image GUID (directory name)")
    image_parser.add_argument("filename", help="Image filename")
    image_parser.add_argument("--output", "-o", help="Output file path")
    image_parser.add_argument("--stdout", action="store_true", help="Write binary to stdout")
    image_parser.set_defaults(func=cmd_image)

    # schema command (bonus utility)
    schema_parser = subparsers.add_parser("schema", help="Show database schema", parents=[format_parent])
    schema_parser.add_argument("--table", "-t", help="Specific table name")
    schema_parser.set_defaults(func=cmd_schema)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
