from pathlib import Path


class UnsupportedFormatError(ValueError):
    """The file extension is not one of .jpg, .jpeg, .webp, .pdf."""

    def __init__(self, path: Path) -> None:
        super().__init__(f"unsupported format: {path} (supported: .jpg, .jpeg, .webp, .pdf)")
        self.path = path


class UnreadableDocumentError(Exception):
    """The file cannot be decoded as its format; the cause is chained."""

    def __init__(self, path: Path) -> None:
        super().__init__(f"cannot read document: {path}")
        self.path = path
