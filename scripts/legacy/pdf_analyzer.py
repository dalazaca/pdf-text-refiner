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
    uv add pdfminer.six language-tool-python tqdm ollama

Uso:
    python pdf_analyzer.py --pdf documento.pdf
    python pdf_analyzer.py --pdf documento.pdf --start-page 10 --end-page 20
    python pdf_analyzer.py --pdf documento.pdf --model mistral:latest
"""

import argparse
import sys
from typing import List, Dict, Optional
from pathlib import Path
import os
from datetime import datetime

# Importar librerías necesarias con manejo de errores
try:
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer, LAParams
    from io import StringIO
    from pdfminer.converter import TextConverter
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.pdfpage import PDFPage
except ImportError:
    print("❌ Error: pdfminer.six no está instalado.")
    print("   Instala con: uv add pdfminer.six")
    sys.exit(1)

try:
    import language_tool_python
except ImportError:
    print("❌ Error: language-tool-python no está instalado.")
    print("   Instala con: uv add language-tool-python")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    print("❌ Error: tqdm no está instalado.")
    print("   Instala con: uv add tqdm")
    sys.exit(1)

try:
    import ollama
except ImportError:
    print("❌ Error: ollama no está instalado.")
    print("   Instala con: uv add ollama")
    sys.exit(1)


def get_windows_host_ip():
    """Obtiene la IP del host Windows desde WSL usando el gateway."""
    try:
        import subprocess
        # Obtener la IP del gateway (host Windows)
        result = subprocess.run(
            ['ip', 'route', 'show'],
            capture_output=True,
            text=True,
            check=True
        )
        for line in result.stdout.split('\n'):
            if 'default via' in line:
                # Formato: "default via 172.28.240.1 dev eth0 proto kernel"
                parts = line.split()
                if len(parts) >= 3:
                    return parts[2]
    except Exception:
        pass
    return None


# Configuración de Ollama
# Detectar automáticamente la IP del host Windows desde WSL
_detected_ip = get_windows_host_ip()
_default_host = f'http://{_detected_ip}:11434' if _detected_ip else 'http://localhost:11434'
OLLAMA_HOST = os.getenv('OLLAMA_HOST', _default_host)


def extract_page_text(pdf_path: str, page_number: int) -> str:
    """
    Extrae el texto limpio de una página específica del PDF.

    Args:
        pdf_path: Ruta al archivo PDF
        page_number: Número de página (0-indexed)

    Returns:
        Texto extraído de la página como string. Si hay error, retorna string vacío.

    Raises:
        Exception: Si el PDF no puede ser leído o la página no existe
    """
    resource_manager = PDFResourceManager()
    output_string = StringIO()
    laparams = LAParams()
    device = TextConverter(resource_manager, output_string, laparams=laparams)
    interpreter = PDFPageInterpreter(resource_manager, device)

    try:
        with open(pdf_path, 'rb') as pdf_file:
            # Iterar sobre las páginas hasta llegar a la deseada
            for current_page_num, page in enumerate(PDFPage.get_pages(pdf_file)):
                if current_page_num == page_number:
                    interpreter.process_page(page)
                    text = output_string.getvalue()
                    device.close()
                    output_string.close()
                    return text.strip()
                elif current_page_num > page_number:
                    break

            device.close()
            output_string.close()
            return ""

    except Exception as e:
        device.close()
        output_string.close()
        raise Exception(f"Error extrayendo texto de página {page_number + 1}: {str(e)}")


def get_pdf_page_count(pdf_path: str) -> int:
    """
    Obtiene el número total de páginas en el PDF.

    Args:
        pdf_path: Ruta al archivo PDF

    Returns:
        Número total de páginas

    Raises:
        Exception: Si el PDF no puede ser leído
    """
    try:
        with open(pdf_path, 'rb') as pdf_file:
            return len(list(PDFPage.get_pages(pdf_file)))
    except Exception as e:
        raise Exception(f"Error leyendo PDF: {str(e)}")


def create_debug_directory(pdf_path: str) -> str:
    """
    Crea un directorio de debug con el nombre del PDF y timestamp.

    Args:
        pdf_path: Ruta al archivo PDF

    Returns:
        Ruta del directorio de debug creado

    Raises:
        Exception: Si el directorio no puede ser creado
    """
    # Extraer nombre base del PDF (sin extensión)
    pdf_name = Path(pdf_path).stem

    # Generar timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Crear nombre del directorio
    debug_dir = f"debug_{pdf_name}_{timestamp}"

    # Crear directorio
    try:
        os.makedirs(debug_dir, exist_ok=True)
        return debug_dir
    except Exception as e:
        raise Exception(f"Error creando directorio de debug: {str(e)}")


def save_page_text_debug(text: str, page_num: int, debug_dir: str):
    """
    Guarda el texto extraído de una página en un archivo de debug.

    Args:
        text: Texto extraído de la página
        page_num: Número de página (0-indexed)
        debug_dir: Directorio donde guardar el archivo
    """
    # Nombre del archivo (página en formato 1-indexed)
    filename = f"pagina_{page_num + 1}.txt"
    filepath = os.path.join(debug_dir, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            # Escribir metadatos
            f.write(f"========== PÁGINA {page_num + 1} ==========\n")
            f.write(f"Longitud del texto: {len(text)} caracteres\n")
            f.write(f"{'=' * 50}\n\n")

            # Escribir el texto extraído
            f.write(text)
    except Exception as e:
        print(f"\n⚠️  Advertencia: No se pudo guardar debug de página {page_num + 1}: {str(e)}")


def verify_ollama_connection(host: str = OLLAMA_HOST, timeout: int = 5) -> bool:
    """
    Verifica que Ollama esté accesible y tenga modelos disponibles.

    Args:
        host: URL del servidor Ollama
        timeout: Timeout en segundos

    Returns:
        True si la conexión es exitosa, False en caso contrario
    """
    try:
        client = ollama.Client(host=host, timeout=timeout)
        models = client.list()

        if not models or len(models.get('models', [])) == 0:
            print(f"⚠️  Advertencia: Ollama conectado pero no hay modelos instalados")
            print("   Descarga un modelo: ollama pull llama3.2:3b")
            return False

        return True

    except Exception as e:
        print(f"❌ Error: No se pudo conectar a Ollama en {host}")
        print(f"   Detalle: {str(e)}")
        print("   Revisa CONFIGURACION_OLLAMA.md para solucionar este problema.")
        return False


def check_spelling_languagetool(text: str, page_number: int, tool: language_tool_python.LanguageTool) -> List[Dict]:
    """
    Verifica errores ortográficos y gramaticales usando LanguageTool.

    Args:
        text: Texto a verificar
        page_number: Número de página (para referencia en el resultado)
        tool: Instancia de LanguageTool configurada para español

    Returns:
        Lista de diccionarios con los errores encontrados
    """
    if not text.strip():
        return []

    errors = []

    try:
        matches = tool.check(text)

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


def check_with_ollama(
    text: str,
    page_number: int,
    model: str = "llama3.2:3b",
    host: str = OLLAMA_HOST,
    timeout: int = 120
) -> List[Dict]:
    """
    Analiza el texto usando un modelo de Ollama para encontrar errores de redacción.

    Args:
        text: Texto a analizar
        page_number: Número de página (para referencia)
        model: Modelo de Ollama a usar
        host: URL del servidor Ollama
        timeout: Timeout en segundos

    Returns:
        Lista de diccionarios con errores encontrados
    """
    if not text.strip():
        return []

    errors = []

    try:
        client = ollama.Client(host=host, timeout=timeout)

        prompt = f"""Eres un corrector profesional de textos en español. Analiza el siguiente texto y encuentra TODOS los errores de:
