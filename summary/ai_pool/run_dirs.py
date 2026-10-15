import logging
import shutil
from collections.abc import Sequence
from pathlib import Path

from .errors import RunDirError

logger = logging.getLogger(__name__)

_DOCUMENT_FILE = "document-{number}.txt"
_SUMMARY_FILE = "summary.md"


def create_run_dir(output_dir: Path, documents: Sequence[str]) -> Path:
    """
    Create the next numbered run dir and write one file per document into it.

    The number is one more than the largest numeric sub-dir name of
    ``output_dir`` (``1`` when there is none); other entries are ignored.
    A run dir whose documents cannot be written is removed before raising.

    :param output_dir: dir of numbered run dirs; created when missing
    :param documents: document texts in input order

    :raises RunDirError: when the run dir cannot be created or filled

    :return: the new absolute run dir ``<output_dir>/<N>/``
    """
    run_dir = _next_run_dir(output_dir.resolve())
    try:
        run_dir.mkdir(parents=True)
    except OSError as error:
        raise RunDirError(f"cannot create run dir {run_dir}: {error}") from error
    for number, text in enumerate(documents, start=1):
        path = document_file(run_dir, number)
        try:
            path.write_text(text, encoding="utf-8", newline="")
        except OSError as error:
            remove_run_dir(run_dir)
            raise RunDirError(f"cannot write {path}: {error}") from error
    return run_dir


def remove_run_dir(run_dir: Path) -> None:
    """
    Remove a run dir; never raise, only log a failure.

    :param run_dir: run dir to remove
    """
    try:
        shutil.rmtree(run_dir)
    except OSError as error:
        logger.warning("cannot remove run dir %s: %s", run_dir, error)


def document_file(run_dir: Path, number: int) -> Path:
    """
    Name the file of one input document.

    :param run_dir: run dir
    :param number: 1-based position of the document in the input

    :return: path of the document file
    """
    return run_dir / _DOCUMENT_FILE.format(number=number)


def summary_file(run_dir: Path) -> Path:
    """
    Name the file the agent writes the summary to.

    :param run_dir: run dir

    :return: path of the summary file
    """
    return run_dir / _SUMMARY_FILE


def _next_run_dir(output_dir: Path) -> Path:
    """
    Pick the next numbered run dir.

    :param output_dir: resolved dir of numbered run dirs

    :raises RunDirError: when ``output_dir`` cannot be listed

    :return: ``<output_dir>/<max number + 1>``
    """
    if not output_dir.is_dir():
        return output_dir / "1"
    try:
        names = [entry.name for entry in output_dir.iterdir() if entry.is_dir()]
    except OSError as error:
        raise RunDirError(f"cannot list {output_dir}: {error}") from error
    numbers = [int(name) for name in names if name.isascii() and name.isdigit()]
    return output_dir / str(max(numbers, default=0) + 1)
