from summary.text_reader.page_layout import TextLine, main_column, split_paragraphs


def _line(text: str, left: float, right: float, top: float = 0) -> TextLine:
    return TextLine(text=text, left=left, right=right, top=top)


def test_main_column_drops_neighbour_strip() -> None:
    strip = [_line("сосед", 0, 170, top) for top in range(0, 100, 20)]
    page = [_line("основной текст страницы", 160, 740, top) for top in range(0, 200, 20)]
    assert main_column(strip + page) == page


def test_main_column_empty() -> None:
    assert main_column([]) == []


def test_split_paragraphs_by_short_line_and_indent() -> None:
    lines = [
        _line("a", 100, 500),
        _line("b", 100, 500),
        _line("c", 100, 300),
        _line("d", 100, 500),
        _line("e", 130, 500),
        _line("f", 100, 500),
    ]
    paragraphs = [[line.text for line in group] for group in split_paragraphs(lines)]
    assert paragraphs == [["a", "b", "c"], ["d"], ["e", "f"]]
