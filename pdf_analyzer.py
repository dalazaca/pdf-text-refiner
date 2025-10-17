#!/usr/bin/env python3
"""
Script para análisis híbrido de errores en PDFs usando LanguageTool + Ollama LLM.

Combina dos métodos complementarios:
1. LanguageTool: Errores ortográficos y gramaticales básicos (rápido)
2. Ollama LLM: Análisis profundo de redacción, coherencia y estilo (preciso)

Dependencias:
    - pdfminer.six: Extracción de texto desde PDFs
    - language-tool-python: Corrección ortográfica y gramatical
    - tqdm: Barra de progreso
    - ollama: Cliente de Ollama para análisis con LLM

Instalación:
    uv add pdfminer.six language-tool-python tqdm ollama pydantic pydantic-settings

Uso:
    python pdf_analyzer.py --pdf documento.pdf
    python pdf_analyzer.py --pdf documento.pdf --start-page 10 --end-page 20
    python pdf_analyzer.py --pdf documento.pdf --model mistral:latest

Nota:
    Este script ha sido refactorizado. El código legacy está disponible en:
    scripts/legacy/pdf_analyzer.py
"""

import argparse
import sys
from pathlib import Path

# Importar módulos refactorizados
from src.pdf.extractor import PDFExtractor
from src.checkers.languagetool import LanguageToolChecker
from src.checkers.ollama import OllamaChecker
from src.formatters import format_output_hybrid
from src.config import settings
from src.utils import get_windows_host_ip, verify_ollama_connection, create_debug_directory, save_page_text_debug

try:
    from tqdm import tqdm
except ImportError:
    print("❌ Error: tqdm no está instalado.")
    print("   Instala con: uv add tqdm")
    sys.exit(1)


def main():
    """
    Función principal del analizador híbrido de PDFs.
    """
    # Detectar automáticamente la IP del host Windows desde WSL
    detected_ip = get_windows_host_ip()
    default_host = f'http://{detected_ip}:11434' if detected_ip else settings.ollama_host

    parser = argparse.ArgumentParser(
        description='Analiza errores en PDFs usando LanguageTool + Ollama (modo híbrido).',
        epilog='Ejemplos:\n'
               '  python pdf_analyzer.py --pdf documento.pdf\n'
               '  python pdf_analyzer.py --pdf documento.pdf --model mistral:latest\n'
               '  python pdf_analyzer.py --pdf documento.pdf --start-page 10 --end-page 20',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--pdf', type=str, required=True, help='Ruta al archivo PDF')
    parser.add_argument('--out', type=str, default='errores_hibrido.txt', help='Archivo de salida (default: errores_hibrido.txt)')
    parser.add_argument('--start-page', type=int, default=None, help='Página de inicio')
    parser.add_argument('--end-page', type=int, default=None, help='Página final')
    parser.add_argument('--debug', action='store_true', help='Modo debug: guarda texto extraído de cada página')
    parser.add_argument(
        '--model',
        type=str,
        default=settings.ollama_model,
        help=f'Modelo de Ollama a usar (default: {settings.ollama_model})'
    )
    parser.add_argument(
        '--ollama-host',
        type=str,
        default=default_host,
        help=f'Host de Ollama (default: auto-detectado)'
    )

    args = parser.parse_args()

    # Validar PDF
    pdf_path = Path(args.pdf)
    if not pdf_path.exists() or not pdf_path.is_file():
        print(f"❌ Error: El archivo '{args.pdf}' no existe o no es válido.")
        sys.exit(1)

    print(f"📄 Analizando: {args.pdf}")
    print(f"💾 Salida: {args.out}")
    print(f"🔧 Modo: Híbrido (LanguageTool + Ollama)")
    print()

    # Inicializar LanguageTool
    print("🔧 Inicializando LanguageTool...")
    lt_checker = LanguageToolChecker(
        language=settings.languagetool_language,
        cache_dir=settings.languagetool_cache_dir
    )

    try:
        lt_checker.initialize()
    except Exception as e:
        print(f"❌ Error al inicializar LanguageTool: {str(e)}")
        sys.exit(1)

    # Verificar Ollama
    print(f"🔧 Verificando conexión a Ollama ({args.ollama_host})...")
    if not verify_ollama_connection(args.ollama_host):
        lt_checker.cleanup()
        sys.exit(1)
    print(f"✅ Ollama conectado - Modelo: {args.model}")

    # Inicializar Ollama checker
    ollama_checker = OllamaChecker(
        model=args.model,
        host=args.ollama_host,
        timeout=settings.ollama_timeout
    )

    print()

    # Inicializar PDF extractor
    try:
        pdf_extractor = PDFExtractor(str(pdf_path))
        total_pages = pdf_extractor.get_page_count()
        print(f"📖 Total de páginas: {total_pages}")
        print()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        lt_checker.cleanup()
        sys.exit(1)

    # Determinar rango
    start_page = args.start_page if args.start_page is not None else 1
    end_page = args.end_page if args.end_page is not None else total_pages

    # Validaciones
    if not (1 <= start_page <= end_page <= total_pages):
        print(f"❌ Error: Rango de páginas inválido")
        lt_checker.cleanup()
        sys.exit(1)

    if start_page != 1 or end_page != total_pages:
        print(f"📑 Rango seleccionado: páginas {start_page} a {end_page} ({end_page - start_page + 1} páginas)")
        print()

    # Debug directory
    debug_dir = None
    if args.debug:
        try:
            debug_dir = create_debug_directory(str(pdf_path))
            print(f"🐛 Modo debug: {debug_dir}\n")
        except Exception as e:
            print(f"⚠️  Advertencia debug: {str(e)}\n")

    # Procesar páginas
    page_errors = {}
    total_lt_errors = 0
    total_ollama_errors = 0

    print("🔍 Analizando páginas...")
    try:
        for page_num in tqdm(range(start_page - 1, end_page), desc="Progreso", unit="pág"):
            try:
                text = pdf_extractor.extract_page_text(page_num)

                if debug_dir:
                    save_page_text_debug(text, page_num, debug_dir)

                if text.strip():
                    page_errors[page_num] = {}

                    # LanguageTool
                    lt_errors = lt_checker.check(text, page_num)
                    if lt_errors:
                        page_errors[page_num]['languagetool'] = lt_errors
                        total_lt_errors += len(lt_errors)

                    # Ollama
                    ollama_errors = ollama_checker.check(text, page_num)
                    if ollama_errors:
                        page_errors[page_num]['ollama'] = ollama_errors
                        total_ollama_errors += len(ollama_errors)

                    # Remover página si no tiene errores
                    if not page_errors[page_num]:
                        del page_errors[page_num]

            except Exception as e:
                print(f"\n⚠️  Error en página {page_num + 1}: {str(e)}")
                continue

    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido")
        lt_checker.cleanup()
        sys.exit(1)
    finally:
        lt_checker.cleanup()

    print()

    # Guardar resultados
    try:
        output_text = format_output_hybrid(page_errors)

        with open(args.out, 'w', encoding='utf-8') as f:
            if output_text:
                f.write(output_text)
            else:
                f.write("No se encontraron errores.\n")

        pages_with_errors = len(page_errors)
        print(f"✅ Análisis completado:")
        print(f"   📝 LanguageTool: {total_lt_errors} errores")
        print(f"   🤖 Ollama LLM: {total_ollama_errors} errores de redacción")
        print(f"   📄 Páginas con errores: {pages_with_errors}")
        print(f"📝 Resultado guardado en: {args.out}")

        if debug_dir:
            print(f"🐛 Debug: {debug_dir}/")

    except Exception as e:
        print(f"❌ Error al guardar: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()