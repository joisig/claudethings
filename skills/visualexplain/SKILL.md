---
name: visualexplain
description: Draw a plan, a code change or a subsystem as a local HTML page on a pan-and-zoom canvas - system shape, before/after delta, order over time, plan steps and gates, UI sketch - with Mermaid for simple diagrams and freehand SVG where fidelity matters. Use when the user types /visualexplain or asks for a visual, a diagram or a picture of a plan, a design, a change or how something works. Also run it without being asked in the case the global CLAUDE.md lists (the first version of a plan, when a picture helps).
---

# visualexplain — draw the plan, the change or the system

Text does not show the shape of a system, the difference between before and after,
or the order of events well. This skill draws them on one HTML page: a canvas
without edges that the user pans and zooms on a large monitor.

The page is a companion. The plan (or the code) stays the source of truth, and the
user's TODOR comments go in the plan, not on the page.

```
/visualexplain [target] [views] [feedback]
```

## Files

| File | Use |
|---|---|
| `/Users/joi/.claude/skills/visualexplain/example.html` | The reference page. Read it before you write the first page of a session |
| `/Users/joi/.claude/skills/visualexplain/canvas.css`, `canvas.js` | The canvas shell. Every page links them. Do not copy them into the page |
| `/Users/joi/.claude/skills/visualexplain/bin/visualexplain` | `mermaid-cache <tmp dir>`: keeps a local copy of Mermaid (Step 4) |

## Step 1 — the target

| Target | Source | Research | Footer text |
|---|---|---|---|
| A plan. This is the default when the session has one | The plan text and what the session already knows | Do not research the code only for the page | "Sketch of `<plan file>`, `<date and time>`. The plan text is the authority." |
| A code change ("changes", "diff", a branch) | The diff. Choose it as `advreview` Step 1 does: the uncommitted changes (staged, unstaged, untracked) on a protected branch; the branch against its base on a feature branch | Read the diff and the code around it | "Sketch of `<what was compared>`, `<date and time>`." |
| A file, a document or a subsystem | The code or the document | Reading it is the job | "Sketch of `<target>`, `<date and time>`." |

The page is a free sketch: it may be approximate, and the footer says so. For a
plan, each frame names the plan section it comes from, so that the user knows where
a TODOR goes. For the other targets, a frame names files.

## Step 2 — the views

Choose only the views that show something that is hard to see in the text:

| View | Shows |
|---|---|
| Shape | The components and their connections |
| Delta | Before and after, with the status colours |
| Order over time | A sequence, a data flow or a decision flow |
| Plan steps | The steps, the output of each, the gates, and the results that feed later steps |
| UI sketch | Roughly what a screen looks like. Only when the UI change is central |

When the user names views, draw those. When everything is new and "before" would be
empty, do not draw a delta: use the status colours on the shape view.

**The gate for an automatic run.** Build a page when at least one view passes, for
example:

- three or more components whose connections change;
- a flow with three or more actors, or an order that matters;
- plan steps with gates or dependencies between them.

The number of files is not the measure: a one-file change to a sequence can pass.
If no view passes, write one line and build nothing:

> visualexplain: no page, the plan is clear as text.

Do not build a page to have a page. An explicit `/visualexplain` always builds one.

## Step 3 — Mermaid or freehand, for each frame

- **Mermaid** when the view is a standard diagram and automatic layout is good
  enough: a flowchart, sequence, state or entity diagram with about 15 nodes or
  fewer. It is quick, and the layout is tidy without a check.
- **Freehand** (inline SVG or HTML) when it gives the best fidelity:
  - a before/after pair where the same element must be in the same place on both
    sides;
  - plan steps with gates and feed-forward notes;
  - a UI sketch;
  - a view that needs its own emphasis, grouping or annotation;
  - a diagram that Mermaid lays out badly.

A page can have both. Do not put a view in Mermaid when that loses the point of the
picture.

## Step 4 — write the page

### Where

`<repo>/tmp/<date>-<subject>/visualexplain-<slug>-<n>.html`

- `<repo>` is the repository the session works in, also when the plan file is
  somewhere else (`~/.claude/plans/`).
- The folder follows the `tmp/` rule in the global CLAUDE.md. If the session
  already has a dated folder, use it.
- `<slug>` is a short name for the subject of the plan or the target, for example
  `retry-queue`. `<n>` starts at 1 and is the next free number for that slug in the
  folder. A new page never overwrites another page.
- Before you write, run `git check-ignore -q <path>` in the repository. The file
  does not have to exist. Exit code 0 means that the path is ignored. With another
  exit code (not ignored, or not a repository), or when the folder is not writable,
  write the page to `<scratchpad>/<date>-<subject>/` in place of the repo folder,
  and tell the user.

### Mermaid cache

When the page has a Mermaid block and the page goes in a repo `tmp/` folder, run:

```bash
/Users/joi/.claude/skills/visualexplain/bin/visualexplain mermaid-cache <repo>/tmp
```

It keeps `<repo>/tmp/visualexplain/mermaid.min.js` and downloads it again when it
is older than 30 days. That folder has no date on purpose: all pages of the repo
share it. This is an exception to the `tmp/` rule. The shell loads that copy first and the CDN second. The
command is best effort and always continues; do not retry it and do not replace it.
Do not run it for a page in the scratchpad: that page uses the CDN.

### Markup

`example.html` is the model. The skeleton:

