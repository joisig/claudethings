"""Tests for skills/projects/bin/projects. Run: python3 -m unittest discover skills/projects/tests"""

import datetime as dt
import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "..", "bin", "projects")

loader = importlib.machinery.SourceFileLoader("projects_tool", TOOL)
spec = importlib.util.spec_from_loader("projects_tool", loader)
P = importlib.util.module_from_spec(spec)
loader.exec_module(P)

TODAY = dt.date.today()
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}


def d(days):
    return (TODAY + dt.timedelta(days=days)).isoformat()


def sh(cwd, *args, env=None):
    r = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True,
                       env={**os.environ, **GIT_ENV, **(env or {})})
    if r.returncode != 0:
        raise AssertionError(f"{args} failed: {r.stdout}{r.stderr}")
    return r.stdout


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(textwrap.dedent(text).lstrip("\n"))


PROJECT = """
# Session diagnostics

State: active · Re-entry: medium · Created: 2026-10-14 · Touched: {touched}

## Goal
Find the reconnect problem.

## Brief
- Where things stand.

## Work
- {repo} · branch joi-diag · commit abc1234 · PR https://github.com/x/y/pull/1

## Waiting on others
- [ ] Fix reconnect bug
  - Waiting: @rodion since {since} · nudge {nudge}
  - Thread: https://mail.superhuman.com/thread/1

## Ready for me
- [ ] Manual test of switching
  - Size: 30 min · shallow · protos, any worktree
  - Unblocks: @yuliia
- [ ] Deep refactor
  - Size: 60 min · deep · protos, branch joi-diag

## Later
- [ ] Check prod data
  - Not before: {later}
  - Size: 15 min · shallow · no worktree
  - How: run X, look for Y.
    Good means Z.
- [ ] Turn logging off
  - Not before: after crankwheel/diag: Check prod

## Backlog
- Idea: a toggle

## Done
- [x] Add logging

## Log
- 2026-10-22 16:40 · ~70 min (guessed 30) · added the soak-test script
"""


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.root = os.path.join(self.tmp, "projects")
        self.claude = os.path.join(self.tmp, "claude")
        self.repo = os.path.join(self.tmp, "protos")
        os.makedirs(self.repo)
        sh(self.repo, "git", "init", "-q", "-b", "main")
        sh(self.repo, "git", "commit", "-q", "--allow-empty", "-m", "root")
        write(os.path.join(self.root, "themes.md"), f"""
            # Themes

            ## crankwheel — CrankWheel
            Repos: {self.repo}
            Delegation: on

            ## personal — Personal
            Repos:
            """)
        write(os.path.join(self.root, "people.md"), """
            ## @rodion — Rodion
            - Email: rodion@crankwheel.com
            - GitHub: gitradik

            ## @yuliia — Yuliia
            - Email: yuliya@example.com
            """)
        os.makedirs(os.path.join(self.root, "personal"))
        self.write_project()
        P.PROJECTS_DIR = self.root
        P.CLAUDE_DIR = self.claude
        self.env = {"PROJECTS_DIR": self.root, "PROJECTS_CLAUDE_DIR": self.claude}

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write_project(self, **kw):
        vals = {"touched": TODAY.isoformat(), "since": d(-3), "nudge": d(-1), "later": d(2),
                "repo": self.repo}
        vals.update(kw)
        write(os.path.join(self.root, "crankwheel", "diag.md"), PROJECT.format(**vals))

    def run_tool(self, *args, stdin=None, ok=True):
        r = subprocess.run(["python3", TOOL, *args], capture_output=True, text=True, input=stdin,
                           env={**os.environ, **GIT_ENV, **self.env})
        if ok and r.returncode != 0:
            raise AssertionError(f"projects {args} failed: {r.stdout}{r.stderr}")
        return r

    def load(self):
        themes, people, projects, errors = P.load_all()
        self.assertEqual(errors, [])
        return themes, people, projects


