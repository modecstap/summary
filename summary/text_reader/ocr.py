from functools import cache

from PIL import Image
from rapidocr import LangDet, LangRec, ModelType, OCRVersion, RapidOCR

from . import page_layout, paragraph
from .page_layout import TextLine


def recognise_image(image: Image.Image) -> str:
    """Recognise the main text column of a page image as paragraphs separated by newlines; "" if no text."""
    result = _engine()(image)
    if not result.txts:
        return ""
    lines = [
        TextLine(
            text=text,
            left=float(box[:, 0].min()),
            right=float(box[:, 0].max()),
            top=float(box[:, 1].min()),
        )
        for box, text in zip(result.boxes, result.txts)
        if text.strip()
    ]
    paragraphs = page_layout.split_paragraphs(page_layout.main_column(lines))
    return "\n".join(paragraph.join_lines([line.text for line in group]) for group in paragraphs)


@cache
def _engine() -> RapidOCR:
    return RapidOCR(
        params={
            # The direction classifier flips correct lines by 180° at this detection size; book photos are upright.
            "Global.use_cls": False,
            "Global.log_level": "error",
            "Det.ocr_version": OCRVersion.PPOCRV5,
            "Det.lang_type": LangDet.CH,
            "Det.model_type": ModelType.MOBILE,
            # The default 736 loses or garbles body lines on phone photos of book pages.
            "Det.limit_side_len": 1600,
            "Rec.ocr_version": OCRVersion.PPOCRV5,
            "Rec.lang_type": LangRec.ESLAV,
            # No eslav model exists for the default "small" type.
            "Rec.model_type": ModelType.MOBILE,
        }
    )
