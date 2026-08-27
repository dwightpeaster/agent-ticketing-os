"""Shared workflow constants."""

STATUSES = [
    "inbox",
    "backlog",
    "ready",
    "in_progress",
    "review",
    "blocked",
    "done",
    "wont_do",
]

TYPES = ["feature", "bug", "change", "repo", "research", "design", "security"]
PRIORITIES = ["P0", "P1", "P2", "P3", "P4"]

PRIORITY_SCORE = {"P0": 500, "P1": 400, "P2": 300, "P3": 200, "P4": 100}
STATUS_SCORE = {"ready": 50, "backlog": 20, "inbox": 10}

DISPLAY_STATUS = {
    "inbox": "Inbox",
    "backlog": "Backlog",
    "ready": "Ready",
    "in_progress": "In Progress",
    "review": "Review",
    "blocked": "Blocked",
    "done": "Done",
    "wont_do": "Won't Do",
}

OPEN_STATUSES = {"inbox", "backlog", "ready", "in_progress", "review", "blocked"}
ACTIVE_STATUSES = {"ready", "in_progress", "review", "blocked"}
CLOSED_STATUSES = {"done", "wont_do"}

TRANSITIONS = {
    "inbox": {"backlog", "ready"},
    "backlog": {"inbox", "ready"},
    "ready": {"backlog", "in_progress", "blocked"},
    "in_progress": {"ready", "review", "blocked"},
    "review": {"in_progress", "blocked"},
    "blocked": {"backlog", "ready", "in_progress"},
    "done": set(),
    "wont_do": set(),
}

BODY_SECTIONS = [
    ("context", "Context"),
    ("acceptance", "Acceptance Criteria"),
    ("notes", "Implementation Notes"),
    ("validation", "Validation Plan"),
    ("evidence", "Validation Evidence"),
    ("handoff", "Agent Handoff"),
    ("activity", "Activity Log"),
    ("closure", "Closure"),
]

PLACEHOLDER_MARKERS = {
    "context": ["context to be expanded", "describe the problem", "tbd"],
    "acceptance": ["acceptance criteria to be confirmed", "define observable completion", "tbd"],
    "validation": ["validation plan to be confirmed", "run the configured validation", "tbd"],
    "evidence": ["not recorded", "no validation evidence"],
}

TRACKER_PROVIDERS = ["github", "jira", "linear", "custom"]
TRACKER_MODES = ["local-primary", "hybrid", "external-primary"]
