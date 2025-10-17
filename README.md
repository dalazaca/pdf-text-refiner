# PDF Analyzer

Script en Python para análisis híbrido de errores en documentos PDF usando LanguageTool y Ollama LLMs.

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

- Python 3.7 o superior
- UV (gestor de paquetes Python)
- Ollama instalado y ejecutándose

### Instalar dependencias

```bash
uv add pdfminer.six language-tool-python tqdm ollama
```

Opcionalmente, puedes crear un entorno virtual aislado:

```bash
uv venv .venv
source .venv/bin/activate  # En Linux/macOS
# .venv\Scripts\activate   # En Windows
uv add pdfminer.six language-tool-python tqdm ollama
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
ollama pull llama3.2:3b
```

📖 **Guía completa**: Consulta `CONFIGURACION_OLLAMA.md` para más detalles.

## Uso

### Sintaxis básica

```bash
python pdf_analyzer.py --pdf documento.pdf
```

### Parámetros

- `--pdf`: **(Obligatorio)** Ruta al archivo PDF a analizar
- `--out`: **(Opcional)** Ruta del archivo de salida (default: `errores_hibrido.txt`)
- `--start-page`: **(Opcional)** Página de inicio para el análisis (default: primera página)
- `--end-page`: **(Opcional)** Página final para el análisis (default: última página)
- `--debug`: **(Opcional)** Activa modo debug: guarda el texto extraído de cada página
- `--model`: **(Opcional)** Modelo de Ollama a usar (default: `llama3.2:3b`)
- `--ollama-host`: **(Opcional)** URL del servidor Ollama (auto-detecta desde WSL)

### Ejemplos

```bash
# Análisis básico con configuración por defecto
python pdf_analyzer.py --pdf documento.pdf

# Especificar archivo de salida personalizado
python pdf_analyzer.py --pdf tesis.pdf --out resultados_tesis.txt

# Analizar solo un rango de páginas (ejemplo: páginas 10 a 20)
python pdf_analyzer.py --pdf libro.pdf --start-page 10 --end-page 20

# Usar un modelo más potente
python pdf_analyzer.py --pdf articulo.pdf --model mistral:latest

# Modo debug para inspeccionar el texto extraído
python pdf_analyzer.py --pdf documento.pdf --debug

# Especificar host de Ollama personalizado
python pdf_analyzer.py --pdf doc.pdf --ollama-host http://192.168.1.100:11434

# Análisis completo con todas las opciones
python pdf_analyzer.py --pdf libro.pdf --out errores.txt --start-page 1 --end-page 50 --model mistral:7b --debug
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
- **Conexión a Internet**: La primera ejecución de LanguageTool requiere conexión para descargar recursos
- **PDFs escaneados**: El script solo funciona con PDFs que contengan texto seleccionable. Para PDFs escaneados (imágenes), se requiere OCR previo
- **Rendimiento**: El análisis híbrido puede tomar 3-10 segundos por página dependiendo del modelo LLM usado
- **Ollama requerido**: El script requiere que Ollama esté instalado y ejecutándose con al menos un modelo descargado

## Solución de problemas

### Error: "LanguageTool no puede inicializar"

**Causa**: Falta de conexión a Internet o recursos no descargados.

**Solución**: Verifica tu conexión y ejecuta nuevamente. Los recursos se descargan automáticamente la primera vez.

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
- Usa modelos más pequeños como `llama3.2:3b` para mayor velocidad
- Analiza solo rangos específicos de páginas con `--start-page` y `--end-page`
- Divide el PDF en secciones más pequeñas

## Contribuciones

Para reportar bugs o sugerir mejoras, consulta la documentación del proyecto.

## Licencia

Este script es de código abierto y puede ser usado libremente para fines educativos y comerciales.
