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

Codex plugin installs are user-home scoped by default. For a workspace-only test, use a workspace-specific `CODEX_HOME`:

```bash
mkdir -p .codex-agent-ticketing
CODEX_HOME="$PWD/.codex-agent-ticketing" codex plugin marketplace add dwightpeaster/agent-ticketing-os
CODEX_HOME="$PWD/.codex-agent-ticketing" codex plugin add agent-ticketing-os@agent-ticketing-os
CODEX_HOME="$PWD/.codex-agent-ticketing" codex -C .
```

## Install For Claude Code

From inside Claude Code:

```text
/plugin marketplace add dwightpeaster/agent-ticketing-os
/plugin install agent-ticketing-os@agent-ticketing-os
/reload-plugins
```

These are Claude Code slash commands. Do not run them in a normal shell.

For a repository-only install, use Claude Code's plugin manager UI and choose **Local scope**. Use **Project scope** only when the repo should share the plugin with collaborators through `.claude/settings.json`. Use **User scope** when you want it available across projects.

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
