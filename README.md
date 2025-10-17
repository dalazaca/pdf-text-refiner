# PDF Text Refiner

Script en Python para análisis híbrido de errores en documentos PDF usando LanguageTool y Ollama LLMs.

> **Versión 0.2.0** - Refactorizado con arquitectura modular para mejor mantenibilidad y escalabilidad.

## Características

Combina dos métodos complementarios para análisis exhaustivo:

### LanguageTool (Análisis Rápido)
- Detección de errores ortográficos y gramaticales básicos
- Verificación de redundancias
- Análisis de concordancia
- Procesamiento rápido y eficiente

### Ollama LLM (Análisis Profundo)
- Análisis contextual de redacción
- Detección de errores de coherencia y estilo
- Sugerencias inteligentes basadas en contexto
- Identificación de problemas de construcción de frases
- 100% local y privado (no envía datos a internet)

## Instalación

### Requisitos previos

- Python 3.12 o superior
- UV (gestor de paquetes Python)
- Ollama instalado y ejecutándose

### Instalar dependencias

```bash
# Clonar o descargar el proyecto
cd pdf-text-refiner

# Instalar dependencias (uv crea automáticamente el entorno virtual)
uv sync

# Copiar archivo de configuración de ejemplo (opcional)
cp .env.example .env
```

### Variables de entorno (opcional)

Puedes personalizar la configuración creando un archivo `.env`:

```bash
# Configuración de Ollama
PDF_ANALYZER_OLLAMA_HOST=http://localhost:11434
PDF_ANALYZER_OLLAMA_MODEL=mistral
PDF_ANALYZER_OLLAMA_TIMEOUT=120

# Configuración de LanguageTool
PDF_ANALYZER_LANGUAGETOOL_LANGUAGE=es

# Debug
PDF_ANALYZER_DEBUG_ENABLED=false
```

## Tabla de dependencias

| Paquete | Versión mínima | Comentario |
|---------|----------------|------------|
| `pdfminer.six` | ≥ 20201018 | Extracción robusta de texto desde PDF |
| `language-tool-python` | ≥ 2.7.0 | Interfaz de LanguageTool para corrección ortográfica |
| `tqdm` | ≥ 4.0 | Barra de progreso en consola |
| `ollama` | ≥ 0.1.0 | Cliente oficial de Ollama para Python |

## Configuración de Ollama

**IMPORTANTE**: Ollama debe ser accesible desde WSL. Sigue estos pasos:

### Paso 1: Verificar la conexión

```bash
python test_ollama_connection.py
```

### Paso 2: Configurar Ollama en Windows (si falla)

1. Abre PowerShell como Administrador
2. Ejecuta:
   ```powershell
   [System.Environment]::SetEnvironmentVariable('OLLAMA_HOST', '0.0.0.0:11434', 'User')
   ```
3. Reinicia Ollama
4. Permite el firewall:
   ```powershell
   New-NetFirewallRule -DisplayName "Ollama WSL" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow
   ```

### Paso 3: Instalar un modelo

```powershell
ollama pull mistral
```

📖 **Guía completa**: Consulta `CONFIGURACION_OLLAMA.md` para más detalles.

## Estructura del Proyecto

```
pdf-text-refiner/
├── src/                          # Código fuente modular
│   ├── pdf/                      # Extracción de PDFs
│   │   └── extractor.py          # PDFExtractor class
│   ├── checkers/                 # Verificadores de texto
│   │   ├── languagetool.py       # LanguageToolChecker
│   │   └── ollama.py             # OllamaChecker
│   ├── formatters.py             # Formateadores de salida
│   ├── config.py                 # Configuración centralizada (pydantic)
│   └── utils.py                  # Utilidades (network, debug)
├── scripts/
│   └── legacy/
│       └── pdf_analyzer.py       # Versión monolítica original (legacy)
├── pdf_analyzer.py               # Script principal refactorizado
├── .env.example                  # Template de configuración
└── pyproject.toml                # Dependencias del proyecto
```

## Uso

### Sintaxis básica

**IMPORTANTE**: Ejecuta el script usando `uv run` para usar el entorno virtual correcto:

```bash
uv run python pdf_analyzer.py --pdf documento.pdf
```

### Parámetros

- `--pdf`: **(Obligatorio)** Ruta al archivo PDF a analizar
- `--out`: **(Opcional)** Ruta del archivo de salida (default: `errores_hibrido.txt`)
- `--start-page`: **(Opcional)** Página de inicio para el análisis (default: primera página)
- `--end-page`: **(Opcional)** Página final para el análisis (default: última página)
- `--debug`: **(Opcional)** Activa modo debug: guarda el texto extraído de cada página
- `--model`: **(Opcional)** Modelo de Ollama a usar (default: `mistral`)
- `--ollama-host`: **(Opcional)** URL del servidor Ollama (auto-detecta desde WSL)

