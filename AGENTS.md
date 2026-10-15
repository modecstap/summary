# summary

TODO: one-line project description.

## Commands

PowerShell, project-local `.venv` (Python 3.12); never install into the global interpreter.

- Setup: `python -m venv .venv; .venv\Scripts\python -m pip install -e ".[test]"`
- Test: `.venv\Scripts\python -m pytest`. The first run downloads OCR models (about 13 MB) and needs network.

## Planning

Save plans to `.agents/plans/` (gitignored).

## Docs

- [Agent setup / onboarding](.agents/docs/onboarding.md) — read when wiring a new agent or changing the agent layout.
- [docs index](.agents/docs/Index.md) - read always
