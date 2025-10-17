"""Checker de texto usando LanguageTool para ortografía y gramática."""

import os
from pathlib import Path
from typing import List, Dict, Optional

try:
    import language_tool_python
except ImportError:
    language_tool_python = None  # type: ignore


class LanguageToolChecker:
    """Verificador de ortografía y gramática usando LanguageTool.

    Ejemplo:
        >>> checker = LanguageToolChecker(language="es")
        >>> checker.initialize()
        >>> errors = checker.check("Este es un texo con eror.", page_number=0)
        >>> checker.cleanup()
    """

    def __init__(self, language: str = "es", cache_dir: Optional[Path] = None):
        """Inicializa el checker.

        Args:
            language: Código de idioma (default: "es")
            cache_dir: Directorio de caché para LanguageTool

        Raises:
            ImportError: Si language_tool_python no está instalado
        """
        if language_tool_python is None:
            raise ImportError(
                "language-tool-python no está instalado. "
                "Instala con: uv add language-tool-python"
            )

        self.language = language
        self.cache_dir = cache_dir or Path.home() / '.cache' / 'language_tool_python'
        self.tool: Optional[language_tool_python.LanguageTool] = None

    def initialize(self) -> None:
        """Inicializa LanguageTool.

        Configura el caché persistente y carga la herramienta.
        """
        # Configurar directorio de caché persistente
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Buscar versión ya descargada en caché
        lt_dir = None
        if self.cache_dir.exists():
            lt_versions = list(self.cache_dir.glob('LanguageTool-*'))
            if lt_versions:
                # Usar la versión más reciente en caché
                lt_dir = max(lt_versions, key=lambda p: p.stat().st_mtime)
                print(f"📦 Usando LanguageTool en caché: {lt_dir.name}")

                # Configurar variable de entorno LTP_JAR_DIR_PATH para evitar descarga
                # Esta variable hace que download_lt() retorne inmediatamente sin descargar
                os.environ['LTP_JAR_DIR_PATH'] = str(lt_dir)

        self.tool = language_tool_python.LanguageTool(self.language)
        print("✅ LanguageTool iniciado")

    def check(self, text: str, page_number: int) -> List[Dict]:
        """Verifica errores ortográficos y gramaticales usando LanguageTool.

        Args:
            text: Texto a verificar
            page_number: Número de página (para referencia en el resultado)

        Returns:
            Lista de diccionarios con los errores encontrados

        Raises:
            RuntimeError: Si el checker no ha sido inicializado
        """
        if self.tool is None:
            raise RuntimeError("LanguageToolChecker no ha sido inicializado. Llama a initialize() primero.")

        if not text.strip():
            return []

        errors = []

        try:
            matches = self.tool.check(text)

            for match in matches:
                error_info = {
                    'word': match.context[match.offsetInContext:match.offsetInContext + match.errorLength],
                    'offset': match.offset,
                    'suggestions': [r for r in match.replacements[:5]],  # Máximo 5 sugerencias
                    'context': match.context,
                    'error_type': match.category
                }
                errors.append(error_info)

        except Exception as e:
            print(f"\n⚠️  Advertencia: Error al verificar con LanguageTool página {page_number + 1}: {str(e)}")

        return errors

    def cleanup(self) -> None:
        """Limpia recursos y cierra LanguageTool."""
        if self.tool is not None:
            self.tool.close()
            self.tool = None