1. Redacción (construcción de frases, claridad)
2. Coherencia (ideas que no fluyen bien)
3. Concordancia (género, número, tiempo verbal)
4. Estilo (repeticiones innecesarias, redundancias)
5. Puntuación incorrecta o faltante

IMPORTANTE: Solo reporta errores REALES. No inventes errores que no existen.

Formato de respuesta (un error por línea):
LÍNEA [número aproximado] | TIPO: [tipo de error] | ERROR: "[texto erróneo]" | SUGERENCIA: "[corrección]" | RAZÓN: [breve explicación]

Si no hay errores, responde: "NO_ERRORS"

Texto a analizar:
{text[:2000]}
"""

        # Generar respuesta
        response = client.generate(
            model=model,
            prompt=prompt,
            stream=False
        )

        response_text = response['response'].strip()

        # Parsear respuesta
        if response_text == "NO_ERRORS" or "NO_ERRORS" in response_text.upper():
            return []

        lines = response_text.split('\n')
        for line in lines:
            if '|' in line and 'ERROR:' in line:
                try:
                    # Parsear formato: LÍNEA X | TIPO: Y | ERROR: "Z" | SUGERENCIA: "W" | RAZÓN: R
                    parts = line.split('|')

                    error_part = [p for p in parts if 'ERROR:' in p]
                    suggestion_part = [p for p in parts if 'SUGERENCIA:' in p]
                    type_part = [p for p in parts if 'TIPO:' in p]
                    reason_part = [p for p in parts if 'RAZÓN:' in p or 'RAZON:' in p]

                    if error_part:
                        error_text = error_part[0].split('ERROR:')[1].strip().strip('"')
                        suggestion = suggestion_part[0].split('SUGERENCIA:')[1].strip().strip('"') if suggestion_part else "revisar manualmente"
                        error_type = type_part[0].split('TIPO:')[1].strip() if type_part else "Redacción"
                        reason = reason_part[0].split('RAZÓN:' if 'RAZÓN:' in reason_part[0] else 'RAZON:')[1].strip() if reason_part else ""

                        error_info = {
                            'word': error_text,
                            'offset': -1,  # Ollama no provee offset exacto
                            'suggestions': [suggestion] if suggestion else [],
                            'context': f"...{error_text}...",
                            'error_type': f"LLM-{error_type}",
                            'reason': reason
                        }
                        errors.append(error_info)

                except Exception as parse_error:
                    # Si falla el parsing, continuar con el siguiente error
                    continue

    except Exception as e:
        print(f"\n⚠️  Advertencia: Error al verificar con Ollama página {page_number + 1}: {str(e)}")

    return errors


def format_output_hybrid(page_errors: Dict[int, Dict[str, List[Dict]]]) -> str:
    """
    Formatea los errores encontrados por ambos métodos.

    Args:
        page_errors: Diccionario con estructura:
            {
                page_num: {
                    'languagetool': [errores],
                    'ollama': [errores]
                }
            }

    Returns:
        String formateado con todos los errores
    """
    output = []

    for page_num in sorted(page_errors.keys()):
        page_data = page_errors[page_num]
        lt_errors = page_data.get('languagetool', [])
        ollama_errors = page_data.get('ollama', [])

        if lt_errors or ollama_errors:
            output.append(f"{'=' * 80}")
            output.append(f"Página {page_num + 1}")
            output.append(f"{'=' * 80}")

            if lt_errors:
                output.append(f"\n📝 Errores detectados por LanguageTool ({len(lt_errors)}):")
                for error in lt_errors:
                    suggestions = "|".join(error['suggestions']) if error['suggestions'] else "sin sugerencias"
                    error_type = error.get('error_type', 'Desconocido')
                    output.append(f"  ❌ \"{error['word']}\"")
                    output.append(f"     Tipo: {error_type}")
                    output.append(f"     Posición: {error['offset']}")
                    output.append(f"     Sugerencia: {suggestions}")
                    output.append("")

            if ollama_errors:
                output.append(f"\n🤖 Errores de redacción detectados por LLM ({len(ollama_errors)}):")
                for error in ollama_errors:
                    suggestions = " | ".join(error['suggestions']) if error['suggestions'] else "revisar manualmente"
                    error_type = error.get('error_type', 'Desconocido')
                    reason = error.get('reason', '')
                    output.append(f"  ❌ \"{error['word']}\"")
                    output.append(f"     Tipo: {error_type}")
                    output.append(f"     Sugerencia: {suggestions}")
                    if reason:
                        output.append(f"     Razón: {reason}")
                    output.append("")

            output.append("")  # Línea en blanco entre páginas

    return "\n".join(output)


def main():
    """
    Función principal del analizador híbrido de PDFs.
    """
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
        default='llama3.2:3b',
        help='Modelo de Ollama a usar (default: llama3.2:3b)'
    )
    parser.add_argument(
        '--ollama-host',
        type=str,
        default=OLLAMA_HOST,
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
    tool = None
    try:
        # Configurar directorio de caché persistente
        cache_dir = Path.home() / '.cache' / 'language_tool_python'
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Buscar versión ya descargada en caché
        lt_dir = None
        if cache_dir.exists():
            lt_versions = list(cache_dir.glob('LanguageTool-*'))
            if lt_versions:
                # Usar la versión más reciente en caché
                lt_dir = max(lt_versions, key=lambda p: p.stat().st_mtime)
                print(f"📦 Usando LanguageTool en caché: {lt_dir.name}")

                # Configurar para usar la versión local sin descargar
                os.environ['LANGUAGE_TOOL_PATH'] = str(lt_dir)

        tool = language_tool_python.LanguageTool('es')
        print("✅ LanguageTool iniciado")
    except Exception as e:
        print(f"❌ Error al inicializar LanguageTool: {str(e)}")
        sys.exit(1)

    # Verificar Ollama
    print(f"🔧 Verificando conexión a Ollama ({args.ollama_host})...")
    if not verify_ollama_connection(args.ollama_host):
        tool.close()
        sys.exit(1)
    print(f"✅ Ollama conectado - Modelo: {args.model}")

    print()

    # Obtener información del PDF
    try:
        total_pages = get_pdf_page_count(str(pdf_path))
        print(f"📖 Total de páginas: {total_pages}")
        print()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        tool.close()
        sys.exit(1)

    # Determinar rango
    start_page = args.start_page if args.start_page is not None else 1
    end_page = args.end_page if args.end_page is not None else total_pages

    # Validaciones
    if not (1 <= start_page <= end_page <= total_pages):
        print(f"❌ Error: Rango de páginas inválido")
        tool.close()
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
                text = extract_page_text(str(pdf_path), page_num)

                if debug_dir:
                    save_page_text_debug(text, page_num, debug_dir)

                if text.strip():
                    page_errors[page_num] = {}

                    # LanguageTool
                    lt_errors = check_spelling_languagetool(text, page_num, tool)
                    if lt_errors:
                        page_errors[page_num]['languagetool'] = lt_errors
                        total_lt_errors += len(lt_errors)

                    # Ollama
                    ollama_errors = check_with_ollama(
                        text,
                        page_num,
                        model=args.model,
                        host=args.ollama_host
                    )
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
        tool.close()
        sys.exit(1)
    finally:
        tool.close()

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
