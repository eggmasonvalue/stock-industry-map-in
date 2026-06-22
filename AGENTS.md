# AGENTS.md

This repository uses the standard agent-maintained docs system.

## Hard guardrails

- Never commit directly to `main`.
- Always work on a branch and open a PR into `main`.
- Keep `[project].dependencies` empty in `pyproject.toml`; producer runtime deps belong only in dependency groups.
- Do not add changelog/worklog docs; use git history.

## Read routing (read only what you need)

- Read `context/MAP.md` before changing module layout, file locations, or data flow.
- Read `context/DECISIONS.md` before changing behavior shaped by prior tradeoffs.
- Read `context/CONVENTIONS.md` while editing code.
- Check active tasks via `todo list` when starting; `todo claim <id>` before implementing.

## Write triggers (event-based updates)

- Update `context/MAP.md` when modules/files are added, removed, moved, or connected differently.
- Append `context/DECISIONS.md` when you make or reverse a non-obvious tradeoff.
- Update `context/CONVENTIONS.md` when a repeatable rule becomes standard.
- Update `README.md` when user-facing behavior, install flow, or CLI usage changes.

## Do not document

- Changelog/worklog narratives.
- Feature completion checklists.
- Status dashboards.
- Restatements of code that is obvious from reading source.

## CONVENTIONS vs DECISIONS

- `context/CONVENTIONS.md` contains imperative rules only.
- If a rule needs rationale, record the rationale in `context/DECISIONS.md` and keep the convention line imperative.

## Todos ↔ decisions

- Treat todos as stateful task records, not scratch notes.
- Keep implementation notes in the todo body while work is active.
- Before closing a todo that involved a real tradeoff, copy the durable tradeoff into `context/DECISIONS.md`.

## Definition of Done

A task is done only when code, tests/lints, and the matching durable docs (`README.md`, `context/*`) are all updated consistently.
