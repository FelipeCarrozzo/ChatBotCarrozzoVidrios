import json
import re
import fitz

class ColumnMapper:
    """
    Mapea la coordenada horizontal de cada palabra extraída del PDF con el nombre
    de la columna a la que pertenece, usando los rangos definidos en `col_config`.
    Permite identificar rápidamente si un valor cae dentro de los límites de una
    columna y devolver su etiqueta correspondiente.
    """
    def __init__(self, col_config):
        self.col_config = col_config

    def get_column(self, x_coord):
        """ Retorna el nombre de la columa para una coordinada dada, o None si no coincide."""
        for col_name, (xmin, xmax) in self.col_config.items():
            if xmin <= x_coord <= xmax:
                return col_name
        return None

class PDFExtractor:
    def __init__(self, pdf_path, marcas_path, column_mapper, y_tolerance=8, header_y_limit=50):
        """
        pdf_path: ruta al PDF
        marcas_path: ruta al archivo JSON con marcas
        column_mapper: instancia de ColumnMapper
        """
        self.pdf_path = pdf_path
        self.marcas_list = self._load_marcas(marcas_path)
        self.column_mapper = column_mapper
        self.data = []
        self.marca_actual = None
        self.modelo_actual = None
        self.y_tolerance = y_tolerance
        self.header_y_limit = header_y_limit
        self.codigo_pattern = re.compile(r'^\d{5}$')

    def _should_ignore(self, text, y0):
        """
        Decide si una palabra debe descartarse antes de procesarla cuando:
        - la cood Y0 sobrepasa el limite de encabezado.
        - el texto es una fracción.
        - el texto es típico de encabezados
        Return True
        """
        if y0 < self.header_y_limit:
            return True
        if "/" in text and text.replace("/", "").isdigit():
            return True
        if text.lower().startswith(("página", "pagina", "catálogo", "catalogo")):
            return True
        return False

    def _load_marcas(self, marcas_path):
        """Carga la lista de marcas desde el archivo JSON"""
        with open(marcas_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            marcas = data["marcas"]
        return set(m["nombre"].upper().strip() for m in marcas if "nombre" in m)

    def is_marca(self, text):
        """Chequea que la marca de vehículo encontrada sea válida"""
        return text.strip().upper() in self.marcas_list

    def extract(self):
        """Recorrer el archivo y procesar palabra por palabra"""
        doc = fitz.open(self.pdf_path)
        for page_number, page in enumerate(doc, start=1):
            words = page.get_text("dict", sort=True)
            self._process_words(words, page_number)
        doc.close()

    def _process_words(self, page_dict, page_number):
        """Procesa spans de texto y delega detección a funciones específicas"""
        for block in page_dict["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span["text"].strip()
                    y0 = line["bbox"][1] if "bbox" in line else 0

                    if self._should_ignore(text, y0):
                        continue

                    # --- MARCA ---
                    if self._is_marca_span(span):
                        self.marca_actual = text.upper()
                        self.modelo_actual = None
                        self.data.append({
                            "marca": self.marca_actual,
                            "modelo": None,
                            "descripcion": None,
                            "incoloro": None,
                            "color": None,
                            "degrade": None,
                        })
                        continue
            # (futuro: detección de modelo, productos, etc.)

    def _is_marca_span(self, span):
        """
        Devuelve True si el span corresponde a una marca válida:
        - texto presente en self.marcas_list
        - texto en cursiva (font_flags & 2)
        - posición vertical (y0) dentro del rango permitido
        """
        text = span.get("text", "").strip()
        flags = span.get("flags", 0)
        bbox = span.get("bbox", None)

        if not bbox or not text:
            return False

        # Extraer coordenadas del rectángulo
        x0, y0, x1, y1 = bbox

        # --- REGLAS ---
        if not (flags & 2):  # debe estar en cursiva
            return False
        if not self.is_marca(text):  # debe estar en lista
            print(f"[DEBUG NO MATCH] texto={text!r} no está en lista")
            return False
        print(f"[DEBUG POS] {text:<15} x0={x0:.1f}, flags={flags}")
        return True

    def _is_modelo_span(span):
        pass

    def _is_producto_span(span):
        pass

    def to_json(self, out_path):
        """
        Exporta el contenido ya procesado a un archivo .json. 
        Recibe la ruta de salida, lo abre en modo escritura y vuelca
        la lista de registros.
        """
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)