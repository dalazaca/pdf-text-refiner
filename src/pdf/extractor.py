"""Extractor de texto desde archivos PDF usando PDFMiner."""

from io import StringIO
from typing import Optional

try:
    from pdfminer.converter import TextConverter
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.pdfpage import PDFPage
    from pdfminer.layout import LAParams
except ImportError:
    TextConverter = None  # type: ignore
    PDFResourceManager = None  # type: ignore
    PDFPageInterpreter = None  # type: ignore
    PDFPage = None  # type: ignore
    LAParams = None  # type: ignore


class PDFExtractor:
    """Extractor de texto desde archivos PDF.

    Ejemplo:
        >>> extractor = PDFExtractor("documento.pdf")
        >>> total_pages = extractor.get_page_count()
        >>> text = extractor.extract_page_text(0)
    """

    def __init__(self, pdf_path: str):
        """Inicializa el extractor.

        Args:
            pdf_path: Ruta al archivo PDF

        Raises:
            FileNotFoundError: Si el PDF no existe
            ImportError: Si pdfminer.six no está instalado
        """
        if PDFPage is None:
            raise ImportError(
                "pdfminer.six no está instalado. "
                "Instala con: uv add pdfminer.six"
            )

        self.pdf_path = pdf_path
        self._validate_pdf()

    def _validate_pdf(self) -> None:
        """Valida que el archivo PDF exista.

        Raises:
            FileNotFoundError: Si el PDF no existe
        """
        try:
            with open(self.pdf_path, 'rb') as f:
                pass
        except FileNotFoundError:
            raise FileNotFoundError(f"PDF no encontrado: {self.pdf_path}")

    def get_page_count(self) -> int:
        """Obtiene el número total de páginas en el PDF.

        Returns:
            Número total de páginas

        Raises:
            Exception: Si el PDF no puede ser leído
        """
        try:
            with open(self.pdf_path, 'rb') as pdf_file:
                return len(list(PDFPage.get_pages(pdf_file)))
        except Exception as e:
            raise Exception(f"Error leyendo PDF: {str(e)}")

    def extract_page_text(self, page_number: int) -> str:
        """Extrae el texto limpio de una página específica del PDF.

        Args:
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
            with open(self.pdf_path, 'rb') as pdf_file:
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
