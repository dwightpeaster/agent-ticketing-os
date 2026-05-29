# Publishing And Installing

## Public GitHub Repo Shape

The repository is a Codex marketplace source:

```text
agent-ticketing-os/
  .agents/plugins/marketplace.json
  README.md
  plugins/
    agent-ticketing-os/
      .codex-plugin/plugin.json
      SKILL.md
      agents/openai.yaml
      skills/
      references/
```

`.agents/plugins/marketplace.json` points Codex at `plugins/agent-ticketing-os`.

## Install For Codex

```bash
codex plugin marketplace add dwightpeaster/agent-ticketing-os
codex plugin add agent-ticketing-os@agent-ticketing-os
```

Restart Codex after installing.

## Install For Claude Code

Claude Code can use the plugin folder as a skill:

```bash
git clone https://github.com/dwightpeaster/agent-ticketing-os.git
cp -R agent-ticketing-os/plugins/agent-ticketing-os ~/.claude/skills/agent-ticketing-os
```

Restart Claude Code after installing.

## First Use In A Repo

Ask the agent:

```text
$agent-ticketing-os
```

Then answer the setup questions, or tell the agent to use defaults.
