import argparse
import logging
import sys
import time
from pathlib import Path

from cursor_sdk import ModelParameterValue, ModelSelection

from summary import run_logging
from summary.ai_pool import AIPool, PoolError
from summary.ai_pool.cursor import CursorAgentLauncher
from summary.text_reader import UnreadableDocumentError, UnsupportedFormatError, read_text

logger = logging.getLogger(__name__)

MODEL = ModelSelection(
    id="composer-2.5",
    params=(ModelParameterValue(id="fast", value="false"),),
)
RULES_FILE = Path("rules") / "summary.md"


class DocumentFolderError(Exception):
    """The input folder is missing, not a folder, or has no supported document."""


def run(arguments: list[str] | None = None) -> int:
    """
    Summarise the documents of a folder and print the summary to stdout.

    Reads ``rules/summary.md`` relative to the working dir. Creates a new
    run dir ``<output_dir>/<N>/``. stdout carries only the summary. Log
    records go to stderr at INFO level, DEBUG with ``-v``, WARNING with
    ``-q``; the run dir also gets ``run.log`` with every record at DEBUG
    level. Errors are printed to stderr as ``error: <message>``.

    :param arguments: command-line arguments without the program name;
        ``sys.argv[1:]`` when omitted

    :return: exit code, 0 on success, 1 on an expected error
    """
    parser = argparse.ArgumentParser(
        prog="python -m summary.main",
        description="Summarise the documents of a folder in a new run dir.",
    )
    parser.add_argument(
        "input_folder", help="folder with .pdf, .jpg, .jpeg, .webp documents"
    )
    parser.add_argument(
        "output_dir", help="dir of numbered run dirs <output_dir>/<N>/"
    )
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-v", "--verbose", action="store_true", help="show debug records on stderr"
    )
    verbosity.add_argument(
        "-q", "--quiet", action="store_true", help="show only warnings and errors on stderr"
    )
    options = parser.parse_args(arguments)
    console_level = logging.INFO
    if options.verbose:
        console_level = logging.DEBUG
    if options.quiet:
        console_level = logging.WARNING
    with run_logging.configure(console_level) as run_log:
        return _summarize(options, run_log)


def _summarize(options: argparse.Namespace, run_log: run_logging.RunLogHandler) -> int:
    """
    Run one summary and print its result or error.

    :param options: parsed command-line options
    :param run_log: handler of ``run.log``, attached to the run dir once it exists

    :return: exit code, 0 on success, 1 on an expected error
    """
    started = time.perf_counter()
    logger.info(
        "run started: input folder %s, output dir %s, model %s",
        options.input_folder, options.output_dir, MODEL.id,
    )
    try:
        launcher = CursorAgentLauncher(MODEL)
        launcher.check()
        documents = _read_documents(Path(options.input_folder))
        result = AIPool(launcher, RULES_FILE).summarize(
            documents, Path(options.output_dir), on_run_dir=run_log.attach
        )
    except (DocumentFolderError, UnreadableDocumentError, OSError, PoolError) as error:
        logger.error("run failed: %s", error, exc_info=True)
        print(f"error: {error}", file=sys.stderr)
        return 1
    except Exception:
        logger.exception("run failed unexpectedly")
        raise
    logger.info(
        "run done in %.1fs, run dir %s", time.perf_counter() - started, result.run_dir
    )
    print(result.summary)
    return 0


def _read_documents(folder: Path) -> list[str]:
    """
    Read the supported top-level files of a folder in name order.

    Files of another format and sub-folders are skipped.

    :param folder: input folder

    :raises DocumentFolderError: when ``folder`` is not a folder or has no
        supported file
    :raises UnreadableDocumentError: when a document cannot be decoded
    :raises OSError: when the folder or a document cannot be read

    :return: document texts in name order; empty texts are kept
    """
    if not folder.is_dir():
        raise DocumentFolderError(f"not a folder: {folder}")
    texts = []
    for path in sorted((p for p in folder.iterdir() if p.is_file()), key=lambda p: p.name):
        started = time.perf_counter()
        try:
            text = read_text(path)
        except UnsupportedFormatError:
            logger.info("skipped %s: unsupported format", path.name)
            continue
        logger.info(
            "read %s: %d characters in %.1fs",
            path.name, len(text), time.perf_counter() - started,
        )
        texts.append(text)
    if not texts:
        raise DocumentFolderError(f"no .pdf, .jpg, .jpeg or .webp files in {folder}")
    return texts


def main() -> None:
    """Run the command line and exit with its code."""
    # A redirected stdout on Windows otherwise uses the ANSI code page and garbles Russian text.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(run())


if __name__ == "__main__":
    main()
