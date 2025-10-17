"""Módulo de extracción de texto desde PDFs."""

__all__ = ["PDFExtractor"]


def __getattr__(name):
    """Lazy import para evitar importaciones eagerly."""
    if name == "PDFExtractor":
        from src.pdf.extractor import PDFExtractor
        return PDFExtractor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
