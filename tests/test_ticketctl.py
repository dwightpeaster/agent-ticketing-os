import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TICKETCTL = ROOT / "plugins" / "agent-ticketing-os" / "scripts" / "ticketctl.py"


class TicketCtlTest(unittest.TestCase):
    def run_ctl(self, repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TICKETCTL), *args, "--root", str(repo)],
            check=True,
            text=True,
            capture_output=True,
        )

    def load_json(self, repo: Path, relative: str) -> dict:
        return json.loads((repo / relative).read_text(encoding="utf-8"))

    def test_generic_ticket_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.run_ctl(repo, "init")
            self.run_ctl(repo, "new", "--title", "Fix redirect", "--type", "bug", "--priority", "P1", "--area", "app")
            self.run_ctl(repo, "move", "T-0002", "in_progress")
            self.run_ctl(repo, "comment", "T-0002", "Changed auth callback.")
            self.run_ctl(repo, "close", "T-0002", "--resolution", "Fixed and tested.")
            doctor = self.run_ctl(repo, "doctor")

            registry = self.load_json(repo, ".tickets/REGISTRY.json")
            ticket = next(item for item in registry["tickets"] if item["id"] == "T-0002")
            self.assertEqual(ticket["status"], "done")
            self.assertIn("Doctor OK", doctor.stdout)
            self.assertTrue((repo / ".tickets" / "CHANGELOG.md").exists())
            decisions = (repo / ".tickets" / "DECISIONS.md").read_text(encoding="utf-8")
            self.assertIn("## Decision Entry Template", decisions)
            self.assertIn("## Open Questions", decisions)
            self.assertTrue((repo / ".tickets" / "sprints").is_dir())
            self.assertTrue((repo / ".tickets" / "sync").is_dir())
            self.assertIn("## Reproduction Steps", (repo / ".tickets/templates/bug.md").read_text(encoding="utf-8"))
            self.assertIn("## User And Workflow", (repo / ".tickets/templates/feature.md").read_text(encoding="utf-8"))
            self.assertIn("## Risk And Rollback", (repo / ".tickets/templates/repo.md").read_text(encoding="utf-8"))
            self.assertIn("## Recommendation", (repo / ".tickets/templates/research.md").read_text(encoding="utf-8"))

    def test_strict_profile_uses_canonical_engine_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.run_ctl(repo, "init", "--profile", "strict")
            self.run_ctl(repo, "new", "--title", "Plan dashboard", "--type", "feature", "--status", "backlog")
            self.run_ctl(repo, "move", "T-0002", "ready")
            self.run_ctl(repo, "close", "T-0002", "--resolution", "Planned and accepted.")
            self.run_ctl(repo, "doctor")

            config = self.load_json(repo, ".tickets/config.json")
            self.assertEqual(config["ticketing"]["default_status"], "ready")
            self.assertIn("ready", config["ticketing"]["statuses"])
            self.assertNotIn("[T-0002]", (repo / "tickets.md").read_text(encoding="utf-8"))
            self.assertIn("[T-0002]", (repo / "docs/tickets/COMPLETED.md").read_text(encoding="utf-8"))
            self.assertTrue((repo / "docs/tickets/BACKLOG.md").exists())
            self.assertTrue((repo / "docs/tickets/COMPLETED.md").exists())
            roadmap = (repo / "docs/ROADMAP.md").read_text(encoding="utf-8")
            self.assertIn("## Release Milestones", roadmap)
            self.assertIn("## Risk Register", roadmap)
            self.assertIn("## Dependency Map", roadmap)
            self.assertIn("## Decision Template", (repo / "docs/PRODUCT_DECISIONS.md").read_text(encoding="utf-8"))

    def test_sprint_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.run_ctl(repo, "init")
            self.run_ctl(repo, "new", "--title", "Add dashboard filter", "--type", "feature")
            self.run_ctl(repo, "sprint", "start", "--name", "Sprint One", "--goal", "Improve dashboard", "--tickets", "T-0001,T-0002")
            status = self.run_ctl(repo, "sprint", "status")
            self.assertIn("Sprint One", status.stdout)
            self.assertTrue((repo / ".tickets/sprints/current.json").exists())
            self.assertIn("Improve dashboard", (repo / ".tickets/reports/current-sprint.md").read_text(encoding="utf-8"))

            self.run_ctl(repo, "sprint", "close", "--summary", "Dashboard work completed.", "--carryover", "T-0002")
            self.assertFalse((repo / ".tickets/sprints/current.json").exists())
            archives = list((repo / ".tickets/sprints").glob("*-sprint-one.json"))
            self.assertEqual(len(archives), 1)

    def test_operating_docs_and_sync_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.run_ctl(repo, "init")
            self.run_ctl(repo, "operating-init", "--mode", "deep")
            self.run_ctl(repo, "sync-hooks", "--provider", "github", "--external-project", "owner/repo")

            self.assertTrue((repo / "AGENTS.md").exists())
            self.assertTrue((repo / "CLAUDE.md").exists())
            self.assertTrue((repo / ".github/pull_request_template.md").exists())
            pr_template = (repo / ".github/pull_request_template.md").read_text(encoding="utf-8")
            ticket_standards = (repo / "docs/TICKET_STANDARDS.md").read_text(encoding="utf-8")
            qa_guide = (repo / "docs/AGENT_QA_GUIDE.md").read_text(encoding="utf-8")
            handoff = (repo / "docs/AGENT_HANDOFF_TEMPLATE.md").read_text(encoding="utf-8")
            security = (repo / "docs/SECURITY_AGENT_PROTOCOL.md").read_text(encoding="utf-8")
            agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
            claude = (repo / "CLAUDE.md").read_text(encoding="utf-8")
            implementation = (repo / "docs/IMPLEMENTATION_STANDARDS.md").read_text(encoding="utf-8")
            writing = (repo / "docs/WRITING_STANDARDS.md").read_text(encoding="utf-8")
            dead_code = (repo / "docs/DEAD_CODE_REMOVAL.md").read_text(encoding="utf-8")
            repo_map = (repo / "docs/REPO_MAP.md").read_text(encoding="utf-8")
            self.assertIn("## Security And Privacy", pr_template)
            self.assertIn("## Review Notes", pr_template)
            self.assertIn("## Bug Intake Checklist", ticket_standards)
            self.assertIn("## Feature Intake Checklist", ticket_standards)
            self.assertIn("## Validation Levels", qa_guide)
            self.assertIn("## Skipped Validation Template", qa_guide)
            self.assertIn("## Decisions Made", handoff)
            self.assertIn("## Security-Sensitive Areas", security)
            self.assertIn("## Start Here Every Time", agents)
            self.assertIn(".tickets/sync/linear-mcp.md", agents)
            self.assertIn(".tickets/sync/linear-mcp.md", claude)
            self.assertIn("## Before Building New Tooling", implementation)
            self.assertIn("## Tickets And Handoffs", writing)
            self.assertIn("## Before Deleting", dead_code)
            self.assertIn("## Area Agent Docs", repo_map)
            provider = self.load_json(repo, ".tickets/sync/github.json")
            self.assertEqual(provider["mode"], "hybrid")
            self.assertEqual(provider["external_project"], "owner/repo")
            config = self.load_json(repo, ".tickets/config.json")
            self.assertIn("github", config["sync"])

    def test_linear_setup_configures_linear_primary_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.run_ctl(repo, "init")
            self.run_ctl(
                repo,
                "linear-setup",
                "--mode",
                "linear-primary",
                "--team",
                "SalesForce",
                "--project",
                "ProFence Quote System",
            )

            provider = self.load_json(repo, ".tickets/sync/linear.json")
            self.assertEqual(provider["provider"], "linear")
            self.assertEqual(provider["mode"], "external-first")
            self.assertEqual(provider["linear_mode"], "linear-primary")
            self.assertEqual(provider["team"], "SalesForce")
            self.assertEqual(provider["project"], "ProFence Quote System")
            self.assertFalse(provider["create_local_mirror"])
            self.assertIn("bug", provider["labels"])
            self.assertIn("Deployment", provider["work_lanes"])
            self.assertEqual(provider["changelog_title"], "ProFence Quote System Changelog")

            config = self.load_json(repo, ".tickets/config.json")
            self.assertIn("linear", config["sync"])
            policy = (repo / ".tickets/sync/linear-mcp.md").read_text(encoding="utf-8")
            self.assertIn("Mode: `linear-primary`", policy)
            self.assertIn("Linear is the planning source of truth", policy)


if __name__ == "__main__":
    unittest.main()
