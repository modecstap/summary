# Agent setup

Agent-neutral layout shared by all coding agents on the team.

## Layout

- `AGENTS.md` — canonical lean index: project one-liner, commands, constraints, docs links.
- `CLAUDE.md` — pointer (`@AGENTS.md`); Claude-only instructions may follow the import.
- `.agents/docs/` — governing docs, linked from `AGENTS.md` with a "read when…" hook. Plain links only, never `@` imports.
- `.agents/skills/<name>/` — canonical project skills.
- `.agents/plans/` — agent plans, gitignored.

## Hooking up an agent

- **Claude Code** — reads `CLAUDE.md`, not `AGENTS.md`; the pointer covers it. Skills: relative symlink `.claude/skills/<name>` → `../../.agents/skills/<name>`, one per skill.
- **Cursor** — reads `AGENTS.md` natively.
- **Any other agent** — point its entry file at `AGENTS.md` via its include mechanism (or duplicate content if it has none), or re-run `/agentify-project` to research and wire it.

## Windows symlinks

Skill symlinks require `git config core.symlinks true` and Windows Developer Mode (or admin) before cloning; otherwise git checks them out as plain text files.
