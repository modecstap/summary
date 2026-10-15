"""Logging of one CLI run: progress on stderr and the run's ``run.log``."""

import contextlib
import logging
import sys
from collections.abc import Iterator
from pathlib import Path

_PROJECT_LOGGER = "summary"
_RUN_LOG_FILE = "run.log"
_CONSOLE_FORMAT = logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
_RUN_LOG_FORMAT = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")


class RunLogHandler(logging.Handler):
    """Writes every record of a run to ``run.log`` in its run dir, at DEBUG level."""

    def __init__(self) -> None:
        """Set up a handler that buffers records until ``attach`` is called."""
        super().__init__(logging.DEBUG)
        self.setFormatter(_RUN_LOG_FORMAT)
        self._buffer: list[logging.LogRecord] = []
        self._path: Path | None = None
        self._discarded = False

    def emit(self, record: logging.LogRecord) -> None:
        """
        Append the record to ``run.log``, or buffer it while no run dir is attached.

        Records are dropped after the run dir is removed.

        :param record: log record
        """
        if self._discarded:
            return
        if self._path is None:
            self._buffer.append(record)
            return
        try:
            # Open and close per record: a file kept open locks the run dir on Windows,
            # so its removal after a failure would fail; it also keeps every record on
            # disk when the run is interrupted.
            with open(self._path, "a", encoding="utf-8") as file:
                file.write(self.format(record) + "\n")
        except FileNotFoundError:
            self._discarded = True
        except Exception:
            self.handleError(record)

    def attach(self, run_dir: Path) -> None:
        """
        Start writing ``run.log`` in the run dir; never raise.

        Records emitted before ``attach`` are written first, so ``run.log``
        holds the whole run.

        :param run_dir: run dir of the run
        """
        self._path = run_dir / _RUN_LOG_FILE
        buffered, self._buffer = self._buffer, []
        for record in buffered:
            self.emit(record)


@contextlib.contextmanager
def configure(console_level: int) -> Iterator[RunLogHandler]:
    """
    Log the project records of one run to stderr and to a ``RunLogHandler``.

    Only the ``summary`` logger is configured; it stops propagating to the
    root logger until exit, then its handlers, level and propagation are
    restored. Records with a traceback reach stderr only at DEBUG level.

    :param console_level: lowest level shown on stderr

    :return: the handler of ``run.log``; call ``attach`` once the run dir exists
    """
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(console_level)
    console.setFormatter(_CONSOLE_FORMAT)
    if console_level > logging.DEBUG:
        console.addFilter(lambda record: not record.exc_info)
    run_log = RunLogHandler()
    logger = logging.getLogger(_PROJECT_LOGGER)
    level, propagate = logger.level, logger.propagate
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.addHandler(console)
    logger.addHandler(run_log)
    try:
        yield run_log
    finally:
        for handler in (console, run_log):
            logger.removeHandler(handler)
            handler.close()
        logger.setLevel(level)
        logger.propagate = propagate
