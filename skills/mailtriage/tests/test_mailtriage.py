"""Tests for skills/mailtriage/bin/mailtriage. Run: python3 -m unittest discover skills/mailtriage/tests

The fixtures are made up; they follow the shape of the Superhuman MCP's list_threads and
list_reminders results."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "..", "bin", "mailtriage")
TODAY = "2026-11-06"
CW = "joi@crankwheel.com"


def thread(tid, subject, sender, date, labels=("INBOX",), splits=("Important",), participants=None,
           count=1):
    return {"thread_id": tid, "subject": subject, "participants": participants or [CW, sender],
            "labels": list(labels), "splits": list(splits), "last_message_at": f"{date}T10:00:00Z",
            "last_message_id": tid + "m", "message_count": count,
            "messages": [{"message_id": tid + "m", "from": sender, "to": [CW], "subject": subject,
                          "labels": list(labels), "sent_at": f"{date}T10:00:00Z"}]}


def entry(tid, project, section="Ready for me", open_=True, remind=None, account=CW, text="x"):
    return {"thread": tid, "account": account, "project": project, "file": project + ".md",
            "section": section, "line": 10, "entry": text, "open": open_, "not_before": remind,
            "gate": None, "nudge": None, "due": None, "waiting": [], "remind": remind}


class TestSnapshot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.threads = [
            thread("t-person-new", "Quick question", "anton@crankwheel.com", "2026-11-05"),
            thread("t-person-old", "Old ask", "Birta <birta@crankwheel.com>", "2026-10-20"),
            thread("t-joi-last", "I replied", CW, "2026-10-01", labels=("SENT",)),
            thread("t-tickler", "Notification: check limits", "calendar-notification@google.com", "2026-10-28"),
            thread("t-nts", "NTS do the thing", "info@emailmeapp.net", "2026-10-26",
                   participants=[CW, "info@emailmeapp.net"]),
            thread("t-bot", "Bounce review", "info@crankwheel.com", "2026-10-25"),
            thread("t-digest", "Klói: Main inbox overview — 2026-11-06", CW, TODAY,
                   participants=[CW]),
            thread("t-invoice", "Invoice 12", "billing@vendor.com", "2026-10-01",
                   labels=("INBOX", "cwinvoices", "ptracked")),
            thread("t-tracked-back", "Came back", "rob@customer.com", "2026-11-04",
                   labels=("INBOX", "ptracked")),
        ]
        # From list_threads(labels=["ptracked"]): the whole label, in the inbox or not.
        self.tracked = [
            thread("t-tracked-back", "Came back", "rob@customer.com", "2026-11-04",
                   labels=("INBOX", "ptracked")),
            thread("t-rem-tracked", "Tracked", "rob@customer.com", "2026-10-30",
                   labels=("ptracked",), splits=()),
            thread("t-dv", "[CrankWheel/protos] PR #1", "notifications@github.com", "2026-11-05",
                   labels=("INBOX", "ptracked"), splits=("Dv",)),
            thread("t-archived", "Archived and tracked", "rob@customer.com", "2026-10-10",
                   labels=("ptracked",), splits=()),
            thread("t-label-only", "Label left behind", "rob@customer.com", "2026-10-10",
                   labels=("ptracked",), splits=()),
        ]
        self.reminders = [
            {"reminder_id": "r1", "thread_id": "t-rem-soon", "subject": "Soon", "remind_at": "2026-11-09T08:00:00Z", "status": "active"},
            {"reminder_id": "r2", "thread_id": "t-rem-far", "subject": "Far", "remind_at": "2027-03-01T08:00:00Z", "status": "active"},
            {"reminder_id": "r3", "thread_id": "draft0087", "subject": "", "remind_at": "2021-01-19T08:00:00Z", "status": "active"},
            {"reminder_id": "r4", "thread_id": "t-rem-tracked", "subject": "Tracked", "remind_at": "2026-11-10T08:00:00Z", "status": "active"},
            {"reminder_id": "r5", "thread_id": "t-rem-mismatch", "subject": "Mismatch", "remind_at": "2026-11-11T08:00:00Z", "status": "active"},
            {"reminder_id": "r7", "thread_id": "t-rem-far-tracked", "subject": "Far but due", "remind_at": "2027-03-01T08:00:00Z", "status": "active"},
            {"reminder_id": "r6", "thread_id": "t-rem-soon", "subject": "Soon", "remind_at": "2026-11-01T08:00:00Z", "status": "triggered"},
        ]
        self.tracker = [
            entry("t-tracked-back", "crankwheel/a", remind="2026-11-20"),
            entry("t-archived", "crankwheel/a", remind="2026-11-12"),
            entry("t-label-only", "crankwheel/a", section="Done", open_=False),
            entry("t-rem-tracked", "crankwheel/b", remind="2026-11-10"),
            entry("t-archived", "crankwheel/d", text="Send the hand-off to @birta (draft in thread)"),
            entry("t-rem-mismatch", "crankwheel/b", remind="2026-11-13"),
            entry("t-gone", "crankwheel/c", account="unknown"),
            entry("t-rem-far-tracked", "crankwheel/c", remind="2026-11-07"),
            entry("t-bella", "bellabooks/x", account="joi@bellabooksai.com"),
        ]
        self.files = []
        for name, data in (("threads.json", {"threads": self.threads, "next_cursor": None}),
                           ("reminders.json", {"reminders": self.reminders}),
                           ("tracked.json", {"threads": self.tracked, "next_cursor": None})):
            path = os.path.join(self.tmp, name)
            with open(path, "w") as f:
                json.dump(data, f)
            self.files.append(path)
        self.projects = os.path.join(self.tmp, "projects")
        with open(self.projects, "w") as f:
            f.write(textwrap.dedent(f"""\
                #!{sys.executable}
                import sys
                assert sys.argv[1:] == ["threads", "--json"], sys.argv
                print({json.dumps(json.dumps(self.tracker))})
                """))
        os.chmod(self.projects, 0o755)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_tool(self, *extra, ok=True):
        r = subprocess.run([sys.executable, TOOL, "snapshot", "--threads", self.files[0],
                            "--reminders", self.files[1], "--tracked", self.files[2],
                            "--projects", self.projects,
                            "--today", TODAY, *extra], capture_output=True, text=True)
        if ok and r.returncode != 0:
            raise AssertionError(r.stderr)
        return r

    def rows(self):
        return {r["thread"]: r for r in json.loads(self.run_tool("--json").stdout)}

    def test_kinds(self):
        rows = self.rows()
        self.assertEqual({t: rows[t]["kind"] for t in ("t-person-new", "t-tickler", "t-nts", "t-bot",
                                                        "t-digest", "t-invoice")},
                         {"t-person-new": "person", "t-tickler": "calendar-tickler", "t-nts": "note-to-self",
                          "t-bot": "automated", "t-digest": "kloi-digest", "t-invoice": "cron-owned"})

    def test_inbox_from_split_even_without_the_label(self):
        rows = self.rows()
        self.assertTrue(rows["t-joi-last"]["in_inbox"])
        self.assertTrue(rows["t-joi-last"]["joi_last"])
        self.assertFalse(rows["t-archived"]["in_inbox"])

    def test_stale_only_for_people_waiting_on_joi(self):
        rows = self.rows()
        self.assertIn("stale", rows["t-person-old"]["flags"])
        self.assertNotIn("stale", rows["t-person-new"]["flags"])
        self.assertNotIn("stale", rows["t-joi-last"]["flags"])
        self.assertNotIn("stale", rows["t-tickler"]["flags"])
        self.assertEqual(rows["t-invoice"]["flags"], [])
        rows = {r["thread"]: r for r in json.loads(self.run_tool("--json", "--stale-days", "30").stdout)}
        self.assertNotIn("stale", rows["t-person-old"]["flags"])

    def test_tracked_threads(self):
        rows = self.rows()
        self.assertIn("tracked-in-inbox", rows["t-tracked-back"]["flags"])
        self.assertIn("archived-no-reminder", rows["t-archived"]["flags"])
        self.assertIn("label-without-entry", rows["t-label-only"]["flags"])
        self.assertNotIn("entry-without-label", rows["t-archived"]["flags"])
        self.assertIn("handoff-pending", rows["t-archived"]["flags"])
        self.assertNotIn("t-dv", rows)                        # Dv split, even with ptracked
        self.assertNotIn("handoff-pending", rows["t-tracked-back"]["flags"])

    def test_reminders(self):
        rows = self.rows()
        self.assertEqual(rows["t-rem-soon"]["reminder"], "2026-11-09")   # triggered one ignored
        self.assertIn("reminder-untracked", rows["t-rem-soon"]["flags"])
        self.assertNotIn("reminder-untracked", rows["t-rem-far"]["flags"])   # beyond 6 weeks
        self.assertIn("broken-reminder", rows["draft0087"]["flags"])
        self.assertNotIn("reminder-untracked", rows["draft0087"]["flags"])
        self.assertEqual(rows["t-rem-tracked"]["flags"], [])
        self.assertIn("date-mismatch", rows["t-rem-mismatch"]["flags"])
        # Snoozed, tracked, but not labelled: known from the complete ptracked list.
        self.assertIn("entry-without-label", rows["t-rem-mismatch"]["flags"])
        self.assertFalse(rows["t-rem-tracked"]["in_inbox"])

    def test_unknown_is_not_no(self):
        rows = self.rows()
        gone = rows["t-gone"]
        self.assertEqual((gone["known"], gone["in_inbox"], gone["tracked_label"]), (False, None, False))
        self.assertIn("state-unknown", gone["flags"])
        self.assertIn("account-unknown", gone["flags"])
        self.assertIn("entry-without-label", gone["flags"])   # not in the complete ptracked list
        self.assertNotIn("t-bella", rows)                     # another account

    def test_text_output(self):
        out = self.run_tool().stdout
        self.assertIn("## INBOX: 9", out)
        self.assertIn("## REMINDERS (not in inbox, due by 2026-12-18): 4", out)
        self.assertIn("## UNKNOWN STATE (look up with get_thread): 1", out)
        other = out.split("## OTHER FLAGGED: ")[1]
        self.assertTrue(other.startswith("1\nt-rem-far-tracked\t"), other)
        self.assertIn("## FLAGS:", out)

    def test_bad_input_fails(self):
        with open(self.files[0], "w") as f:
            json.dump({"nope": []}, f)
        r = self.run_tool(ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not a list_threads result", r.stderr)


if __name__ == "__main__":
    unittest.main()
