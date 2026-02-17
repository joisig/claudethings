---
name: bear-notes
description: Read and search Bear notes, extract images for transcription. Use when user mentions Bear notes, WPlan, DPlan, weekly plans, or wants to transcribe handwritten notes from Bear.
---

# Bear Notes Reader

Access Joi's Bear notes database (read-only) using the `bear_reader.py` tool.

## Tool Location

```bash
/Users/joi/p/claudethings/bear_reader.py
```

Always launch the tool using that path. Do not put python3 in front. I want to be able to "always allow" for invocations of just that particular file.

## Available Commands

### Query (raw SQL)
```bash
bear_reader.py query "SELECT ZTITLE FROM ZSFNOTE WHERE ZTRASHED=0 LIMIT 10"
```
Only SELECT queries are allowed. The tool rejects INSERT, UPDATE, DELETE, etc.

### Get Note by Title
```bash
bear_reader.py note "Exact Note Title"
```
Returns the full note content including ZTEXT (markdown body).

### Search Notes
```bash
bear_reader.py search "WPlan%"
```
Uses SQL LIKE pattern. `%` is wildcard. Results sorted by modification date (newest first).

### List Pinned Notes
```bash
bear_reader.py pinned
```
Returns all currently pinned notes, sorted by modification date (newest first).

### List Images in a Note
```bash
bear_reader.py images "Note Title"
```
Returns ZUNIQUEIDENTIFIER (guid) and ZFILENAME for each image.

### Extract an Image
```bash
bear_reader.py image <guid> <filename> --output /tmp/bearnotes/image.png
```
Copies the image to the specified path. Always use `/tmp/bearnotes/` as the output directory.

### Show Database Schema
```bash
bear_reader.py schema
bear_reader.py schema --table ZSFNOTE
```

## Output Formats

All commands except `image` support `--format` / `-f`:
- `json` (default) - JSON array
- `csv` - CSV with headers
- `text` - Tab-separated values

## Database Structure

### Main Tables

**ZSFNOTE** - Notes table
| Column | Description |
|--------|-------------|
| Z_PK | Primary key (integer) |
| ZUNIQUEIDENTIFIER | UUID string for the note |
| ZTITLE | Note title |
| ZTEXT | Full note content (markdown) |
| ZCREATIONDATE | Creation timestamp (Cocoa format) |
| ZMODIFICATIONDATE | Last modified timestamp (Cocoa format) |
| ZPINNED | 1 if pinned, 0 otherwise |
| ZTRASHED | 1 if in trash, 0 otherwise |
| ZARCHIVED | 1 if archived, 0 otherwise |
| ZENCRYPTED | 1 if encrypted, 0 otherwise |

**ZSFNOTEFILE** - Attachments/images
| Column | Description |
|--------|-------------|
| Z_PK | Primary key (integer) |
| ZUNIQUEIDENTIFIER | GUID used in file path (e.g., `F8DE33E6-B56A-431D-9EB3-3D474930E894`) |
| ZFILENAME | Filename (e.g., `sketch.png`) |
| ZNOTE | Foreign key to ZSFNOTE.Z_PK |
| ZUNUSED | 1 if orphaned/deleted, 0 if in use |

### Joining Notes and Files
```sql
SELECT n.ZTITLE, f.ZUNIQUEIDENTIFIER, f.ZFILENAME
FROM ZSFNOTE n
JOIN ZSFNOTEFILE f ON f.ZNOTE = n.Z_PK
WHERE n.ZTRASHED = 0 AND f.ZUNUSED = 0
```

### Date Format
Bear uses **Cocoa/Core Data timestamps**: seconds since January 1, 2001.
- To convert to Unix timestamp: add 978307200
- Example: `786635250` = December 2025

### Default Filters
Always filter for active notes:
```sql
WHERE ZTRASHED = 0 AND ZARCHIVED = 0 AND ZENCRYPTED = 0
```
The tool applies these automatically for convenience commands.

### File Locations
- **Database**: `~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/database.sqlite`
- **Images**: `~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/Local Files/Note Images/{guid}/{filename}`
- **Files**: `~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/Local Files/Note Files/{guid}/{filename}`

## Note Naming Conventions

### Weekly Plans (WPlan)
Format: `WPlan YYYY-MM-DD WXX`
- `YYYY-MM-DD` is the Monday of that week
- `WXX` is the ISO week number (W01-W53)
- Example: `WPlan 2025-12-01 W49`

To find the current week's plan:
```bash
bear_reader.py search "WPlan 2025-12%" -f json
```

### Daily Plans (DPlan) - Historical
Format: `DPlan YYYY-MM-DD Day`
- Example: `DPlan 2020-02-01 Sat`
- These are older notes, no longer actively created.

## WPlan Structure

Weekly plans contain these sections:

1. **Title**: `# WPlan YYYY-MM-DD WXX`
2. **Remember**: Links to QPlan, habit reminders
3. **Work summary**: Expected work hours per project
4. **## Plan**: Tasks organized by project/category
   - Tasks use `- [ ]` (incomplete) or `- [x]` (complete)
   - Priority markers: `A:` (high), `B:` (medium), `C:` (low)
5. **## Journal**: Personal highs/lows/notable events
6. **## DONE**: Completed items organized by day of week
7. **## [Project] Next Up**: Project-specific backlogs
8. **## Recent backlog**: Items under consideration

## Image Transcription Workflow

When the user asks to transcribe handwritten notes:

1. **Find the note** containing the images:
   ```bash
   bear_reader.py note "WPlan 2025-12-01 W49" -f json
   ```

2. **List images** in the note:
   ```bash
   bear_reader.py images "WPlan 2025-12-01 W49"
   ```

3. **Extract each image** to `/tmp/bearnotes/`:
   ```bash
   mkdir -p /tmp/bearnotes
   bear_reader.py image <guid> <filename> --output /tmp/bearnotes/<filename>
   ```

4. **Read the image** using the Read tool to analyze the handwriting

5. **Return markdown** formatted transcription for the user to copy

Images are often named `sketch.png`, `sketch 2.png`, etc. for handwritten notes.

## Common Queries

### Recent notes modified today
```bash
bear_reader.py query "SELECT ZTITLE, ZMODIFICATIONDATE FROM ZSFNOTE WHERE ZTRASHED=0 AND ZARCHIVED=0 ORDER BY ZMODIFICATIONDATE DESC LIMIT 20"
```

### Notes containing specific text
```bash
bear_reader.py query "SELECT ZTITLE FROM ZSFNOTE WHERE ZTEXT LIKE '%search term%' AND ZTRASHED=0 AND ZARCHIVED=0"
```

### All WPlans from this year
```bash
bear_reader.py search "WPlan 2025%"
```
