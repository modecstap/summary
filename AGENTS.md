# summary

Python CLI that turns a folder of PDFs and document photos into one summary written by a Cursor agent.

## Commands

PowerShell, project-local `.venv` (Python 3.12); never install into the global interpreter.

- Setup: `python -m venv .venv; .venv\Scripts\python -m pip install -e ".[test]"`
- Test: `.venv\Scripts\python -m pytest`. The first run downloads OCR models (about 13 MB) and needs network.
- Run: from the repo root, `$env:CURSOR_API_KEY="<key>"; .venv\Scripts\python -m summary.main <input_folder> <output_dir>` — summarises the `.pdf/.jpg/.jpeg/.webp` files of the folder with the rules in `rules/summary.md`; each run creates `<output_dir>/<N>/`.

## Planning

Save plans to `.agents/plans/` (gitignored).

## Docs

- [Agent setup / onboarding](.agents/docs/onboarding.md) — read when wiring a new agent or changing the agent layout.
- [docs index](.agents/docs/Index.md) - read always