class TestParse(Fixture):
    def test_project_parses(self):
        themes, people, projects = self.load()
        (p,) = projects
        self.assertEqual(p.ident, "crankwheel/diag")
        self.assertEqual(p.front["title"], "Session diagnostics")
        self.assertEqual([i.section for i in p.items],
                         ["Waiting on others", "Ready for me", "Ready for me", "Later", "Later", "Done"])
        w = p.items[0].waiting
        self.assertEqual(w["handles"], ["@rodion"])
        self.assertEqual(w["nudge"].isoformat(), d(-1))
        self.assertEqual(p.items[1].size["minutes"], 30)
        self.assertEqual(p.items[1].size["repo"], "protos")
        self.assertEqual(p.items[2].size["branch"], "joi-diag")
        self.assertEqual(p.items[3].keys["How"], "run X, look for Y. Good means Z.")
        self.assertEqual(p.items[4].not_before, ("after", "crankwheel/diag", "Check prod"))
        self.assertEqual(p.work[0]["commit"], "abc1234")
        self.assertEqual(p.work[0]["prs"], ["https://github.com/x/y/pull/1"])
        self.assertEqual(p.log[0][0].hour, 16)
        self.assertEqual(P.validate(themes, people, projects), [])

    def test_unknown_key_is_an_error(self):
        path = os.path.join(self.root, "crankwheel", "diag.md")
        with open(path) as f:
            text = f.read()
        with open(path, "w") as f:
            f.write(text.replace("  - Unblocks: @yuliia", "  - Unblock: @yuliia"))
        _, _, _, errors = P.load_all()
        self.assertEqual(len(errors), 1)
        self.assertIn("known key", errors[0])

    def test_unknown_section_is_an_error(self):
        path = os.path.join(self.root, "crankwheel", "diag.md")
        with open(path, "a") as f:
            f.write("\n## Random\nx\n")
        _, _, _, errors = P.load_all()
        self.assertIn("unknown section", errors[0])

    def test_survives_a_wysiwyg_editor_rewrite(self):
        # What CowCo wrote on save: blank lines after headings, escaped ~ and >.
        path = os.path.join(self.root, "crankwheel", "diag.md")
        with open(path) as f:
            text = f.read()
        text = text.replace("## Goal\n", "## Goal\n\n")
        text = text.replace("- [ ] Fix reconnect bug", "- [ ] Fix reconnect bug -&gt; asked again")
        text = text.replace("~70 min", "\\~70 min")
        with open(path, "w") as f:
            f.write(text)
        themes, people, projects = self.load()
        self.assertEqual(projects[0].items[0].text, "Fix reconnect bug -> asked again")
        self.assertEqual(projects[0].log[0][1].split(" · ")[1], "~70 min (guessed 30)")
        self.assertEqual(P.validate(themes, people, projects), [])

    def test_nested_checkbox_is_an_error(self):
        path = os.path.join(self.root, "crankwheel", "diag.md")
        with open(path) as f:
            text = f.read()
        with open(path, "w") as f:
            f.write(text.replace("  - Unblocks: @yuliia", "  - [ ] delegated to someone"))
        _, _, _, errors = P.load_all()
        self.assertIn("known key", errors[0])

    def test_bad_size(self):
        with self.assertRaises(P.ParseError):
            P.parse_size("30 min · sleepy · no worktree", "x")
        with self.assertRaises(P.ParseError):
            P.parse_size("30 min · deep · protos", "x")
        self.assertEqual(P.parse_size("2 h · deep · no worktree · dev server", "x")["minutes"], 120)


class TestValidate(Fixture):
    def errors(self):
        return P.validate(*self.load())

    def test_later_needs_not_before_and_handles_must_be_known(self):
        path = os.path.join(self.root, "crankwheel", "diag.md")
        with open(path) as f:
            text = f.read()
        text = text.replace(f"  - Not before: {d(2)}\n", "").replace("@yuliia", "@nobody")
        with open(path, "w") as f:
            f.write(text)
        errs = self.errors()
        self.assertTrue(any("needs 'Not before:'" in e for e in errs), errs)
        self.assertTrue(any("unknown handle @nobody" in e for e in errs), errs)

    def test_reference_to_missing_or_ambiguous_item(self):
        path = os.path.join(self.root, "crankwheel", "diag.md")
        with open(path) as f:
            text = f.read()
        with open(path, "w") as f:
            f.write(text.replace("after crankwheel/diag: Check prod", "after crankwheel/diag: "
                                 "M").replace("- [ ] Deep refactor", "- [ ] Manual deep refactor"))
        errs = self.errors()
        self.assertTrue(any("2 items in crankwheel/diag start with 'M'" in e for e in errs), errs)
        with open(path, "w") as f:
            f.write(text.replace("after crankwheel/diag: Check prod", "after crankwheel/gone"))
        self.assertTrue(any("no project crankwheel/gone" in e for e in self.errors()))

    def test_reference_into_archive(self):
        write(os.path.join(self.root, "archive", "personal", "old.md"), """
            # Old

            State: done · Re-entry: low · Created: 2026-01-01 · Touched: 2026-01-02

            ## Goal
            Old.
            """)
        path = os.path.join(self.root, "crankwheel", "diag.md")
        with open(path) as f:
            text = f.read()
        with open(path, "w") as f:
            f.write(text.replace("after crankwheel/diag: Check prod", "after personal/old"))
        self.assertEqual(self.errors(), [])
        _, _, projects = self.load()
        item = [i for p in projects for i in p.items if i.text == "Turn logging off"][0]
        self.assertTrue(P.not_before_met(item, projects, TODAY))

    def test_done_state_outside_archive(self):
        path = os.path.join(self.root, "crankwheel", "diag.md")
        with open(path) as f:
            text = f.read()
        with open(path, "w") as f:
            f.write(text.replace("State: active", "State: done"))
        self.assertTrue(any("move it to archive" in e for e in self.errors()))


