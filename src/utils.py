"""Utilidades generales: network, debug, y helpers."""

import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    import ollama
except ImportError:
    ollama = None


def get_windows_host_ip() -> Optional[str]:
    """Obtiene la IP del host Windows desde WSL usando el gateway.

    Returns:
        IP del host Windows o None si no se puede determinar.
    """
    try:
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


def verify_ollama_connection(host: str, timeout: int = 5) -> bool:
    """Verifica que Ollama esté accesible y tenga modelos disponibles.

    Args:
        host: URL del servidor Ollama
        timeout: Timeout en segundos

    Returns:
        True si la conexión es exitosa, False en caso contrario
    """
    if ollama is None:
        print("❌ Error: ollama no está instalado.")
        return False

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


def create_debug_directory(pdf_path: str) -> str:
    """Crea un directorio de debug con el nombre del PDF y timestamp.

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


def save_page_text_debug(text: str, page_num: int, debug_dir: str) -> None:
    """Guarda el texto extraído de una página en un archivo de debug.

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
