#!/usr/bin/env python3
"""
Script para verificar la conexión a Ollama desde WSL.

Uso:
    python test_ollama_connection.py
    python test_ollama_connection.py --host http://localhost:11434
"""

import argparse
import sys
import os

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


def test_connection(host: str, timeout: int = 5):
    """
    Prueba la conexión a Ollama.

    Args:
        host: URL del servidor Ollama
        timeout: Timeout en segundos
    """
    print(f"🔍 Probando conexión a: {host}")
    print()

    try:
        client = ollama.Client(host=host, timeout=timeout)

        # Listar modelos
        print("📦 Obteniendo lista de modelos...")
        response = client.list()
        models = response.get('models', [])

        if not models:
            print("⚠️  Ollama está conectado pero no hay modelos instalados")
            print()
            print("Para instalar un modelo, ejecuta en Windows (PowerShell):")
            print("  ollama pull llama3.2:3b")
            return False

        print(f"✅ Conexión exitosa!")
        print(f"📦 Modelos disponibles: {len(models)}")
        print()

        # Encontrar primer modelo válido (no cloud)
        first_model = None
        for model in models:
            name = model.get('name', model.get('model', 'Desconocido'))
            size = model.get('size', 0) / (1024**3)  # Convertir a GB
            is_cloud = 'cloud' in name
            model_type = " (cloud)" if is_cloud else ""
            print(f"  • {name} ({size:.2f} GB){model_type}")

            # Guardar primer modelo local para prueba
            if not is_cloud and first_model is None and size > 0:
                first_model = name

        print()

        if not first_model:
            print("⚠️  No hay modelos locales disponibles para prueba")
            print("   Todos los modelos son remotos (cloud)")
            return True

        print(f"🎯 Probando generación de texto con {first_model}...")

        # Probar generación
        test_response = client.generate(
            model=first_model,
            prompt="Di 'Hola' en una palabra.",
            stream=False
        )

        generated_text = test_response.get('response', '').strip()
        print(f"✅ Respuesta del modelo: {generated_text}")
        print()
        print("🎉 Todo funciona correctamente!")

        return True

    except Exception as e:
        print(f"❌ Error al conectar con Ollama")
        print(f"   Detalle: {str(e)}")
        print()
        print("💡 Posibles soluciones:")
        print()
        print("1. Verifica que Ollama esté corriendo en Windows")
        print("   - Busca el ícono de Ollama en la bandeja del sistema")
        print()
        print("2. Configura Ollama para escuchar en todas las interfaces:")
        print("   En PowerShell como Administrador:")
        print("   [System.Environment]::SetEnvironmentVariable('OLLAMA_HOST', '0.0.0.0:11434', 'User')")
        print()
        print("3. Permite el acceso en el Firewall de Windows:")
        print("   New-NetFirewallRule -DisplayName 'Ollama WSL' -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow")
        print()
        print("4. Reinicia Ollama después de hacer cambios")
        print()
        print("📖 Consulta CONFIGURACION_OLLAMA.md para más detalles")

        return False


def main():
    parser = argparse.ArgumentParser(
        description='Verifica la conexión a Ollama desde WSL'
    )
    parser.add_argument(
        '--host',
        type=str,
        default=None,
        help='Host de Ollama (default: detecta automáticamente)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        help='Timeout en segundos (default: 10)'
    )

    args = parser.parse_args()

    # Determinar host
    if args.host:
        host = args.host
        print(f"🔧 Usando host especificado: {host}")
    else:
        # Intentar detectar automáticamente
        windows_ip = get_windows_host_ip()
        if windows_ip:
            host = f"http://{windows_ip}:11434"
            print(f"🔧 Host Windows detectado: {windows_ip}")
        else:
            # Fallback a localhost (por si está en modo mirrored)
            host = "http://localhost:11434"
            print(f"🔧 Usando localhost (modo mirrored o nativo)")

    print()

    # Probar conexión
    success = test_connection(host, timeout=args.timeout)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
