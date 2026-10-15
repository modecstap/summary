from collections.abc import Sequence
from dataclasses import dataclass

# Share of the narrower line's width two lines must overlap horizontally to be in one column.
_COLUMN_OVERLAP = 0.5
# Lines on each side of the current line used to measure local margins; absorbs tilt and perspective.
_WINDOW_RADIUS = 3
# Share of the local width by which a line must fall short of the right margin to end a paragraph.
_SHORT_LINE = 0.05
# Share of the local width by which a line must be indented to start a paragraph.
_INDENT = 0.03


@dataclass(frozen=True)
class TextLine:
    """One recognised line with its horizontal extent and top edge, in pixels."""

    text: str
    left: float
    right: float
    top: float


def main_column(lines: Sequence[TextLine]) -> list[TextLine]:
    """Keep only the column with the most text, in input order.

    Lines are in one column when they overlap horizontally. Assumes a single-column page:
    any column other than the largest one (for example a strip of the neighbouring page) is dropped.
    """
    parent = list(range(len(lines)))

    def root(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for a in range(len(lines)):
        for b in range(a + 1, len(lines)):
            if _same_column(lines[a], lines[b]):
                parent[root(a)] = root(b)

    text_by_column: dict[int, int] = {}
    for index, line in enumerate(lines):
        column = root(index)
        text_by_column[column] = text_by_column.get(column, 0) + len(line.text)
    if not text_by_column:
        return []
    largest = max(text_by_column, key=text_by_column.__getitem__)
    return [line for index, line in enumerate(lines) if root(index) == largest]


def split_paragraphs(lines: Sequence[TextLine]) -> list[list[TextLine]]:
    """Group lines in reading order into paragraphs.

    A line starts a new paragraph when the previous line ends short of the right margin
    or when the line itself is indented from the left margin.
    """
    paragraphs: list[list[TextLine]] = []
    for index, line in enumerate(lines):
        if index == 0 or _starts_paragraph(lines, index):
            paragraphs.append([line])
        else:
            paragraphs[-1].append(line)
    return paragraphs


def _same_column(a: TextLine, b: TextLine) -> bool:
    overlap = min(a.right, b.right) - max(a.left, b.left)
    narrower = min(a.right - a.left, b.right - b.left)
    return overlap > _COLUMN_OVERLAP * narrower


def _starts_paragraph(lines: Sequence[TextLine], index: int) -> bool:
    window = lines[max(0, index - _WINDOW_RADIUS) : index + _WINDOW_RADIUS + 1]
    left_margin = min(line.left for line in window)
    right_margin = max(line.right for line in window)
    width = right_margin - left_margin

    previous_window = lines[max(0, index - 1 - _WINDOW_RADIUS) : index + _WINDOW_RADIUS]
    previous_right_margin = max(line.right for line in previous_window)

    previous_is_short = lines[index - 1].right < previous_right_margin - _SHORT_LINE * width
    is_indented = lines[index].left > left_margin + _INDENT * width
    return previous_is_short or is_indented
