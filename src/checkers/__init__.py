"""Módulo de verificadores de texto (LanguageTool y Ollama)."""

# Importaciones lazy para evitar errores si faltan dependencias
__all__ = ["LanguageToolChecker", "OllamaChecker"]


def __getattr__(name):
    """Lazy import para evitar importaciones eagerly."""
    if name == "LanguageToolChecker":
        from src.checkers.languagetool import LanguageToolChecker
        return LanguageToolChecker
    elif name == "OllamaChecker":
        from src.checkers.ollama import OllamaChecker
        return OllamaChecker
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
