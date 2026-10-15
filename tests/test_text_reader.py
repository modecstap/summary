import logging
import shutil
from pathlib import Path

import pymupdf
import pytest
from PIL import Image

from summary.text_reader import UnreadableDocumentError, UnsupportedFormatError, read_text

SOURCE = Path(__file__).parents[1] / "source"
PDF_SAMPLE = SOURCE / "5_grazhdanskijj_kodeks_rossijjskojj_federacii_chast_pervaya.pdf"
JPG_SAMPLE = SOURCE / "3_fc21cff16e05519324936c9c89d642bb_1460720162.jpg"
WEBP_SAMPLE = SOURCE / "e6ce831e-6346-4397-b2a0-47e9470304a6.webp"

JPG_HEADINGS = [
    "Статья 9. Осуществление гражданских прав",
    "Статья 10. Пределы осуществления гражданских прав",
    "Статья 11. Судебная защита гражданских прав",
    "Статья 12. Способы защиты гражданских прав",
]


@pytest.fixture(scope="module")
def jpg_text() -> str:
    return read_text(JPG_SAMPLE)


@pytest.fixture(scope="module")
def webp_text() -> str:
    return read_text(WEBP_SAMPLE)


@pytest.fixture
def fake_ocr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("summary.text_reader.ocr.recognise_image", lambda image: "ok")


def test_pdf_text_layer_without_ocr(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def fail(image: Image.Image) -> str:
        raise AssertionError("OCR must not run for pages with a text layer")

    monkeypatch.setattr("summary.text_reader.ocr.recognise_image", fail)
    caplog.set_level(logging.DEBUG, logger="summary.text_reader.pdf")
    text = read_text(PDF_SAMPLE)
    assert "Статья 13. Признание недействительным акта государственного органа или" in text
    assert f"{PDF_SAMPLE.name} page 1: text layer" in caplog.messages


def test_image_only_pdf_uses_ocr(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    scan = tmp_path / "scan.pdf"
    with pymupdf.open(JPG_SAMPLE) as image_document:
        scan.write_bytes(image_document.convert_to_pdf())
    caplog.set_level(logging.DEBUG, logger="summary.text_reader.pdf")
    assert JPG_HEADINGS[0] in read_text(scan)
    assert "scan.pdf page 1: OCR" in caplog.messages


def test_jpg_headings(jpg_text: str) -> None:
    for heading in JPG_HEADINGS:
        assert heading in jpg_text


def test_webp_main_page_only(webp_text: str) -> None:
    for heading in ["Глава 1", "ОБЩИЕ ПОЛОЖЕНИЯ", "Статья 1. Основные понятия, используемые в настоящем Кодексе"]:
        assert heading in webp_text
    assert "372-ФЗ" not in webp_text
    assert "448-ФЗ" not in webp_text


def test_blank_image_gives_empty_text(tmp_path: Path) -> None:
    blank = tmp_path / "blank.jpg"
    Image.new("RGB", (800, 1000), "white").save(blank)
    assert read_text(blank) == ""


@pytest.mark.parametrize("name", ["X.JPG", "Y.jpeg"])
def test_jpg_suffix_variants(tmp_path: Path, fake_ocr: None, name: str) -> None:
    path = tmp_path / name
    shutil.copy(JPG_SAMPLE, path)
    assert read_text(path) == "ok"


@pytest.mark.parametrize("name", ["a.png", "a.txt", "noext"])
def test_unsupported_format(tmp_path: Path, name: str) -> None:
    path = tmp_path / name
    path.write_bytes(b"data")
    with pytest.raises(UnsupportedFormatError) as error:
        read_text(path)
    assert str(path) in str(error.value)


def test_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "missing.pdf"
    with pytest.raises(FileNotFoundError) as error:
        read_text(path)
    assert error.value.filename == str(path)


@pytest.mark.parametrize("name", ["bad.jpg", "bad.pdf"])
def test_undecodable_file(tmp_path: Path, name: str) -> None:
    path = tmp_path / name
    path.write_bytes(b"not a document")
    with pytest.raises(UnreadableDocumentError) as error:
        read_text(path)
    assert str(path) in str(error.value)
    assert error.value.__cause__ is not None
