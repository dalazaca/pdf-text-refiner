"""Checker de texto usando Ollama LLM para análisis de redacción y estilo."""

from typing import List, Dict

try:
    import ollama
except ImportError:
    ollama = None  # type: ignore


class OllamaChecker:
    """Verificador de redacción y estilo usando Ollama LLM.

    Ejemplo:
        >>> checker = OllamaChecker(model="llama3:8b", host="http://localhost:11434")
        >>> errors = checker.check("Este es un texto.", page_number=0)
    """

    def __init__(self, model: str = "llama3:8b", host: str = "http://localhost:11434", timeout: int = 120):
        """Inicializa el checker de Ollama.

        Args:
            model: Modelo de Ollama a usar
            host: URL del servidor Ollama
            timeout: Timeout en segundos para las peticiones

        Raises:
            ImportError: Si ollama no está instalado
        """
        if ollama is None:
            raise ImportError(
                "ollama no está instalado. "
                "Instala con: uv add ollama"
            )

        self.model = model
        self.host = host
        self.timeout = timeout
        self.client = ollama.Client(host=host, timeout=timeout)

    def check(self, text: str, page_number: int) -> List[Dict]:
        """Analiza el texto usando un modelo de Ollama para encontrar errores de redacción.

        Args:
            text: Texto a analizar
            page_number: Número de página (para referencia)

        Returns:
            Lista de diccionarios con errores encontrados
        """
        if not text.strip():
            return []

        errors = []

        try:
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
            response = self.client.generate(
                model=self.model,
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
