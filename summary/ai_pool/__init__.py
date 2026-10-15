"""Run one Cursor agent that summarises a list of documents in a new run dir
``<output_dir>/<N>/``.
"""

from .errors import (
    AgentRunError,
    BridgeLaunchError,
    MissingApiKeyError,
    PoolError,
    RulesFileError,
    RunDirError,
    SummaryError,
)
from .launcher import AgentLauncher
from .pool import AIPool
from .result import PoolResult
from .session import AgentSession

__all__ = [
    "AIPool",
    "AgentLauncher",
    "AgentRunError",
    "AgentSession",
    "BridgeLaunchError",
    "MissingApiKeyError",
    "PoolError",
    "PoolResult",
    "RulesFileError",
    "RunDirError",
    "SummaryError",
]
