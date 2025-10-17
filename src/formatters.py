"""Formateadores de salida para los resultados del análisis."""

from typing import Dict, List


def format_output_hybrid(page_errors: Dict[int, Dict[str, List[Dict]]]) -> str:
    """Formatea los errores encontrados por ambos métodos (LanguageTool + Ollama).

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

    Ejemplo:
        >>> page_errors = {
        ...     0: {
        ...         'languagetool': [{'word': 'eror', 'suggestions': ['error'], ...}],
        ...         'ollama': []
        ...     }
        ... }
        >>> output = format_output_hybrid(page_errors)
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
