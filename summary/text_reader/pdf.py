from pathlib import Path

import pymupdf
from PIL import Image

from . import ocr, paragraph
from .errors import UnreadableDocumentError

_SCAN_DPI = 300
_TEXT_BLOCK = 0


def read_pdf(path: Path) -> str:
    """Read a PDF page by page: the text layer where present, OCR of the rendered page otherwise."""
    try:
        document = pymupdf.open(path, filetype="pdf")
    except pymupdf.FileDataError as exc:
        raise UnreadableDocumentError(path) from exc
    with document:
        if document.needs_pass:
            raise UnreadableDocumentError(path)
        page_texts = (_read_page(page) for page in document)
        return "\n".join(text for text in page_texts if text)


def _read_page(page: pymupdf.Page) -> str:
    blocks = [
        block[4]
        for block in page.get_text("blocks")
        if block[6] == _TEXT_BLOCK and block[4].strip()
    ]
    if blocks:
        return "\n".join(paragraph.join_lines(block.splitlines()) for block in blocks)
    pixmap = page.get_pixmap(dpi=_SCAN_DPI)
    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    return ocr.recognise_image(image)
