"""Configuración centralizada de la aplicación usando Pydantic Settings."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación.

    Las variables pueden ser configuradas mediante:
    1. Archivo .env
    2. Variables de entorno
    3. Valores por defecto
    """

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        env_prefix='PDF_ANALYZER_'
    )

    # Configuración de Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "mistral"
    ollama_timeout: int = 120

    # Configuración de LanguageTool
    languagetool_language: str = "es"
    languagetool_cache_dir: Path = Path.home() / ".cache" / "language_tool_python"

    # Configuración de debug
    debug_enabled: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        """Crea una instancia de Settings desde variables de entorno."""
        return cls()


# Instancia global de configuración
settings = Settings()
