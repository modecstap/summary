from pathlib import Path


class PoolError(Exception):
    """Base of every error the caller of ``AIPool.summarize`` can react to."""


class RulesFileError(PoolError):
    """The summary rules file cannot be read as UTF-8."""


class MissingApiKeyError(PoolError):
    """The API key of the agent backend is not set."""


class RunDirError(PoolError):
    """The run dir cannot be created or filled."""


class BridgeLaunchError(PoolError):
    """The agent backend cannot be launched."""


class SummaryError(PoolError):
    """The agent ran but produced no valid summary; the run dir is kept."""

    def __init__(self, reason: str, run_dir: Path) -> None:
        """
        Set up the error.

        :param reason: why there is no valid summary
        :param run_dir: run dir kept for inspection
        """
        super().__init__(f"{reason} (run dir: {run_dir})")
        self.reason = reason
        self.run_dir = run_dir


class AgentRunError(Exception):
    """The agent run fails or does not finish; the message is the reason."""
