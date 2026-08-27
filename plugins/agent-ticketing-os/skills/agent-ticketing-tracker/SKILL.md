---
name: agent-ticketing-tracker
description: Configure optional external tracker guidance for Agent Ticketing OS and mediate authorized connector actions during an active agent session. Use when the user asks to connect, map, or work with GitHub Issues, Jira, Linear, or another tracker. This skill does not install a background agent or automatic synchronization.
---

# Agent Ticketing Tracker

Read `references/tracker-setup.md` before configuring a provider or resolving a conflict.

Configure guidance only after the user selects the provider and source-of-truth mode:

```bash
python3 <package-root>/scripts/ticketctl.py tracker-setup --root . --provider <provider> --mode <local-primary|hybrid|external-primary> --external-project "<project>"
```

This stores local connector policy. It does not poll, push, pull, or reconcile automatically.

After an authorized connector creates or matches an external record, store the stable id through the engine:

```bash
python3 <package-root>/scripts/ticketctl.py edit T-0001 --root . --external-id linear=ENG-42
```

When an authorized connector is available during the current session:

1. Read existing external records before creating anything.
2. Match stored external ids before matching titles.
3. Show conflicts before writing either side.
4. Confirm bulk, destructive, or structural changes.
5. Record the resulting external id through `edit --external-id`; the engine adds the activity note.

If no connector is available, leave the local ticket unchanged and explain what remains manual.
