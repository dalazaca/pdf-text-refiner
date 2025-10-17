#!/bin/bash
# Script para configurar LanguageTool sin descargas automáticas

# Directorio de caché
CACHE_DIR="$HOME/.cache/language_tool_python"
LT_DIR="$CACHE_DIR/LanguageTool-6.8-SNAPSHOT"

# Verificar si existe el caché
if [ -d "$LT_DIR" ]; then
    echo "✅ LanguageTool encontrado en: $LT_DIR"
    echo "📦 Configurando para usar versión local..."

    # Configurar variable de entorno
    export LANGUAGE_TOOL_PATH="$LT_DIR"
    echo "export LANGUAGE_TOOL_PATH=\"$LT_DIR\"" >> ~/.bashrc

    echo "✅ Configuración completada"
    echo "Reinicia tu terminal o ejecuta: source ~/.bashrc"
else
    echo "❌ LanguageTool no encontrado en el caché"
    echo "Ubicación esperada: $LT_DIR"
    echo "Ejecuta el script una vez para que se descargue"
fi
