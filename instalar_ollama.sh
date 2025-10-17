#!/bin/bash

# Script de instalación y configuración de Ollama para la versión mejorada
# Ejecutar: bash instalar_ollama.sh

echo "=================================================="
echo "Instalación de dependencias para Ollama"
echo "=================================================="
echo ""

# Instalar dependencias Python
echo "📦 Instalando dependencias Python..."
uv add ollama

if [ $? -eq 0 ]; then
    echo "✅ Dependencias instaladas correctamente"
else
    echo "❌ Error al instalar dependencias"
    exit 1
fi

echo ""
echo "=================================================="
echo "Verificando conexión a Ollama"
echo "=================================================="
echo ""

# Probar conexión
python test_ollama_connection.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo "✅ Todo listo!"
    echo "=================================================="
    echo ""
    echo "Puedes empezar a usar la versión mejorada:"
    echo "  python pdf_spelling_check_ollama.py --pdf documento.pdf --mode hybrid"
    echo ""
else
    echo ""
    echo "=================================================="
    echo "⚠️  Configuración adicional requerida"
    echo "=================================================="
    echo ""
    echo "Ollama no está accesible desde WSL."
    echo ""
    echo "📖 Consulta CONFIGURACION_OLLAMA.md para solucionar."
    echo ""
    echo "Resumen rápido:"
    echo "1. En Windows PowerShell (como Administrador):"
    echo "   [System.Environment]::SetEnvironmentVariable('OLLAMA_HOST', '0.0.0.0:11434', 'User')"
    echo ""
    echo "2. Reinicia Ollama"
    echo ""
    echo "3. Permite firewall:"
    echo "   New-NetFirewallRule -DisplayName 'Ollama WSL' -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow"
    echo ""
    echo "4. Instala un modelo:"
    echo "   ollama pull llama3.2:3b"
    echo ""
    exit 1
fi
