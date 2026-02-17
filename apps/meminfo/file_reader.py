"""File reader module for markdown and PDF extraction."""
from pathlib import Path

import pdfplumber


def read_file(path: str) -> str:
    """Read content from markdown or PDF file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = p.suffix.lower()
    if ext == ".pdf":
        return _read_pdf(p)
    elif ext in (".md", ".markdown", ".txt"):
        return p.read_text(encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _read_pdf(path: Path) -> str:
    """Extract text from PDF using pdfplumber."""
    with pdfplumber.open(path) as pdf:
        return "\n\n".join(page.extract_text() or "" for page in pdf.pages)
