import errno
import os
from pathlib import Path

from PIL import Image, ImageOps

from . import ocr, pdf
from .errors import UnreadableDocumentError, UnsupportedFormatError

_IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".webp"})
_PDF_SUFFIX = ".pdf"


def read_text(path: str | os.PathLike[str]) -> str:
    """Return the text of one .jpg, .jpeg, .webp or .pdf document.

    Result: paragraphs separated by "\\n", PDF pages also separated by "\\n", no trailing newline.
    PDF pages with a text layer use it; image files and image-only PDF pages are recognised with OCR.
    In photos only the main page column is kept; a strip of the neighbouring page is dropped.
    Returns "" when the file contains no text.

    Side effects: reads the file. The first OCR use downloads the model weights (about 13 MB) once.

    Errors:
        UnsupportedFormatError: the extension (case-insensitive) is not .jpg, .jpeg, .webp or .pdf.
        FileNotFoundError: the path does not point to an existing file.
        UnreadableDocumentError: the file cannot be decoded as its format; the cause is chained.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix != _PDF_SUFFIX and suffix not in _IMAGE_SUFFIXES:
        raise UnsupportedFormatError(path)
    if not path.is_file():
        raise FileNotFoundError(errno.ENOENT, "document not found", str(path))
    if suffix == _PDF_SUFFIX:
        return pdf.read_pdf(path)
    return _read_image(path)


def _read_image(path: Path) -> str:
    try:
        with Image.open(path) as image:
            page = ImageOps.exif_transpose(image).convert("RGB")
    except OSError as exc:
        raise UnreadableDocumentError(path) from exc
    return ocr.recognise_image(page)
