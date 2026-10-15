# AI-summary

## Contents

- [About](#about)
- [Features](#features)
- [Tech stack](#tech-stack)
- [Installation](#installation)
- [Running](#running)
- [Usage](#usage)
- [Project structure](#project-structure)
- [Configuration](#configuration)
- [Testing](#testing)
- [Coding agents](#coding-agents)

## About

AI-summary is a Python command-line tool that turns a folder of PDFs and document photos into one summary written by a Cursor agent.

It extracts the text of each document, from the PDF text layer or with local OCR. Then a local Cursor agent writes one summary of all documents together, following the rules in an editable Markdown file.

## Features

- Reads `.pdf`, `.jpg`, `.jpeg` and `.webp` files.
- Uses the PDF text layer when a page has one; image-only PDF pages fall back to OCR.
- Runs OCR locally, tuned for Cyrillic (East Slavic) text.
- Keeps only the main page column in photos and rejoins paragraphs: line breaks inside a paragraph are joined and hyphenated words are glued.
- Writes one summary for the whole folder, not one per document.
- Takes the summary rules from `rules/summary.md`, which is re-read at every run.
- Keeps each run in a numbered run dir with the extracted texts and `summary.md`.
- Prints the summary to stdout.

## Tech stack

- Python 3.12+
- [PyMuPDF](https://pymupdf.readthedocs.io/) for PDF text and page rendering
- [Pillow](https://python-pillow.org/) for images
- [RapidOCR](https://github.com/RapidAI/RapidOCR) with [onnxruntime](https://onnxruntime.ai/) for local OCR
- Cursor SDK (`cursor-sdk`) for the local agent; the package bundles the bridge it needs
- pytest for tests

## Installation

Prerequisites:

- Python 3.12 or newer.
- Network access on the first OCR use: the OCR model weights (about 13 MB) are downloaded once.
- A Cursor API key, needed only for running, not for tests.

Install into a project-local `.venv`. Never install into the global interpreter.

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[test]"
```

Linux bash:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[test]"
```

## Running

Run from the repo root: `rules/summary.md` is resolved against the working dir. Set `CURSOR_API_KEY` first.

Windows PowerShell:

```powershell
$env:CURSOR_API_KEY="<key>"
.venv\Scripts\python -m summary.main <input_folder> <output_dir>
```

Linux bash:

```bash
export CURSOR_API_KEY="<key>"
.venv/bin/python -m summary.main <input_folder> <output_dir>
```

## Usage

```text
python -m summary.main <input_folder> <output_dir>
```

- `<input_folder>` — folder with the documents.
- `<output_dir>` — dir for numbered run dirs; created if missing.

Only the top-level files of `<input_folder>` are read, in name order. Supported extensions are `.pdf`, `.jpg`, `.jpeg` and `.webp`, in any case. Other files and sub-folders are skipped.

Each run creates a new run dir `<output_dir>/<N>/`, where `N` is the largest existing numeric run dir plus 1, starting at 1:

```text
<output_dir>/
  1/
    document-1.txt
    document-2.txt
    summary.md
  2/
    ...
```

`document-<n>.txt` holds the extracted text of each document. The agent writes `summary.md`, and the summary is also printed to stdout. The run dir is kept after success and after an agent failure.

On error the tool prints `error: <message>` to stderr and exits with code 1. Examples: the input is not a folder, it has no supported file, or `CURSOR_API_KEY` is not set. On success the exit code is 0.

## Project structure

```text
summary/
  main.py          command-line entry point
  text_reader/     text extraction: PDF text layer, OCR, page layout, paragraph reflow
  ai_pool/         run dirs, prompt and agent run for the summary
    cursor/        local Cursor agent launcher (Cursor SDK)
rules/summary.md   summary rules given to the agent
source/            sample documents used by tests
tests/             pytest tests
pyproject.toml     package metadata and dependencies
AGENTS.md          instructions for coding agents (CLAUDE.md points to it)
.agents/           coding agent docs; plans/ is gitignored
```

## Configuration

- `CURSOR_API_KEY` environment variable — required for running. If it is unset or blank, the tool fails before creating a run dir.
- `rules/summary.md` — rules for the summary. Edit it to change the summary without code changes; it is re-read at every run. Currently it asks for a legal review summary in the documents' language with a fixed structure: scope of review, overall assessment, key findings, material risks rated High / Medium / Low / Open, gaps and inconsistencies, and action items.
- Model — set by the `MODEL` constant in `summary/main.py`, currently `composer-2.5`. It is not configurable by CLI or environment variable; change the constant to use another model.

## Testing

Windows PowerShell:

```powershell
.venv\Scripts\python -m pytest
```

Linux bash:

```bash
.venv/bin/python -m pytest
```

The first run downloads the OCR models (about 13 MB) and needs network. Tests replace the Cursor agent with a fake, so they need no `CURSOR_API_KEY` and no Cursor account.

## Coding agents

The entry file for coding agents is [AGENTS.md](AGENTS.md). Agent setup and repo layout: [.agents/docs/onboarding.md](.agents/docs/onboarding.md).
