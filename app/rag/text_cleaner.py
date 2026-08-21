import re


def clean_text(text: str) -> str:
    """
    Normalize PDF-extracted text while preserving readable structure.
    """

    if not text:
        return ""

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove spaces before punctuation
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)

    # Normalize bullet spacing
    text = re.sub(r"\s*●\s*", "\n● ", text)

    return text.strip()