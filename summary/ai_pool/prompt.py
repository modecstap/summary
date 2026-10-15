from collections.abc import Sequence
from pathlib import Path

PROMPT = """You write a summary of several documents.
Read the documents from these files, in this order:
{documents}
Each file holds the text of one document, extracted from a PDF or recognised from a photo, so it may contain recognition errors.
Write the summary according to the summary rules below.
Write the summary only to the file {summary}. Do not create or modify any other files.

# Summary rules
{rules}
"""


def build_prompt(rules: str, documents: Sequence[Path], summary: Path) -> str:
    """
    Fill the summary prompt.

    :param rules: text of the summary rules file
    :param documents: document files in input order
    :param summary: file the agent writes the summary to

    :return: prompt text
    """
    lines = "\n".join(
        f"{number}. {path.as_posix()}"
        for number, path in enumerate(documents, start=1)
    )
    return PROMPT.format(
        documents=lines, summary=summary.as_posix(), rules=rules
    )
