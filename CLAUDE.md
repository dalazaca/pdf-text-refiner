# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF Text Refiner v0.2.0 - A hybrid PDF text analysis tool that combines LanguageTool (for spelling/grammar) and Ollama LLMs (for style/coherence) to provide comprehensive error detection in Spanish-language PDFs.

**Key Characteristic**: This project runs in a WSL environment where Ollama is hosted on the Windows machine, requiring special network configuration to bridge WSL ↔ Windows communication.

## Development Setup

```bash
# Install dependencies
uv sync

# Run the analyzer
uv run python pdf_analyzer.py --pdf documento.pdf

# Test with specific pages and debug mode
uv run python pdf_analyzer.py --pdf test.pdf --start-page 10 --end-page 20 --debug

# Test Ollama connection (critical for WSL environments)
uv run python test_ollama_connection.py
```

## Architecture

### Modular Structure (v0.2.0 Refactoring)

The codebase was refactored from a 622-line monolith (`scripts/legacy/pdf_analyzer.py`) into a modular architecture:

```
src/
├── config.py          # Pydantic Settings with env variable support
├── pdf/extractor.py   # PDFExtractor class (uses pdfminer.six)
├── checkers/
│   ├── languagetool.py   # LanguageToolChecker with persistent caching
│   └── ollama.py         # OllamaChecker with structured LLM prompting
├── formatters.py      # format_output_hybrid() - unified output format
└── utils.py           # network (WSL IP detection) + debug utilities
```

**Entry Point**: `pdf_analyzer.py` orchestrates the pipeline using these modules.

### Key Architectural Patterns

1. **Checker Interface**: Both checkers implement `check(text: str, page_number: int) -> List[Dict]` returning standardized error dictionaries
2. **No Dependency Injection**: Classes are instantiated directly in `pdf_analyzer.py` (simpler than originally planned DI container)
3. **Configuration Hierarchy**: `.env` → environment variables → hardcoded defaults (via pydantic-settings)
4. **Lazy Imports**: Import errors are caught and set to `None` to provide better error messages at instantiation time

### Configuration System

Uses `pydantic-settings` with `PDF_ANALYZER_` prefix for environment variables:

```python
# src/config.py
ollama_host: str = "http://localhost:11434"     # Auto-detected from WSL gateway
ollama_model: str = "mistral"                   # Default model
ollama_timeout: int = 120
languagetool_language: str = "es"
languagetool_cache_dir: Path                    # Persistent LanguageTool downloads
```

**Critical**: `get_windows_host_ip()` in `utils.py` auto-detects the Windows host IP from WSL by parsing `ip route show` to find the gateway.

### Checker Implementations

**LanguageToolChecker**:
- Manages lifecycle: `initialize()` → `check()` → `cleanup()`
- Uses persistent cache in `~/.cache/language_tool_python/`
- Downloads ~254MB on first run (requires internet)
- Returns errors with exact character offsets

**OllamaChecker**:
- No initialization required (stateless HTTP client)
- Sends structured prompt requesting Spanish text analysis
- Parses LLM response format: `LÍNEA X | TIPO: Y | ERROR: "Z" | SUGERENCIA: "W" | RAZÓN: R`
- Returns errors with `-1` offset (LLMs don't provide exact positions)
- Analyzes only first 2000 characters per page (performance vs. accuracy tradeoff)

### Output Format

`formatters.py` produces hybrid output with clear separation:
```
📝 Errores detectados por LanguageTool (X):
  ❌ "word" | Tipo: X | Posición: X | Sugerencia: X

🤖 Errores de redacción detectados por LLM (Y):
  ❌ "phrase" | Tipo: LLM-X | Sugerencia: X | Razón: X
```

**Important**: Output format must remain unchanged for backward compatibility with v0.1.0.

## Common Development Tasks

### Adding a New Checker

1. Create `src/checkers/nuevo_checker.py` with a class implementing:
   ```python
   def check(self, text: str, page_number: int) -> List[Dict]:
       return [{
           'word': str,           # Error text
           'offset': int,         # Character position (-1 if unknown)
           'suggestions': List[str],
           'context': str,
           'error_type': str,
           'reason': str          # Optional explanation
       }]
   ```

2. Import and instantiate in `pdf_analyzer.py` main():
   ```python
   nuevo_checker = NuevoChecker()
   nuevo_errors = nuevo_checker.check(text, page_num)
   if nuevo_errors:
       page_errors[page_num]['nuevo'] = nuevo_errors
   ```

3. Update `format_output_hybrid()` in `formatters.py` to handle the new checker type

### Debugging Ollama Issues

The most common issue is WSL ↔ Ollama connectivity:

1. Check Ollama is running on Windows (port 11434)
2. Run `uv run python test_ollama_connection.py` to diagnose
3. Verify `OLLAMA_HOST` environment variable on Windows:
   ```powershell
   [System.Environment]::SetEnvironmentVariable('OLLAMA_HOST', '0.0.0.0:11434', 'User')
   ```
4. Check firewall allows port 11434 inbound
5. Manually test: `curl http://<windows-ip>:11434/api/tags` from WSL

### Testing Changes

Currently no automated tests. Manual testing workflow:

```bash
# Quick test (2 pages with debug)
uv run python pdf_analyzer.py --pdf libros/Compresion-3.pdf --start-page 10 --end-page 11 --debug --out test_output.txt

# Verify output format unchanged
diff test_output.txt <expected-format-reference>

# Check debug files created
ls debug_Compresion-3_*/
```

**Future**: Tests structure exists (`tests/unit/`, `tests/integration/`) but not yet implemented.

## Critical Constraints

1. **Output Format Immutability**: The hybrid text output format must remain exactly the same as v0.1.0 (legacy) for user compatibility
2. **WSL Environment**: Always assume running in WSL with Ollama on Windows host - include WSL-specific utilities
3. **Spanish Language**: All checkers, prompts, and documentation are Spanish-focused
4. **Model Default**: `mistral` is the default Ollama model (not `llama3.2:3b`) - confirmed by user
5. **0-indexed Pages**: Internally pages are 0-indexed, but displayed as 1-indexed to users
6. **Text Truncation**: OllamaChecker only analyzes first 2000 characters per page (performance constraint)

## Environment-Specific Notes

- **LanguageTool First Run**: Requires internet to download ~254MB, shows progress bar that can take several minutes
- **PDFMiner.six**: Works with text-selectable PDFs only (not scanned/image PDFs)
- **Performance**: ~3-10 seconds per page depending on Ollama model size
- **Memory**: LanguageTool caches in memory after initialization - don't recreate instances unnecessarily

## Legacy Code

`scripts/legacy/pdf_analyzer.py` contains the original monolithic implementation. **Never modify it** - it's preserved for reference only. The refactored version in `pdf_analyzer.py` maintains identical behavior.