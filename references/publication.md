# Publishing And Installing

## Public GitHub Repo Shape

Keep this repository as a skill package:

```text
agent-ticketing-os/
  .codex-plugin/plugin.json
  SKILL.md
  agents/openai.yaml
  scripts/ticketctl.py
  skills/
    agent-ticketing-os/SKILL.md
    agent-ticketing-init/SKILL.md
    agent-ticketing-new/SKILL.md
    agent-ticketing-next/SKILL.md
    agent-ticketing-board/SKILL.md
    agent-ticketing-move/SKILL.md
    agent-ticketing-close/SKILL.md
  references/*.md
  README.md
```

The `skills/` directory exposes the package as multiple related commands. The root `SKILL.md` remains as a broad fallback for clients that install one skill folder at a time.

## Install For Codex As A Plugin Package

```bash
git clone https://github.com/dwightpeaster/agent-ticketing-os.git ~/.agents/plugins/agent-ticketing-os
```

Restart Codex so it discovers the package.

## Install For Claude Code

```bash
git clone https://github.com/dwightpeaster/agent-ticketing-os.git ~/.claude/skills/agent-ticketing-os
```

Restart Claude Code so it discovers the skill package or root fallback skill.

## Install For Codex As A Plain Skill

```bash
git clone https://github.com/dwightpeaster/agent-ticketing-os.git ~/.codex/skills/agent-ticketing-os
```

Restart Codex so it discovers the root fallback skill.

## Project-local Install

For a repo that should carry the skill with it:

```bash
mkdir -p .claude/skills .codex/skills
git submodule add https://github.com/dwightpeaster/agent-ticketing-os.git .claude/skills/agent-ticketing-os
ln -s ../../.claude/skills/agent-ticketing-os .codex/skills/agent-ticketing-os
```

If symlinks are awkward on the target platform, copy the folder into both paths.

## First Use In A Repo

Ask the agent:

```text
$agent-ticketing-os
```

Then answer the setup questions, or tell the agent to use defaults.