```html
<!doctype html>
<meta charset="utf-8">
<title>visualexplain: <subject></title>
<link rel="stylesheet" href="file:///Users/joi/.claude/skills/visualexplain/canvas.css">

<div id="ve-world" style="--ve-cols: 3">
  <h1>Title</h1>
  <p class="ve-lede">One or two sentences: what the page shows.</p>

  <section class="ve-frame">
    <h2>Shape: after</h2>
    <p class="ve-src">Plan section: "Design"</p>
    <!-- a Mermaid block, an inline svg, or HTML -->
  </section>
  <section class="ve-frame ve-wide">...</section>
</div>

<p class="ve-note">Sketch of ..., 2026-10-04 10:00. The plan text is the authority.</p>
<script src="file:///Users/joi/.claude/skills/visualexplain/canvas.js"></script>
```

The world:

- `#ve-world` is a grid. The frames go into it in the order you write them.
  `--ve-cols` is the number of columns (2 to 4). `ve-wide` makes a frame two columns
  wide. Do not position frames in another way.
- At most about six frames, in reading order. Before comes directly before after.
  Cause comes before effect.
- A legend frame when the page uses the status colours: a `<ul class="ve-legend">`
  with one `<li>` for each status class that the page uses. The legend does not
  count as one of the six.
- Make a frame `ve-wide` when its content is wider than about 900 px: a wide SVG, a
  left-to-right flowchart with a long chain, or a sequence diagram with more than
  five participants.
- There are no arrows between frames. The order and the titles carry the relation.

Status colours, the same in every page:

| Class | Meaning |
|---|---|
| `ve-existing` | Exists today, not changed |
| `ve-added` | Added by the plan or the change |
| `ve-changed` | Exists today and is changed |
| `ve-removed` | Removed |

Use them only for this meaning. A shape that has no status (a plan step, a gate, the
outline of a UI sketch) gets `class="ve-box"`.

A Mermaid frame:

- `<pre class="mermaid">`, and the first line is the diagram type.
- A `<` that comes directly before a letter is read as an HTML tag, so write it as
  `&lt;` (for example `&lt;&lt;interface>>`). A `<br/>` in a label stays as it is.
- To show an angle bracket in a label (`tmp/<date>`), write `#lt;` and `#gt;`.
- Put a label that has punctuation in quotes: `a["install.sh (links)"]`. Do not use
  `end` as a node name.
- In a `flowchart` and a `stateDiagram-v2`, the classes `existing`, `added`,
  `changed` and `removed` are defined by the shell: `node[Label]:::added`, or
  `class Busy added` for a state. Do not write a `classDef` for them.
- A sequence diagram has no classes for single elements. Mark an added part with a
  `rect` block or a `Note`. When the delta is the point, draw the frame freehand.
- A block that does not parse shows its error and its source in the frame.

A freehand SVG frame:

- `<svg viewBox="0 0 W H">` and no `width` attribute. One unit is one CSS pixel at
  100% zoom. A normal frame is 400 to 900 wide; a wide frame can be 1000 to 1800.
- Shapes are `rect`, `circle`, `ellipse` or `polygon`. Connectors are `path`, `line`
  or `polyline`. The status classes work on both and on `text`.
- A plain connector: `class="ve-arrow"`. An arrowhead:
  `marker-end="url(#ve-arrowhead)"`, or `#ve-arrowhead-added`, `-changed`,
  `-removed`, `-existing` for a status colour. The shell defines these markers.
- A connector ends at the edge of its target shape, or 2 px before it. The point of
  the arrowhead is at the end of the connector.
- Small secondary text: `class="ve-label"`. Do not make text smaller than 12 px.
- Give each label room: a box is at least as wide as its text, and no text is on
  top of a line. You do not see the result, so calculate the positions with care.
  Normal text is 15 px, about 8 px for each character. `ve-label` is 13 px, about
  7 px for each character.

Colours come from the classes and the CSS variables (`var(--ve-fg)`,
`var(--ve-muted)`, `var(--ve-line)`, `var(--ve-added)`, ...), so that the page works
in light and in dark mode. Do not write fixed colours.

### Interaction

A page is static by default: everything is visible, and the user pans and zooms.
Add one of these only when the static view would be crowded:

- **Before/after toggle:** one diagram that changes between the two states.
- **Step-through:** next and previous buttons, the active step or message lit, and a
  caption for the step.

Write them for the page, in a `<script>` after `canvas.js`. Use `<button>` elements
(a drag on a button does not pan). When the script changes the size of a frame, call
`window.visualexplain.fitAll()`.

## Step 5 — show the page

1. Run `open <file>`. In a sandbox this can fail. Do not retry.
2. In both cases, tell the user in one or two lines: the `file://` URL and the list
   of frames.
3. For a plan, also put the URL in the plan file, as one line directly below the
   title: `Visual: <file:// URL>`. A new page replaces that line.

Do not render the page and do not take a screenshot of it first. The user reports a
bad layout, and you fix it.

## Feedback and later versions

- **Feedback about the drawing** (an overlap, something unreadable, wrong emphasis, a
  Mermaid error): fix the same file in place.
- **Feedback about the design:** that is plan feedback. Handle it by the TODOR rules
  in the global CLAUDE.md. Build a new page (the next `<n>`) only when the user asks.
- A page is a dated snapshot, and the skill does not detect a stale page. When you
  write a new version of a plan in a session where a page exists, say once: "the
  page predates this plan version".

## Plan mode

The plan file is always yours to edit in plan mode (the `Visual:` line). In addition,
the global CLAUDE.md permits two writes: the page file, and the Mermaid cache
command. Make those two and no other.

If a write is not possible in plan mode, do not work around it. Write one line that
names the views a page would have, and show the plan as usual:

> visualexplain: a page with the data flow and the step gates would help. Ask for
> /visualexplain outside plan mode.

## Later: what moves into the shell

The shell is small on purpose. When the same hand-written behaviour (for example the
before/after toggle) is on a third page, propose to move it into `canvas.js`.
