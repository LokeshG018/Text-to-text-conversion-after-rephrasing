"""Stage 1 of the pipeline: text preprocessing."""
import re
import unicodedata

_SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


def clean_text(text: str) -> str:
    """Unicode-normalise, strip control chars, collapse whitespace, fix spacing before punctuation."""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\u0000-\u0008\u000b\u000c\u000e-\u001f]", " ", text)
    text = text.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    parts = []
    for para in text.split("\n"):
        para = para.strip()
        if para:
            parts.extend(s.strip() for s in _SENT_RE.split(para) if s.strip())
    return parts


def chunk_sentences(text: str, max_words: int = 80) -> list[str]:
    """Group sentences into chunks so long inputs fit the model's context window."""
    chunks, cur, count = [], [], 0
    for s in split_sentences(text):
        n = len(s.split())
        if cur and count + n > max_words:
            chunks.append(" ".join(cur))
            cur, count = [], 0
        cur.append(s)
        count += n
    if cur:
        chunks.append(" ".join(cur))
    return chunks or [text]