class TestDerived(Fixture):
    def test_status_and_dates(self):
        _, _, projects = self.load()
        (p,) = projects
        self.assertEqual(P.status(p, projects, TODAY), "ready")
        self.assertEqual(P.next_date(p).isoformat(), d(-1))
        self.assertEqual(P.ball(p), ["@rodion"])
        later, after = p.items[3], p.items[4]
        self.assertFalse(P.actionable(later, projects, TODAY))
        self.assertTrue(P.actionable(later, projects, TODAY + dt.timedelta(days=2)))
        self.assertFalse(P.actionable(after, projects, TODAY))
        later.checked = True
        self.assertTrue(P.actionable(after, projects, TODAY))

    def test_waiting_when_only_others_hold_the_ball(self):
        _, _, projects = self.load()
        (p,) = projects
        for i in p.items:
            if i.section == "Ready for me":
                i.checked = True
        self.assertEqual(P.status(p, projects, TODAY), "waiting")

    def test_reentry_goes_up_when_stale(self):
        _, _, projects = self.load()
        (p,) = projects
        self.assertEqual(P.reentry_minutes(p, TODAY), 15)
        self.assertEqual(P.reentry_minutes(p, TODAY + dt.timedelta(days=30)), 30)


class TestCommands(Fixture):
    def test_fit(self):
        out = self.run_tool("fit", "--minutes", "50").stdout
        self.assertIn("Manual test of switching", out)
        self.assertNotIn("Deep refactor", out)          # 60 + 15 > 50
        self.assertNotIn("Check prod data", out)        # not before is in the future
        out = self.run_tool("fit", "--minutes", "120").stdout
        self.assertLess(out.index("Manual test"), out.index("Deep refactor"))   # unblocks first
        out = self.run_tool("fit", "--minutes", "120", "--attention", "shallow").stdout
        self.assertNotIn("Deep refactor", out)
        out = self.run_tool("fit", "--minutes", "120", "--no-worktree").stdout
        self.assertIn("nothing fits", out)
        out = self.run_tool("fit", "--minutes", "120", "--repo", self.repo).stdout
        self.assertIn("Manual test", out)

    def test_next(self):
        out = self.run_tool("next").stdout
        self.assertIn("Fix reconnect bug", out.split("## Ready")[0])          # nudge due
        self.assertIn("Manual test of switching", out)
        self.assertIn("On Joi in delegation themes (crankwheel)", out)
        later = self.run_tool("next", "--date", d(3)).stdout
        self.assertIn("Check prod data  [was in Later", later)

    def test_render(self):
        self.run_tool("render")
        with open(os.path.join(self.root, "crankwheel", "README.md")) as f:
            readme = f.read()
        self.assertIn("[Session diagnostics](diag.md) | ready", readme)
        with open(os.path.join(self.root, "overview.md")) as f:
            self.assertIn("crankwheel/diag", f.read())
        with open(os.path.join(self.root, "personal", "README.md")) as f:
            self.assertIn("No open projects", f.read())

    def test_find(self):
        sh(self.repo, "git", "checkout", "-q", "-b", "joi-diag")
        out = self.run_tool("find", "--repo", self.repo, "--branch", "joi-diag").stdout
        self.assertIn("crankwheel/diag (branch match", out)
        self.assertIn("theme crankwheel", out)

    def test_landed(self):
        main_sha = sh(self.repo, "git", "rev-parse", "HEAD").strip()
        sh(self.repo, "git", "checkout", "-q", "-b", "side")
        sh(self.repo, "git", "commit", "-q", "--allow-empty", "-m", "side")
        side_sha = sh(self.repo, "git", "rev-parse", "HEAD").strip()
        out = self.run_tool("landed", "--repo", self.repo, "--commit", main_sha).stdout
        self.assertTrue(out.startswith("landed"), out)
        out = self.run_tool("landed", "--repo", self.repo, "--commit", side_sha).stdout
        self.assertTrue(out.startswith("not landed"), out)
        out = self.run_tool("landed", "--repo", self.repo, "--commit", "0" * 40).stdout
        self.assertTrue(out.startswith("unknown"), out)
        out = self.run_tool("landed", "--repo", self.repo, "--branch", "side").stdout
        self.assertTrue(out.startswith("not landed"), out)

    def test_save_commits_only_its_own_paths(self):
        sh(self.root, "git", "init", "-q", "-b", "main")
        write(os.path.join(self.root, ".gitignore"), "/overview.md\n/*/README.md\npending-handoffs.jsonl\n")
        sh(self.root, "git", "add", ".gitignore", "themes.md", "people.md")
        sh(self.root, "git", "commit", "-q", "-m", "base")
        write(os.path.join(self.root, "inbox.md"), "- something\n")
        sh(self.root, "git", "add", "inbox.md")                      # another session's staged file
        out = self.run_tool("save", "-m", "Add diag", "crankwheel/diag.md").stdout
        self.assertIn("Add diag", out)
        files = sh(self.root, "git", "show", "--name-only", "--format=", "HEAD").split()
        self.assertEqual(files, ["crankwheel/diag.md"])
        self.assertIn("A  inbox.md", sh(self.root, "git", "status", "--short"))
        self.assertTrue(os.path.exists(os.path.join(self.root, "overview.md")))

    def test_project_branch_without_commit_is_unknown(self):
        verdict, details = P.landed_check(self.repo, None, "main", [])
        self.assertEqual(verdict, "unknown", details)

    def test_no_trunk_is_unknown(self):
        sh(self.repo, "git", "branch", "-m", "main", "feature")
        sha = sh(self.repo, "git", "rev-parse", "HEAD").strip()
        verdict, details = P.landed_check(self.repo, sha, None, [])
        self.assertEqual(verdict, "unknown", details)

    def test_only_the_last_pr_decides(self):
        side = os.path.join(self.repo)
        sh(side, "git", "checkout", "-q", "-b", "side")
        sh(side, "git", "commit", "-q", "--allow-empty", "-m", "side")
        sha = sh(side, "git", "rev-parse", "HEAD").strip()
        states = {"https://x/1": ("MERGED", ""), "https://x/2": ("OPEN", "REVIEW_REQUIRED")}
        orig = P.pr_state
        P.pr_state = lambda url: states[url]
        try:
            verdict, details = P.landed_check(self.repo, sha, None, ["https://x/1", "https://x/2"])
            self.assertEqual(verdict, "not landed", details)
            verdict, _ = P.landed_check(self.repo, sha, None, ["https://x/2", "https://x/1"])
            self.assertEqual(verdict, "landed")
        finally:
            P.pr_state = orig

    def test_saving_only_the_inbox_is_no_handoff(self):
        sh(self.root, "git", "init", "-q", "-b", "main")
        # The tool finds its session by walking up to a PID listed in sessions/*.json;
        # this test process is an ancestor of the tool's process.
        write(os.path.join(self.claude, "sessions", "1.json"),
              json.dumps({"pid": os.getpid(), "sessionId": "t1"}))
        write(os.path.join(self.root, "inbox.md"), "- something\n")
        self.run_tool("save", "-m", "inbox", "inbox.md")
        log = os.path.join(self.root, ".git", "projects-handoffs.jsonl")
        self.assertFalse(os.path.exists(log))
        self.run_tool("save", "-m", "diag", "crankwheel/diag.md")
        self.assertEqual(P.read_jsonl(log)[0]["projects"], ["crankwheel/diag"])
        self.assertEqual(P.read_jsonl(log)[0]["session"], "t1")

    def test_save_refuses_a_broken_file(self):
        sh(self.root, "git", "init", "-q", "-b", "main")
        path = os.path.join(self.root, "crankwheel", "diag.md")
        with open(path, "a") as f:
            f.write("\n## Nonsense\n")
        r = self.run_tool("save", "-m", "x", "crankwheel/diag.md", ok=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("nothing saved", r.stderr)


class TestHook(Fixture):
    def setUp(self):
        super().setUp()
        sh(self.root, "git", "init", "-q", "-b", "main")
        self.transcript = os.path.join(self.tmp, "t.jsonl")
        self.write_transcript(work=True)

    def write_transcript(self, work, minutes=5):
        start = dt.datetime(2026, 10, 22, 10, 0, tzinfo=dt.timezone.utc)
        rows = []
        for m in range(0, minutes + 1):
            rows.append({"type": "user", "timestamp": (start + dt.timedelta(minutes=m)).isoformat(),
                         "cwd": self.repo, "gitBranch": "joi-diag", "message": {"content": "hi"}})
        tool = {"type": "tool_use", "name": "Edit",
                "input": {"file_path": os.path.join(self.repo, "a.ex") if work else
                          os.path.join(self.root, "crankwheel", "diag.md")}}
        rows.append({"type": "assistant", "timestamp": (start + dt.timedelta(minutes=minutes)).isoformat(),
                     "message": {"content": [tool]}})
        with open(self.transcript, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    def hook(self, event, session="s1", cwd=None, extra=None):
        data = {"session_id": session, "transcript_path": self.transcript, "cwd": cwd or self.repo}
        data.update(extra or {})
        r = self.run_tool("hook", event, stdin=json.dumps(data))
        self.assertEqual(r.returncode, 0)
        return r.stdout.strip()

    def test_stop_blocks_once_then_rate_limits(self):
        out = self.hook("stop")
        self.assertEqual(json.loads(out)["decision"], "block")
        self.assertEqual(self.hook("stop"), "")
        self.assertEqual(self.hook("stop", extra={"stop_hook_active": True}, session="s2"), "")

    def test_stop_silent_without_work_or_outside_themes(self):
        self.write_transcript(work=False)
        self.assertEqual(self.hook("stop"), "")
        self.write_transcript(work=True)
        other = os.path.join(self.tmp, "other")
        os.makedirs(other)
        sh(other, "git", "init", "-q")
        self.assertEqual(self.hook("stop", session="s3", cwd=other), "")

    def test_stop_silent_after_handoff(self):
        with open(os.path.join(self.root, ".git", "projects-handoffs.jsonl"), "w") as f:
            f.write(json.dumps({"session": "s1", "at": "2026-10-22T11:00:00+00:00"}) + "\n")
        self.assertEqual(self.hook("stop"), "")

    def test_session_end_records_pending(self):
        self.assertEqual(self.hook("session-end"), "")
        rows = P.read_jsonl(os.path.join(self.root, "pending-handoffs.jsonl"))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["project"], "crankwheel/diag")
        self.assertEqual(rows[0]["branches"], ["joi-diag"])
        out = self.run_tool("next").stdout
        self.assertIn("crankwheel/diag", out.split("ended without a handoff")[1])

    def test_silent_before_bootstrap(self):
        os.remove(os.path.join(self.root, "themes.md"))
        r = self.run_tool("hook", "stop", stdin=json.dumps(
            {"session_id": "s1", "transcript_path": self.transcript, "cwd": self.repo}))
        self.assertEqual((r.stdout, r.stderr), ("", ""))

    def test_saving_the_inbox_keeps_a_pending_handoff(self):
        write(os.path.join(self.root, "pending-handoffs.jsonl"),
              json.dumps({"session": "s9", "project": "crankwheel/diag"}) + "\n")
        write(os.path.join(self.root, "inbox.md"), "- x\n")
        self.run_tool("save", "-m", "inbox", "inbox.md")
        self.assertEqual(len(P.read_jsonl(os.path.join(self.root, "pending-handoffs.jsonl"))), 1)
        self.run_tool("save", "-m", "diag", "crankwheel/diag.md")
        self.assertEqual(P.read_jsonl(os.path.join(self.root, "pending-handoffs.jsonl")), [])

    def test_resolved_session_stays_handed_off(self):
        self.assertEqual(self.hook("session-end"), "")
        self.run_tool("save", "-m", "diag", "crankwheel/diag.md")    # clears it by project
        log = P.read_jsonl(os.path.join(self.root, ".git", "projects-handoffs.jsonl"))
        self.assertEqual(log[-1]["resolves"], ["s1"])
        self.assertEqual(self.hook("stop"), "")                        # resumed: no reminder

    def test_hooks_off(self):
        r = subprocess.run(["python3", TOOL, "hook", "stop"], capture_output=True, text=True,
                           input=json.dumps({"session_id": "s1", "transcript_path": self.transcript,
                                             "cwd": self.repo}),
                           env={**os.environ, **self.env, "PROJECTS_HOOKS": "off"})
        self.assertEqual(r.stdout, "")

    def test_broken_input_is_silent(self):
        r = subprocess.run(["python3", TOOL, "hook", "stop"], capture_output=True, text=True,
                           input="not json", env={**os.environ, **self.env})
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))


if __name__ == "__main__":
    unittest.main()
