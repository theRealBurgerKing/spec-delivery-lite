import copy
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "workflow.py"
SPEC = importlib.util.spec_from_file_location("workflow", SCRIPT)
workflow = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workflow)


def base_change(level="tracked"):
    return {
        "format_version": 2,
        "requirements": [{
            "id": "R-01", "title": "Save a choice", "level": level,
            "level_reasons": ["observable behavior"], "state": "planned",
            "blocked_from": None, "blocked_reason": None,
            "developer": None, "reviewer": None, "self_review_reason": None,
            "approval": {"required": level == "high", "confirmed_by": None, "confirmed_at": None},
            "acceptance_ids": ["AC-01"],
        }],
        "tasks": [] if level == "direct" else [
            {"id": "T-01", "requirement_ids": ["R-01"], "status": "pending"}
        ],
        "acceptance": [{
            "id": "AC-01", "requirement_id": "R-01",
            "criterion": "The choice persists after restart",
            "status": "pending", "evidence": None,
            "waiver_reason": None, "waiver_approved_by": None,
        }],
        "history": [],
    }


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name) / ".spec-delivery-lite" / "changes" / "choice"
        self.directory.mkdir(parents=True)
        self.addCleanup(self.temporary.cleanup)

    def docs(self, high=False, verified=False):
        (self.directory / "brief.md").write_text("# brief", encoding="utf-8")
        (self.directory / "tasks.md").write_text("# tasks", encoding="utf-8")
        if high:
            (self.directory / "design.md").write_text("# design", encoding="utf-8")
        if verified:
            (self.directory / "verification.md").write_text("# evidence\nAC-01: passed", encoding="utf-8")

    def test_direct_needs_only_state_file_and_separate_acceptance(self):
        data = base_change("direct")
        self.assertEqual(workflow.validate(data, self.directory), [])
        workflow.transition(data, self.directory, "R-01", "implementing", "developer", None)
        workflow.transition(data, self.directory, "R-01", "ready_for_acceptance", None, None)
        with self.assertRaisesRegex(workflow.WorkflowError, "Illegal transition"):
            workflow.transition(data, self.directory, "R-01", "accepted", None, None)
        workflow.transition(data, self.directory, "R-01", "accepting", "reviewer", None)
        with self.assertRaisesRegex(workflow.WorkflowError, "must pass"):
            workflow.transition(data, self.directory, "R-01", "accepted", None, None)
        data["acceptance"][0]["status"] = "passed"
        data["acceptance"][0]["evidence"] = "restart scenario: passed"
        workflow.transition(data, self.directory, "R-01", "accepted", None, None)
        self.assertEqual(workflow.validate(data, self.directory), [])

    def test_tracked_requires_completed_tasks_and_verification(self):
        data = base_change()
        self.docs()
        workflow.transition(data, self.directory, "R-01", "implementing", "developer", None)
        with self.assertRaisesRegex(workflow.WorkflowError, "Complete linked tasks"):
            workflow.transition(data, self.directory, "R-01", "ready_for_acceptance", None, None)
        data["tasks"][0]["status"] = "done"
        workflow.transition(data, self.directory, "R-01", "ready_for_acceptance", None, None)
        workflow.transition(data, self.directory, "R-01", "accepting", "reviewer", None)
        data["acceptance"][0]["status"] = "passed"
        data["acceptance"][0]["evidence"] = "test run: passed"
        with self.assertRaisesRegex(workflow.WorkflowError, "verification.md"):
            workflow.transition(data, self.directory, "R-01", "accepted", None, None)
        (self.directory / "verification.md").write_text("# missing AC", encoding="utf-8")
        workflow.transition(data, self.directory, "R-01", "accepted", None, None)
        self.assertTrue(any("omits AC-01" in error for error in workflow.validate(data, self.directory)))
        self.docs(verified=True)
        self.assertEqual(workflow.validate(data, self.directory), [])

    def test_failed_acceptance_returns_to_development(self):
        data = base_change("direct")
        workflow.transition(data, self.directory, "R-01", "implementing", "developer", None)
        workflow.transition(data, self.directory, "R-01", "ready_for_acceptance", None, None)
        workflow.transition(data, self.directory, "R-01", "accepting", "reviewer", None)
        data["acceptance"][0]["status"] = "failed"
        data["acceptance"][0]["evidence"] = "restart loses choice"
        workflow.transition(data, self.directory, "R-01", "changes_requested", None, "retry persistence")
        workflow.transition(data, self.directory, "R-01", "implementing", "developer", None)
        self.assertEqual(data["acceptance"][0]["status"], "pending")
        self.assertTrue(any("changes_requested" in item["event"] for item in data["history"]))

    def test_blocked_resume_is_exact_and_high_risk_needs_approval(self):
        data = base_change("high")
        self.docs(high=True)
        workflow.transition(data, self.directory, "R-01", "blocked", None, "waiting for decision")
        with self.assertRaisesRegex(workflow.WorkflowError, "unblock only"):
            workflow.transition(data, self.directory, "R-01", "implementing", "developer", None)
        workflow.transition(data, self.directory, "R-01", "planned", None, None)
        with self.assertRaisesRegex(workflow.WorkflowError, "recorded approval"):
            workflow.transition(data, self.directory, "R-01", "implementing", "developer", None)
        data["requirements"][0]["approval"].update(
            confirmed_by="user", confirmed_at="2026-09-18T00:00:00Z"
        )
        workflow.transition(data, self.directory, "R-01", "implementing", "developer", None)
        self.assertEqual(workflow.validate(data, self.directory), [])

    def test_mixed_levels_and_invalid_links(self):
        data = base_change()
        self.docs()
        other = copy.deepcopy(base_change("direct")["requirements"][0])
        other.update(id="R-02", acceptance_ids=["AC-02"])
        data["requirements"].append(other)
        ac = copy.deepcopy(data["acceptance"][0])
        ac.update(id="AC-02", requirement_id="R-02")
        data["acceptance"].append(ac)
        self.assertEqual(workflow.validate(data, self.directory), [])
        data["requirements"][1]["acceptance_ids"] = ["AC-01"]
        self.assertTrue(any("invalid acceptance link" in error for error in workflow.validate(data, self.directory)))

    def test_unfilled_template_is_not_a_valid_change(self):
        template = SCRIPT.parents[1] / "assets" / "templates" / "change.yaml"
        data = yaml.safe_load(template.read_text(encoding="utf-8"))
        self.docs()
        errors = workflow.validate(data, self.directory)
        self.assertTrue(any("replace template placeholders" in error for error in errors))

    def test_self_review_needs_recorded_limitation(self):
        data = base_change("direct")
        workflow.transition(data, self.directory, "R-01", "implementing", "same-agent", None)
        workflow.transition(data, self.directory, "R-01", "ready_for_acceptance", None, None)
        with self.assertRaisesRegex(workflow.WorkflowError, "Self-review requires"):
            workflow.transition(data, self.directory, "R-01", "accepting", "same-agent", None)
        workflow.transition(data, self.directory, "R-01", "accepting", "same-agent", "fresh read-only pass")
        self.assertEqual(workflow.validate(data, self.directory), [])
        workflow.transition(data, self.directory, "R-01", "blocked", None, "test environment unavailable")
        workflow.transition(data, self.directory, "R-01", "accepting", None, None)
        self.assertEqual(workflow.validate(data, self.directory), [])

    def test_stale_acceptance_result_is_rejected_before_review(self):
        data = base_change("direct")
        data["acceptance"][0].update(status="passed", evidence="old run")
        self.assertTrue(any("stale acceptance" in error for error in workflow.validate(data, self.directory)))

    def test_cli_persists_progress_and_rejects_premature_archive(self):
        path = self.directory / "change.yaml"
        path.write_text(yaml.safe_dump(base_change("direct")), encoding="utf-8")

        def run(*args):
            return subprocess.run(
                [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
            )

        self.assertNotEqual(run("archive", str(self.directory)).returncode, 0)
        self.assertEqual(run("transition", str(self.directory), "R-01", "implementing", "--actor", "developer").returncode, 0)
        self.assertEqual(run("transition", str(self.directory), "R-01", "ready_for_acceptance").returncode, 0)
        self.assertEqual(run("transition", str(self.directory), "R-01", "accepting", "--actor", "reviewer").returncode, 0)
        self.assertNotEqual(run("transition", str(self.directory), "R-01", "accepted").returncode, 0)
        self.assertEqual(run("acceptance", str(self.directory), "AC-01", "passed", "--evidence", "restart passed").returncode, 0)
        self.assertEqual(run("transition", str(self.directory), "R-01", "accepted").returncode, 0)
        self.assertIn("R-01 [direct] accepted", run("status", str(self.directory)).stdout)
        self.assertEqual(run("archive", str(self.directory)).returncode, 0)
        self.assertFalse(self.directory.exists())
        archived = list((self.directory.parent.parent / "archive").glob("*-choice"))
        self.assertEqual(len(archived), 1)
        self.assertEqual(workflow.load(archived[0] / "change.yaml")["history"][-1]["event"], "Change archived")


if __name__ == "__main__":
    unittest.main()
