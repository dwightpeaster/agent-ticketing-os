# Publishing And Installing

## Public GitHub Repo Shape

The repository is a Codex marketplace source:

```text
agent-ticketing-os/
  .agents/plugins/marketplace.json
  .claude-plugin/marketplace.json
  README.md
  plugins/
    agent-ticketing-os/
      .codex-plugin/plugin.json
      .claude-plugin/plugin.json
      SKILL.md
      agents/openai.yaml
      skills/
      references/
```

`.agents/plugins/marketplace.json` points Codex at `plugins/agent-ticketing-os`.
`.claude-plugin/marketplace.json` points Claude Code at the same plugin.

## Install For Codex

```bash
codex plugin marketplace add dwightpeaster/agent-ticketing-os
codex plugin list
codex plugin add agent-ticketing-os@agent-ticketing-os
```

Restart Codex after installing.

## Install For Claude Code

From inside Claude Code:

```text
/plugin marketplace add dwightpeaster/agent-ticketing-os
/plugin install agent-ticketing-os@agent-ticketing-os
/reload-plugins
```

These are Claude Code slash commands. Do not run them in a normal shell.

## First Use In A Repo

In Codex, ask the agent:

```text
$agent-ticketing-os
```

In Claude Code, use the plugin skill namespace:

```text
/agent-ticketing-os:agent-ticketing-os
```

Then answer the setup questions, or tell the agent to use defaults.
