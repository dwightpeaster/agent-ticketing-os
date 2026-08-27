import concurrent.futures
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TICKETCTL = ROOT / "plugins" / "agent-ticketing-os" / "scripts" / "ticketctl.py"
PLUGIN = ROOT / "plugins" / "agent-ticketing-os"


class TicketCtlTest(unittest.TestCase):
    def run_ctl(
        self,
        repo: Path,
        *args: str,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TICKETCTL), *args, "--root", str(repo)],
            check=check,
            text=True,
            capture_output=True,
        )

    def install(self, repo: Path, *args: str) -> None:
        self.run_ctl(repo, "install", *args)

    def load_json(self, repo: Path, relative: str) -> dict:
        return json.loads((repo / relative).read_text(encoding="utf-8"))

    def snapshot(self, repo: Path) -> dict[str, str]:
        return {
            str(path.relative_to(repo)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(repo.rglob("*"))
            if path.is_file() and path.name != ".lock"
        }

    def test_clean_install_is_generic_and_has_no_seed_ticket(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.install(repo)

            config = self.load_json(repo, ".tickets/config.json")
            registry = self.load_json(repo, ".tickets/REGISTRY.json")
            self.assertEqual(config["schema_version"], 2)
            self.assertEqual(config["system_version"], "0.4.0")
            self.assertEqual(config["workflow"]["policy"], "standard")
            self.assertEqual(config["ticketing"]["default_status"], "inbox")
            self.assertEqual(config["trackers"], {})
            self.assertEqual(registry["tickets"], [])
            self.assertEqual(registry["generated_from"], "canonical Markdown ticket files")
            self.assertTrue((repo / "docs/agent-workflow/BRANCH_WORKFLOW.md").exists())
            self.assertTrue((repo / "docs/agent-workflow/IMPLEMENTATION_WORKFLOW.md").exists())
            self.assertTrue((repo / "docs/agent-workflow/REVIEW_AND_HANDOFF.md").exists())
            self.assertFalse((repo / "docs/agent-workflow/QA_GUIDE.md").exists())
            agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
            for workflow_doc in (
                "TICKET_STANDARDS.md",
                "BRANCH_WORKFLOW.md",
                "IMPLEMENTATION_WORKFLOW.md",
                "COMMIT_WORKFLOW.md",
                "DEFINITION_OF_DONE.md",
                "REVIEW_AND_HANDOFF.md",
            ):
                self.assertIn(workflow_doc, agents)
            self.assertIn("context --next", agents)
            self.assertIn("### Load By Phase", agents)
            self.assertIn("Do not silently expand scope", agents)
            self.assertIn("Never store secrets", agents)
            self.assertIn("No synchronization is automatic", agents)
            self.assertIn("### Handoff", agents)
            generated = "\n".join(path.read_text(encoding="utf-8") for path in repo.rglob("*.md"))
            for private_default in ("Salesforce", "Quote Workflow", "Assistant Behavior"):
                self.assertNotIn(private_default, generated)

    def test_install_is_idempotent_and_preserves_custom_workflow_docs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.install(repo)
            before = self.snapshot(repo)
            self.install(repo)
            self.assertEqual(before, self.snapshot(repo))

            branch_doc = repo / "docs/agent-workflow/BRANCH_WORKFLOW.md"
            branch_doc.write_text(branch_doc.read_text(encoding="utf-8") + "\nCustom repository rule.\n", encoding="utf-8")
            self.install(repo)
            self.assertIn("Custom repository rule.", branch_doc.read_text(encoding="utf-8"))
            agents_path = repo / "AGENTS.md"
            agents = agents_path.read_text(encoding="utf-8")
            self.assertEqual(agents.count("<!-- agent-ticketing-os:start -->"), 1)

            before_managed, remainder = agents.split("<!-- agent-ticketing-os:start -->", 1)
            _managed, after_managed = remainder.split("<!-- agent-ticketing-os:end -->", 1)
            agents_path.write_text(
                f"{before_managed}<!-- agent-ticketing-os:start -->\n"
                "## Agent Ticketing OS\n\n- Read the board before work.\n"
                f"<!-- agent-ticketing-os:end -->{after_managed.rstrip()}\n\n"
                "User-owned repository instruction.\n",
                encoding="utf-8",
            )
            self.install(repo)
            upgraded_agents = agents_path.read_text(encoding="utf-8")
            self.assertIn("Do not silently expand scope", upgraded_agents)
            self.assertIn("User-owned repository instruction.", upgraded_agents)
            self.assertEqual(upgraded_agents.count("<!-- agent-ticketing-os:start -->"), 1)
            upgraded_snapshot = self.snapshot(repo)
            self.install(repo)
            self.assertEqual(upgraded_snapshot, self.snapshot(repo))

    def test_explicit_policy_changes_apply_to_existing_installations(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.install(repo)

            changed = json.loads(self.run_ctl(repo, "install", "--profile", "guarded", "--json").stdout)
            self.assertEqual(changed["policy"], "guarded")
            self.assertEqual(self.load_json(repo, ".tickets/config.json")["workflow"]["policy"], "guarded")
            guarded_snapshot = self.snapshot(repo)

            self.install(repo)
            self.assertEqual(guarded_snapshot, self.snapshot(repo))
            self.assertEqual(self.load_json(repo, ".tickets/config.json")["workflow"]["policy"], "guarded")

            changed = json.loads(self.run_ctl(repo, "install", "--profile", "standard", "--json").stdout)
            self.assertEqual(changed["policy"], "standard")
            self.assertEqual(self.load_json(repo, ".tickets/config.json")["workflow"]["policy"], "standard")

    def test_install_rejects_operating_docs_outside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            repo = workspace / "repo"
            repo.mkdir()
            self.install(repo)
            config_path = repo / ".tickets/config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["operating"]["docs_root"] = "../outside"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            rejected = self.run_ctl(repo, "install", check=False)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("outside the repository", rejected.stderr)
            self.assertFalse((workspace / "outside").exists())

    def test_symbolic_link_ticket_files_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.install(repo)
            linked_ticket = repo / ".tickets/tickets/T-9999-linked.md"
            linked_ticket.symlink_to(repo / "missing-ticket-target.md")

            rejected = self.run_ctl(repo, "doctor", check=False)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("symbolic-link ticket files", rejected.stderr)

    def test_markdown_is_canonical_and_registry_is_derived(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.install(repo)
            self.run_ctl(
                repo,
                "new",
                "--title",
                "Original title",
                "--type",
                "repo",
                "--area",
                "repo",
                "--status",
                "ready",
                "--context",
                "A concrete repository problem.",
                "--acceptance",
                "- [ ] The behavior is verified.",
                "--validation",
                "- [ ] Run the targeted test.",
            )
            ticket_path = next((repo / ".tickets/tickets").glob("T-0001-*.md"))
            text = ticket_path.read_text(encoding="utf-8")
            metadata = json.loads(text.split("---", 2)[1])
            for omitted_default in (
                "severity",
                "owner",
                "estimate",
                "risk",
                "labels",
                "depends_on",
                "blocks",
                "source",
                "external_ids",
            ):
                self.assertNotIn(omitted_default, metadata)
            text = text.replace('"title": "Original title"', '"title": "Edited in Markdown"')
            text = text.replace("# T-0001: Original title", "# T-0001: Edited in Markdown")
            ticket_path.write_text(text, encoding="utf-8")

            self.run_ctl(repo, "render")
            registry = self.load_json(repo, ".tickets/REGISTRY.json")
            self.assertEqual(registry["tickets"][0]["title"], "Edited in Markdown")
            self.assertNotIn("body", registry["tickets"][0])

            ticket_path.write_text(ticket_path.read_text(encoding="utf-8") + "\n## Unsupported Custom Section\n\nPreserve me.\n", encoding="utf-8")
            rejected = self.run_ctl(repo, "render", check=False)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("unsupported level-two section", rejected.stderr)
            self.assertIn("Preserve me.", ticket_path.read_text(encoding="utf-8"))

    def test_context_packets_are_compact_and_progressive(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.install(repo)
            self.run_ctl(
                repo,
                "new",
                "--title",
                "Compact working packet",
                "--type",
                "bug",
                "--priority",
                "P1",
                "--area",
                "app",
                "--status",
                "ready",
                "--context",
                "Users cannot complete sign in after a valid callback.",
                "--acceptance",
                "- [ ] A valid callback signs the user in.\n- [ ] Invalid callbacks remain rejected.",
                "--validation",
                "- [ ] Run the focused authentication tests.",
            )
            self.run_ctl(repo, "new", "--title", "Deferred cleanup", "--status", "backlog")

            before_context = self.snapshot(repo)
            session = json.loads(self.run_ctl(repo, "context", "--json").stdout)
            self.assertEqual(session["next"]["id"], "T-0001")
            self.assertEqual(session["queue"], {"backlog": 1, "inbox": 0})
            self.assertEqual(session["active"], [])

            human = self.run_ctl(repo, "context", "--next").stdout
            self.assertIn("T-0001 · Ready · P1 · bug · app", human)
            self.assertIn("Goal: Users cannot complete sign in", human)
            self.assertIn("Next action:", human)
            self.assertNotIn("Activity Log", human)
            self.assertNotIn("Implementation Notes", human)
            self.assertLessEqual(len(human.split()), 180)

            machine = self.run_ctl(repo, "context", "T-0001", "--json").stdout.strip()
            packet = json.loads(machine)
            self.assertNotIn("activity", packet)
            self.assertNotIn("created", packet)
            self.assertNotIn("updated", packet)
            self.assertNotIn("notes", packet)
            self.assertNotIn("handoff", packet)
            self.assertNotIn("\n", machine)
            self.assertEqual(before_context, self.snapshot(repo))

            conflict = self.run_ctl(repo, "context", "T-0001", "--next", check=False)
            self.assertNotEqual(conflict.returncode, 0)
            self.assertIn("ticket id or --next", conflict.stderr)

            self.run_ctl(repo, "validate", "T-0001", "--result", "failed", "--command", "focused tests")
            self.run_ctl(repo, "validate", "T-0001", "--result", "passed", "--command", "focused tests")
            packet = json.loads(self.run_ctl(repo, "context", "T-0001", "--json").stdout)
            self.assertIn("[PASSED]", packet["latest_evidence"])
            self.assertNotIn("[FAILED]", packet["latest_evidence"])

    def test_generated_ticket_links_are_relative_to_each_view(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.install(repo)
            self.run_ctl(
                repo,
                "new",
                "--title",
                "Linked from generated views",
                "--status",
                "ready",
            )
            self.run_ctl(
                repo,
                "sprint",
                "start",
                "--name",
                "Link test",
                "--goal",
                "Verify generated links",
                "--tickets",
                "T-0001",
            )
            filename = "T-0001-linked-from-generated-views.md"
            self.assertIn(f"(tickets/{filename})", (repo / ".tickets/BOARD.md").read_text(encoding="utf-8"))
            self.assertIn(f"(tickets/{filename})", (repo / ".tickets/BACKLOG.md").read_text(encoding="utf-8"))
            self.assertIn(f"(../tickets/{filename})", (repo / ".tickets/reports/current-sprint.md").read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.install(repo, "--profile", "guarded")
            self.run_ctl(repo, "new", "--title", "Deferred split view")
            self.run_ctl(
                repo,
                "new",
                "--title",
                "Working split view",
                "--status",
                "ready",
                "--context",
                "Verify the root working-board link.",
                "--acceptance",
                "- [ ] The link resolves.",
                "--validation",
                "- [ ] Inspect the generated file.",
            )
            self.assertIn(
                "(.tickets/tickets/T-0002-working-split-view.md)",
                (repo / "tickets.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "(../../.tickets/tickets/T-0001-deferred-split-view.md)",
                (repo / "docs/tickets/BACKLOG.md").read_text(encoding="utf-8"),
            )

    def test_guarded_policy_enforces_readiness_and_closure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.install(repo, "--profile", "guarded")
            self.run_ctl(repo, "new", "--title", "Guarded ticket", "--type", "feature", "--area", "app")

            blocked = self.run_ctl(repo, "move", "T-0001", "ready", check=False)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("not ready", blocked.stderr)

            self.run_ctl(
                repo,
                "edit",
                "T-0001",
                "--context",
                "Users need a deterministic guarded workflow.",
                "--acceptance",
                "- [ ] Guarded transitions are enforced.",
                "--validation",
                "- [ ] Run the guarded lifecycle test.",
            )
            self.run_ctl(repo, "move", "T-0001", "ready")
            self.run_ctl(repo, "move", "T-0001", "in_progress")
            self.run_ctl(repo, "move", "T-0001", "review")

            blocked_close = self.run_ctl(repo, "close", "T-0001", "--resolution", "Implemented.", check=False)
            self.assertNotEqual(blocked_close.returncode, 0)
            self.assertIn("validation evidence", blocked_close.stderr)
            skipped = self.run_ctl(repo, "validate", "T-0001", "--result", "skipped", check=False)
            self.assertNotEqual(skipped.returncode, 0)
            self.assertIn("Skipped validation requires --notes", skipped.stderr)
            self.run_ctl(repo, "validate", "T-0001", "--result", "failed", "--command", "python3 -m unittest")
            failed_close = self.run_ctl(repo, "close", "T-0001", "--resolution", "Implemented.", check=False)
            self.assertNotEqual(failed_close.returncode, 0)
            self.assertIn("no passed result or documented skip", failed_close.stderr)
            self.run_ctl(repo, "validate", "T-0001", "--result", "passed", "--command", "python3 -m unittest")
            unchecked_close = self.run_ctl(repo, "close", "T-0001", "--resolution", "Implemented.", check=False)
            self.assertNotEqual(unchecked_close.returncode, 0)
            self.assertIn("acceptance criteria remain unchecked", unchecked_close.stderr)
            self.run_ctl(repo, "edit", "T-0001", "--acceptance", "- [x] Guarded transitions are enforced.")
            self.run_ctl(repo, "close", "T-0001", "--resolution", "Implemented and tested.")
            doctor = self.run_ctl(repo, "doctor")
            self.assertIn("Doctor OK", doctor.stdout)

    def test_next_uses_only_ready_dependency_clear_tickets(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.install(repo)
            self.run_ctl(repo, "new", "--title", "Urgent untriaged", "--priority", "P0", "--status", "backlog")
            self.run_ctl(repo, "new", "--title", "Ready work", "--priority", "P2", "--status", "ready")
            self.assertTrue(self.run_ctl(repo, "next").stdout.startswith("T-0002"))

            self.run_ctl(repo, "new", "--title", "Required foundation", "--priority", "P3", "--status", "ready")
            self.run_ctl(repo, "link", "T-0002", "depends-on", "T-0003")
            board = (repo / ".tickets/BOARD.md").read_text(encoding="utf-8")
            waiting = board.split("## Waiting On Dependencies", 1)[1].split("## Ready", 1)[0]
            ready = board.split("## Ready", 1)[1]
            self.assertIn("T-0002", waiting)
            self.assertIn("waiting on T-0003", waiting)
            self.assertNotIn("T-0002", ready)
            self.assertIn("T-0003", ready)
            self.assertTrue(self.run_ctl(repo, "next").stdout.startswith("T-0003"))
            self.run_ctl(repo, "close", "T-0003", "--resolution", "Foundation completed.")
            board = (repo / ".tickets/BOARD.md").read_text(encoding="utf-8")
            waiting = board.split("## Waiting On Dependencies", 1)[1].split("## Ready", 1)[0]
            ready = board.split("## Ready", 1)[1]
            self.assertNotIn("T-0002", waiting)
            self.assertIn("T-0002", ready)
            self.assertTrue(self.run_ctl(repo, "next").stdout.startswith("T-0002"))

    def test_closed_creation_and_dependency_cycles_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.install(repo)
            closed = self.run_ctl(repo, "new", "--title", "Invalid closed ticket", "--status", "done", check=False)
            self.assertNotEqual(closed.returncode, 0)
            self.assertIn("use close", closed.stderr)

            self.run_ctl(repo, "new", "--title", "First", "--status", "ready")
            self.run_ctl(repo, "new", "--title", "Second", "--status", "ready")
            self.run_ctl(repo, "link", "T-0001", "depends-on", "T-0002")
            cycle = self.run_ctl(repo, "link", "T-0002", "depends-on", "T-0001", check=False)
            self.assertNotEqual(cycle.returncode, 0)
            self.assertIn("dependency cycle", cycle.stderr)

    def test_concurrent_ticket_creation_allocates_unique_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.install(repo)

            def create(index: int) -> subprocess.CompletedProcess[str]:
                return self.run_ctl(repo, "new", "--title", f"Concurrent ticket {index}", "--type", "repo", "--area", "repo")

            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                results = list(executor.map(create, range(12)))
            self.assertTrue(all(result.returncode == 0 for result in results))
            registry = self.load_json(repo, ".tickets/REGISTRY.json")
            ids = [ticket["id"] for ticket in registry["tickets"]]
            self.assertEqual(len(ids), 12)
            self.assertEqual(len(set(ids)), 12)
            self.assertEqual(ids, [f"T-{number:04d}" for number in range(1, 13)])

    def test_schema_one_migration_backs_up_and_preserves_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            ticket_dir = repo / ".tickets/tickets"
            ticket_dir.mkdir(parents=True)
            config = {
                "project": {
                    "name": "Legacy",
                    "profile": "strict",
                    "mission": "Track work with one readable working board, a deferred backlog, one-line completed archives, and strict agent handoffs.",
                },
                "ticketing": {
                    "prefix": "T",
                    "default_status": "ready",
                    "default_priority": "P2",
                    "layout": "split-board",
                    "areas": ["backend", "mobile", "dashboard", "public", "notifications", "security", "deployment", "docs", "repo"],
                    "phase_ranges": {"T-0100": "backend domain"},
                    "display_statuses": {"ready": "Ready"},
                },
                "validation": {
                    "commands": [],
                    "definition_of_done": ["The change maps to one active ticket"],
                },
            }
            registry_ticket = {
                "id": "T-0001",
                "title": "Legacy ticket",
                "type": "repo",
                "status": "ready",
                "priority": "P2",
                "area": "repo",
                "created": "2026-01-01T00:00:00+00:00",
                "updated": "2026-01-01T00:00:00+00:00",
                "body": {"context": "Registry context."},
                "activity": [],
                "file": ".tickets/tickets/T-0001-legacy-ticket.md",
            }
            (repo / ".tickets/config.json").write_text(json.dumps(config), encoding="utf-8")
            (repo / ".tickets/REGISTRY.json").write_text(json.dumps({"next_number": 2, "tickets": [registry_ticket]}), encoding="utf-8")
            legacy = """---
id: T-0001
title: Legacy ticket
type: repo
status: ready
priority: P2
area: repo
created: 2026-01-01T00:00:00+00:00
updated: 2026-01-01T00:00:00+00:00
---

# T-0001: Legacy ticket

## Context
Manually improved legacy context.

## Acceptance Criteria
- [ ] Preserve this ticket.

## Validation Plan
- [ ] Run migration tests.
"""
            (ticket_dir / "T-0001-legacy-ticket.md").write_text(legacy, encoding="utf-8")

            dry = self.run_ctl(repo, "migrate", "--dry-run", "--json")
            self.assertTrue(json.loads(dry.stdout)["needs_migration"])
            self.install(repo)
            migrated_config = self.load_json(repo, ".tickets/config.json")
            self.assertEqual(migrated_config["schema_version"], 2)
            self.assertEqual(migrated_config["workflow"]["policy"], "guarded")
            self.assertEqual(migrated_config["ticketing"]["default_status"], "inbox")
            self.assertEqual(migrated_config["ticketing"]["areas"], ["app", "api", "data", "tests", "docs", "repo"])
            self.assertNotIn("phase_ranges", migrated_config["ticketing"])
            self.assertNotIn("display_statuses", migrated_config["ticketing"])
            self.assertNotIn("strict agent handoffs", migrated_config["project"]["mission"])
            self.assertTrue(list((repo / ".tickets/backups").glob("schema-v1-*")))
            migrated_text = (ticket_dir / "T-0001-legacy-ticket.md").read_text(encoding="utf-8")
            self.assertIn("Manually improved legacy context.", migrated_text)
            self.assertTrue(migrated_text.startswith("---\n{"))

    def test_sprint_report_uses_live_ticket_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.install(repo)
            self.run_ctl(repo, "new", "--title", "Sprint ticket", "--status", "ready")
            self.run_ctl(repo, "sprint", "start", "--name", "Sprint One", "--goal", "Improve reliability", "--tickets", "T-0001")
            report = (repo / ".tickets/reports/current-sprint.md").read_text(encoding="utf-8")
            self.assertIn("## Ready", report)
            self.run_ctl(repo, "move", "T-0001", "in_progress")
            report = (repo / ".tickets/reports/current-sprint.md").read_text(encoding="utf-8")
            self.assertIn("## In Progress", report)
            self.run_ctl(repo, "sprint", "close", "--summary", "Sprint reviewed.")
            self.assertFalse((repo / ".tickets/sprints/current.json").exists())
            self.assertTrue(list((repo / ".tickets/sprints").glob("*-sprint-one.json")))

    def test_extended_operating_profile_adds_only_optional_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.install(repo, "--operating", "extended")
            docs = repo / "docs/agent-workflow"
            self.assertTrue((docs / "QA_GUIDE.md").exists())
            self.assertTrue((docs / "RELEASE_RUNBOOK.md").exists())
            self.assertTrue((docs / "SECURITY_WORKFLOW.md").exists())
            config = self.load_json(repo, ".tickets/config.json")
            self.assertEqual(config["operating"]["profile"], "extended")

    def test_tracker_setup_is_explicit_guidance_not_automatic_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.install(repo)
            self.run_ctl(repo, "tracker-setup", "--provider", "linear", "--mode", "external-primary", "--external-project", "Product")
            tracker = self.load_json(repo, ".tickets/trackers/linear.json")
            self.assertFalse(tracker["automatic_sync"])
            self.assertNotIn("labels", tracker)
            self.assertNotIn("work_lanes", tracker)
            guidance = (repo / ".tickets/trackers/linear.md").read_text(encoding="utf-8")
            self.assertIn("does not install a background agent", guidance)
            self.assertFalse((repo / ".tickets/sync").exists())
            before = self.snapshot(repo)
            self.run_ctl(repo, "tracker-setup", "--provider", "linear", "--mode", "external-primary", "--external-project", "Product")
            self.assertEqual(before, self.snapshot(repo))

            self.run_ctl(repo, "new", "--title", "Externally tracked work")
            self.run_ctl(repo, "edit", "T-0001", "--external-id", "linear=ENG-42")
            ticket = json.loads(self.run_ctl(repo, "show", "T-0001", "--json").stdout)
            self.assertEqual(ticket["external_ids"], {"linear": "ENG-42"})
            self.assertEqual(ticket["severity"], "")
            self.assertEqual(ticket["estimate"], "")
            self.run_ctl(repo, "edit", "T-0001", "--remove-external-id", "linear")
            ticket = json.loads(self.run_ctl(repo, "show", "T-0001", "--json").stdout)
            self.assertEqual(ticket["external_ids"], {})

    def test_public_skill_surface_and_release_versions(self) -> None:
        skill_files = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
        names = []
        for path in skill_files:
            lines = path.read_text(encoding="utf-8").splitlines()
            name = next(line.split(":", 1)[1].strip() for line in lines if line.startswith("name:"))
            names.append(name)
            metadata_path = path.parent / "agents/openai.yaml"
            self.assertTrue(metadata_path.exists(), f"missing UI metadata for {name}")
            metadata = metadata_path.read_text(encoding="utf-8")
            self.assertIn(f"$" + name, metadata)
            self.assertIn("allow_implicit_invocation: true", metadata)
            short = re.search(r'^  short_description: "(.+)"$', metadata, re.MULTILINE)
            self.assertIsNotNone(short)
            self.assertGreaterEqual(len(short.group(1)), 25)
            self.assertLessEqual(len(short.group(1)), 64)
        self.assertEqual(
            names,
            [
                "agent-operating-review",
                "agent-ticketing",
                "agent-ticketing-os",
                "agent-ticketing-sprint",
                "agent-ticketing-tracker",
            ],
        )
        codex_manifest = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        claude_manifest = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(codex_manifest["version"], "0.4.0")
        self.assertEqual(claude_manifest["version"], "0.4.0")
        self.assertEqual(marketplace["plugins"][0]["version"], "0.4.0")
        self.assertIn("$agent-ticketing-os", codex_manifest["interface"]["defaultPrompt"])

    def test_skill_activation_cases_and_context_budgets(self) -> None:
        skill_files = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
        skill_names = {path.parent.name for path in skill_files}
        cases = json.loads((ROOT / "tests/skill_activation_cases.json").read_text(encoding="utf-8"))
        covered = {case["expected_skill"] for case in cases if case["expected_skill"]}
        self.assertEqual(covered, skill_names)
        self.assertTrue(any(case["expected_skill"] is None for case in cases))
        self.assertTrue(any(not case["mutation_allowed"] for case in cases))
        for case in cases:
            self.assertTrue(case["prompt"].strip())
            self.assertIn(case["expected_skill"], {*skill_names, None})

        for path in skill_files:
            content = path.read_text(encoding="utf-8")
            description = next(
                line.split(":", 1)[1].strip()
                for line in content.splitlines()
                if line.startswith("description:")
            )
            self.assertLessEqual(len(description), 400, path)
            self.assertLessEqual(len(re.findall(r"\b[\w$-]+\b", content)), 320, path)

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            self.install(repo)
            agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
            managed = agents.split("<!-- agent-ticketing-os:start -->", 1)[1].split(
                "<!-- agent-ticketing-os:end -->", 1
            )[0]
            self.assertGreaterEqual(len(managed.split()), 200)
            self.assertLessEqual(len(managed.split()), 300)
            implementation = (repo / "docs/agent-workflow/IMPLEMENTATION_WORKFLOW.md").read_text(
                encoding="utf-8"
            )
            self.assertLessEqual(len(implementation.split()), 350)
            self.assertIn("## Safe Removal", implementation)


if __name__ == "__main__":
    unittest.main()
