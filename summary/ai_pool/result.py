from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PoolResult:
    """Summary of one ``summarize`` call and the run dir it was made in."""

    summary: str
    """Text of ``summary.md``, unchanged."""
    run_dir: Path
    """Absolute run dir ``<output_dir>/<N>/``."""