### Ejemplos

```bash
# Análisis básico con configuración por defecto
uv run python pdf_analyzer.py --pdf documento.pdf

# Especificar archivo de salida personalizado
uv run python pdf_analyzer.py --pdf tesis.pdf --out resultados_tesis.txt

# Analizar solo un rango de páginas (ejemplo: páginas 10 a 20)
uv run python pdf_analyzer.py --pdf libro.pdf --start-page 10 --end-page 20

# Usar un modelo más potente
uv run python pdf_analyzer.py --pdf articulo.pdf --model mistral:latest

# Modo debug para inspeccionar el texto extraído
uv run python pdf_analyzer.py --pdf documento.pdf --debug

# Especificar host de Ollama personalizado
uv run python pdf_analyzer.py --pdf doc.pdf --ollama-host http://192.168.1.100:11434

# Análisis completo con todas las opciones
uv run python pdf_analyzer.py --pdf libro.pdf --out errores.txt --start-page 1 --end-page 50 --model mistral:7b --debug
```

## Formato de salida

El script genera un archivo de texto con el siguiente formato:

```
================================================================================
Página 3
================================================================================

📝 Errores detectados por LanguageTool (2):
  ❌ "cómmic"
     Tipo: Ortografía
     Posición: 127
     Sugerencia: comic|comi|cómic

  ❌ "estare"
     Tipo: Ortografía
     Posición: 245
     Sugerencia: estaré|estar

🤖 Errores de redacción detectados por LLM (1):
  ❌ "La investigación fue realizada por nosotros durante el año 2023 en el mes de enero"
     Tipo: LLM-Redundancia
     Sugerencia: La investigación fue realizada en enero de 2023
     Razón: Redundancia temporal innecesaria y voz pasiva puede mejorarse
```

**Ventaja del análisis híbrido**: El LLM detecta errores de redacción y estilo que LanguageTool no puede identificar, proporcionando un análisis más completo y profundo.

## Modelos Recomendados

| Modelo | Tamaño | Velocidad | Calidad | Uso Recomendado |
|--------|--------|-----------|---------|-----------------|
| `llama3.2:3b` | 3 GB | Muy rápido | Buena | Pruebas y análisis rápidos |
| `mistral:7b` | 7 GB | Rápido | Muy buena | Balance velocidad/calidad |
| `mistral:latest` | 7 GB | Rápido | Muy buena | Versión actualizada de Mistral |
| `gemma2:9b` | 9 GB | Moderado | Excelente | Análisis profundo |

## Por qué análisis híbrido

El enfoque híbrido combina lo mejor de ambos mundos:

### LanguageTool
- Rápido y eficiente
- Basado en reglas lingüísticas
- Alta precisión en errores ortográficos básicos
- No requiere GPU

### Ollama LLMs
- Comprensión contextual profunda
- Detección de problemas de estilo y coherencia
- Sugerencias inteligentes basadas en el contexto
- 100% privado y local
- Sin costos ni APIs de pago

### Juntos
Proporcionan un análisis **completo** que cubre desde errores ortográficos básicos hasta problemas complejos de redacción y estilo.

## Por qué language_tool_python

**`language-tool-python`** es la mejor opción para corrección ortográfica en español porque:

