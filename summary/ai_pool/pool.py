from collections.abc import Callable, Sequence
from pathlib import Path

from .errors import AgentRunError, BridgeLaunchError, RulesFileError, SummaryError
from .launcher import AgentLauncher
from .prompt import build_prompt
from .result import PoolResult
from .run_dirs import create_run_dir, document_file, remove_run_dir, summary_file
from .session import AgentSession


class AIPool:
    """Runs one summary agent on a list of documents in a new run dir."""

    def __init__(self, launcher: AgentLauncher, rules: Path) -> None:
        """
        Set up the pool.

        :param launcher: launcher of the agent backend
        :param rules: Markdown summary rules file; read at every
            ``summarize`` call, so edits apply without code changes
        """
        self._launcher = launcher
        self._rules = rules

    def summarize(
        self,
        documents: Sequence[str],
        output_dir: Path,
        on_run_dir: Callable[[Path], None] | None = None,
    ) -> PoolResult:
        """
        Summarise the documents with one agent in a new run dir.

        Creates ``<output_dir>/<N>/`` with one ``document-<n>.txt`` file per
        document; the agent writes ``summary.md`` there. The run dir stays
        after success and after ``SummaryError``. No run dir is left after
        ``RulesFileError``, ``MissingApiKeyError``, ``RunDirError`` or
        ``BridgeLaunchError``.

        :param documents: non-empty list of document texts in input order;
            empty texts are allowed
        :param output_dir: dir of numbered run dirs
        :param on_run_dir: called with the new run dir right after it is
            created and filled; not called when no run dir is created

        :raises ValueError: when ``documents`` is empty
        :raises RulesFileError: when the rules file cannot be read as UTF-8
        :raises MissingApiKeyError: when the backend API key is not set
        :raises RunDirError: when the run dir cannot be created or filled
        :raises BridgeLaunchError: when the agent backend cannot start
        :raises SummaryError: when the agent run fails or leaves no valid
            ``summary.md``

        :return: the summary text and the run dir
        """
        if not documents:
            raise ValueError("no documents to summarize")
        rules = self._read_rules()
        self._launcher.check()
        run_dir = create_run_dir(output_dir, documents)
        if on_run_dir is not None:
            on_run_dir(run_dir)
        files = [document_file(run_dir, n) for n in range(1, len(documents) + 1)]
        prompt = build_prompt(rules, files, summary_file(run_dir))
        try:
            with self._launcher.connect(run_dir) as session:
                self._prompt(session, prompt, run_dir)
        except BridgeLaunchError:
            remove_run_dir(run_dir)
            raise
        return PoolResult(self._read_summary(run_dir), run_dir)

    def _read_rules(self) -> str:
        """
        Read the summary rules file.

        :raises RulesFileError: when the file cannot be read as UTF-8

        :return: rules text
        """
        try:
            return self._rules.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise RulesFileError(
                f"cannot read summary rules {self._rules}: {error}"
            ) from error

    @staticmethod
    def _prompt(session: AgentSession, prompt: str, run_dir: Path) -> None:
        """
        Run the agent on the prompt.

        :param session: backend session of the run
        :param prompt: summary prompt
        :param run_dir: run dir the agent works in

        :raises SummaryError: when the agent run fails or does not finish
        """
        try:
            session.prompt(prompt)
        except AgentRunError as error:
            raise SummaryError(str(error), run_dir) from error

    @staticmethod
    def _read_summary(run_dir: Path) -> str:
        """
        Read the summary the agent wrote.

        :param run_dir: run dir the agent worked in

        :raises SummaryError: when ``summary.md`` is missing, unreadable,
            not UTF-8 or blank

        :return: summary text, unchanged
        """
        path = summary_file(run_dir)
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError as error:
            raise SummaryError("summary.md not written", run_dir) from error
        except UnicodeDecodeError as error:
            raise SummaryError(f"summary.md is not UTF-8: {error}", run_dir) from error
        except OSError as error:
            raise SummaryError(f"cannot read summary.md: {error}", run_dir) from error
        if not text.strip():
            raise SummaryError("summary.md is empty", run_dir)
        return text
