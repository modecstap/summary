import pytest

from summary.text_reader.paragraph import join_lines


@pytest.mark.parametrize(
    ("lines", "expected"),
    [
        (["при-", "чинить"], "причинить"),
        (["при\u00ad", "чинить"], "причинить"),
        (["Санкт-", "Петербург"], "Санкт- Петербург"),
        (["пункт-", "2"], "пункт- 2"),
        (["права —", "это"], "права — это"),
        ([" первая ", "", "вторая"], "первая вторая"),
        ([], ""),
    ],
)
def test_join_lines(lines: list[str], expected: str) -> None:
    assert join_lines(lines) == expected