1. **IA y reglas lingüísticas**: Combina modelos basados en aprendizaje automático con reglas gramaticales y ortográficas específicas del español
2. **LanguageTool backend**: Es un frontend de [LanguageTool](https://languagetool.org/), una herramienta de código abierto ampliamente reconocida
3. **Detección contextual**: No solo identifica palabras mal escritas, sino también errores gramaticales y estilísticos
4. **Sugerencias inteligentes**: Proporciona múltiples sugerencias de corrección ordenadas por relevancia
5. **Mantenimiento activo**: Proyecto activamente mantenido con actualizaciones regulares
6. **Instalación simple**: No requiere configuración compleja, descarga automáticamente los recursos necesarios

## Manejo de errores

El script incluye validaciones para:

- PDF no existente o corrupto
- Falta de conexión a Internet (LanguageTool descarga recursos en primera ejecución)
- Ollama no accesible o sin modelos instalados
- Páginas ilegibles o con formato complejo
- Interrupciones del usuario (Ctrl+C)
- Errores de escritura en archivo de salida

## Limitaciones

- **Tamaño recomendado**: PDFs de hasta ~300 páginas. Documentos más grandes pueden procesarse pero tardarán más
- **Conexión a Internet**: La primera ejecución de LanguageTool requiere conexión para descargar recursos (~254MB). Una vez descargado, el caché persiste en `~/.cache/language_tool_python/` y no requiere conexión
- **PDFs escaneados**: El script solo funciona con PDFs que contengan texto seleccionable. Para PDFs escaneados (imágenes), se requiere OCR previo
- **Rendimiento**: El análisis híbrido puede tomar 3-10 segundos por página dependiendo del modelo LLM usado
- **Ollama requerido**: El script requiere que Ollama esté instalado y ejecutándose con al menos un modelo descargado

## Solución de problemas

### Error: "LanguageTool no puede inicializar"

**Causa**: Falta de conexión a Internet o recursos no descargados.

**Solución**: Verifica tu conexión y ejecuta nuevamente. Los recursos se descargan automáticamente la primera vez.

### LanguageTool sigue intentando descargar aunque ya está descargado

**Síntoma**: Aparece "Downloading LanguageTool latest: 2%" cada vez que ejecutas el script.

**Causa**: Versiones anteriores del código no configuraban correctamente la variable de entorno `LTP_JAR_DIR_PATH`.

**Solución Automática** (v0.2.0+): El script ahora detecta automáticamente la versión descargada y la usa. Deberías ver:
```
🔧 Inicializando LanguageTool...
📦 Usando LanguageTool en caché: LanguageTool-6.8-SNAPSHOT
✅ LanguageTool iniciado
```

**Si el problema persiste**:
```bash
# 1. Verifica que LanguageTool esté descargado
ls -la ~/.cache/language_tool_python/
# Deberías ver: LanguageTool-6.8-SNAPSHOT/ (~254MB)

# 2. Si la carpeta está vacía o corrupta, elimínala y vuelve a descargar
rm -rf ~/.cache/language_tool_python/
uv run python pdf_analyzer.py --pdf test.pdf --start-page 1 --end-page 1

# 3. Si actualizaste desde una versión anterior, asegúrate de tener el código más reciente
git pull  # o descarga la última versión
```

**Detalles técnicos**: El script usa la variable de entorno `LTP_JAR_DIR_PATH` que es la única que la librería `language_tool_python` respeta para evitar re-descargas (ver [src/checkers/languagetool.py:62](src/checkers/languagetool.py#L62)).

### Error: "No se pudo conectar a Ollama"

**Causa**: Ollama no está ejecutándose o no es accesible desde WSL.

**Solución**:
- Verifica que Ollama esté ejecutándose en Windows
- Ejecuta `python test_ollama_connection.py` para diagnosticar
- Consulta `CONFIGURACION_OLLAMA.md` para configuración completa

### Error: "PDF no puede ser leído"

**Causa**: PDF corrupto, protegido por contraseña, o es una imagen escaneada.

**Solución**:
- Verifica que el PDF no esté corrupto
- Remueve la contraseña si está protegido
- Para PDFs escaneados, usa herramientas OCR como Tesseract primero

### El script es muy lento

**Causa**: El análisis con LLM es naturalmente más lento que solo LanguageTool.

**Solución**:
- Usa modelos más pequeños como `mistral` para mayor velocidad
- Analiza solo rangos específicos de páginas con `--start-page` y `--end-page`
- Divide el PDF en secciones más pequeñas

## Migración desde versión anterior

Si estabas usando la versión anterior (monolítica), el script legacy está disponible en:

```bash
scripts/legacy/pdf_analyzer.py
```

La nueva versión refactorizada mantiene **exactamente el mismo comportamiento y formato de salida**, pero con código más mantenible y escalable.

### Cambios principales:

- **Arquitectura modular**: Código separado por responsabilidades
- **Configuración centralizada**: Usa pydantic-settings para variables de entorno
- **Mejor mantenibilidad**: Cada módulo tiene una responsabilidad clara
- **Preparado para testing**: Estructura lista para agregar tests unitarios e integración
- **Mismo CLI**: Los mismos argumentos y comportamiento

## Desarrollo

### Agregar nuevos checkers

Para agregar un nuevo verificador de texto:

1. Crea una nueva clase en `src/checkers/nuevo_checker.py`
2. Implementa el método `check(text: str, page_number: int) -> List[Dict]`
3. Importa y usa en `pdf_analyzer.py`

Ejemplo:

```python
# src/checkers/nuevo_checker.py
from typing import List, Dict

class NuevoChecker:
    def check(self, text: str, page_number: int) -> List[Dict]:
        # Tu lógica aquí
        return []
```

### Estructura de módulos

- **`src/pdf/extractor.py`**: Maneja toda la extracción de texto desde PDFs
- **`src/checkers/`**: Verificadores de texto (LanguageTool, Ollama, etc.)
- **`src/formatters.py`**: Formateo de resultados
- **`src/config.py`**: Configuración con pydantic-settings
- **`src/utils.py`**: Funciones auxiliares (network, debug)

## Contribuciones

Para reportar bugs o sugerir mejoras, consulta la documentación del proyecto.

## Licencia

Este script es de código abierto y puede ser usado libremente para fines educativos y comerciales.
