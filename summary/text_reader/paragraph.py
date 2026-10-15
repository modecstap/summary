from collections.abc import Sequence

_HYPHENS = ("-", "\u00ad", "\u2010")


def join_lines(lines: Sequence[str]) -> str:
    """Join the source lines of one paragraph into one line, gluing hyphenated word breaks."""
    text = ""
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if not text:
            text = line
        elif _is_word_break(text, line):
            text = text[:-1] + line
        else:
            text = f"{text} {line}"
    return text


def _is_word_break(text: str, next_line: str) -> bool:
    return (
        len(text) >= 2
        and text[-1] in _HYPHENS
        and text[-2].isalpha()
        and next_line[0].islower()
    )
