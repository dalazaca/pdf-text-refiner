# Configuración de Ollama desde WSL

## Problema Detectado

Tu IP del host Windows es: **10.255.255.254**

Ollama está instalado en Windows pero no es accesible desde WSL porque está configurado para escuchar solo en `localhost` (127.0.0.1) de Windows, no en todas las interfaces de red.

## Solución: Configurar Ollama para Escuchar en Todas las Interfaces

### Opción 1: Configurar Variable de Entorno en Windows (RECOMENDADO)

1. **Abrir PowerShell como Administrador** en Windows

2. **Configurar Ollama para escuchar en todas las interfaces:**
   ```powershell
   [System.Environment]::SetEnvironmentVariable('OLLAMA_HOST', '0.0.0.0:11434', 'User')
   ```

3. **Reiniciar el servicio de Ollama:**
   - Cierra Ollama completamente (busca el ícono en la bandeja del sistema y cierra)
   - Vuelve a abrir Ollama

4. **Permitir acceso en el Firewall:**
   ```powershell
   New-NetFirewallRule -DisplayName "Ollama WSL Access" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow
   ```

### Opción 2: Modo Mirrored Network (Windows 11 22H2+)

Si tienes Windows 11 versión 22H2 o superior, puedes habilitar el modo de red "mirrored":

1. Crea o edita el archivo `.wslconfig` en tu carpeta de usuario de Windows:
   ```
   C:\Users\TuUsuario\.wslconfig
   ```

2. Agrega estas líneas:
   ```ini
   [wsl2]
   networkingMode=mirrored
   ```

3. Reinicia WSL desde PowerShell:
   ```powershell
   wsl --shutdown
   ```

4. Vuelve a abrir WSL. Ahora podrás acceder a Ollama usando `localhost:11434`

---

## Verificar la Conexión desde WSL

Una vez configurado, prueba la conexión desde WSL:

```bash
# Probar con la IP del host Windows
curl http://10.255.255.254:11434/api/tags

# Si configuraste modo mirrored, usa localhost
curl http://localhost:11434/api/tags
```

Deberías ver una respuesta JSON con los modelos instalados.

---

## Modelos Recomendados para Corrección en Español

Una vez que Ollama esté accesible, descarga modelos optimizados para español:

```bash
# En Windows (PowerShell):
ollama pull llama3.2:3b        # Rápido y eficiente (3B parámetros)
ollama pull mistral:7b         # Mejor calidad (7B parámetros)
ollama pull gemma2:9b          # Excelente para español (9B parámetros)
```

**Recomendación**: Empieza con `llama3.2:3b` para pruebas rápidas.

---

## Script de Prueba Rápida

Guarda este script como `test_ollama.py` y ejecútalo desde WSL para verificar:

```python
#!/usr/bin/env python3
import requests

# Cambia según tu configuración:
OLLAMA_HOST = "http://10.255.255.254:11434"  # IP del host Windows
# O si usas modo mirrored:
# OLLAMA_HOST = "http://localhost:11434"

def test_connection():
    try:
        # Probar conexión
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)

        if response.status_code == 200:
            models = response.json().get('models', [])
            print("✅ Conexión exitosa a Ollama!")
            print(f"📦 Modelos disponibles: {len(models)}")
            for model in models:
                print(f"   - {model['name']}")
            return True
        else:
            print(f"❌ Error: Status code {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar a Ollama")
        print(f"   Verifica que Ollama esté corriendo en: {OLLAMA_HOST}")
        print("   Revisa la configuración en este documento.")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    test_connection()
```

Ejecuta:
```bash
python test_ollama.py
```

---

## Integración con el Código Actual

Una vez verificada la conexión, instala la librería oficial de Ollama:

```bash
uv add ollama
```

El código se modificará para:
1. Mantener LanguageTool para errores ortográficos básicos
2. Agregar Ollama para análisis profundo de redacción y coherencia
3. Combinar ambos resultados en el reporte final

---

## Troubleshooting

### "Connection refused" desde WSL
- Verifica que `OLLAMA_HOST` esté configurado a `0.0.0.0`
- Confirma que el firewall permite el puerto 11434
- Reinicia Ollama después de cambiar configuración

### "Model not found"
- Descarga el modelo primero: `ollama pull llama3.2:3b` en Windows

### Ollama muy lento
- Usa modelos más pequeños (3B en lugar de 7B)
- Verifica que tu GPU esté siendo utilizada en Task Manager

### Error de timeout
- Aumenta el timeout en el código Python
- Verifica que Ollama no esté procesando otra solicitud
