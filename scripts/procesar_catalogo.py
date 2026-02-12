#dependencias
from abc import ABC, abstractmethod
import pandas as pd
import json

class CatalogProcessor(ABC):
    """Clase base para procesar catálogos de distintos formatos."""

    def __init__(self, path):
        self.path = path
        self.data = None 

    @abstractmethod
    def extract(self):
        """Extrae los datos del archivo fuente (PDF, Excel, etc.) y devuelve un DataFrame."""
        pass

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpieza general aplicable a todos los catálogos."""
        df = df.copy()
        df.columns = df.columns.str.strip().str.lower()
        df = df.dropna(how="all")
        return df

    @abstractmethod
    def to_json(self, output_path: str):
        """Convierte el catálogo procesado en un JSON con estructura estandarizada."""
        pass

class ExcelCatalogProcessor(CatalogProcessor):
    """Clase procesadora del catálogo."""
    def __init__(self, path: str, sheet_name: str | int | None = 0, header_row: int = 1):
        """
        Inicializa el procesador de catálogos Excel.
        path: Ruta al archivo Excel.
        sheet_name: Nombre o índice de la hoja a leer (por defecto, la primera).
        header_row: Fila donde comienzan los nombres de columnas (0-indexada).
        """
        super().__init__(path)
        self.sheet_name = sheet_name
        self.header_row = header_row

    def extract(self):
        """Lee el archivo Excel y devuelve un DataFrame con los datos."""
        try:
            df = pd.read_excel(self.path, sheet_name=self.sheet_name,
                               header = self.header_row)
        except Exception as e:
            raise RuntimeError(f"Error leyendo Excel: {e}")

        self.data = df
        return df
    
    def infer_posicion_y_lado(self, row):
        """
        Determina valores normalizados de posición y lado a partir de la descripción
        del cristal cuando faltan en el registro original.
        """
        desc = str(row.get("cristal", "")).lower()

        def normalize_field(value):
            if value is None or pd.isna(value):
                return ""
            text = str(value).strip().lower()
            return "" if text in {"nan", "none", ""} else text

        pos = normalize_field(row.get("posicion", ""))
        lado = normalize_field(row.get("lado", ""))

        #inferir posición
        if not pos or pos == "nan":
            if "parabrisas" in desc:
                pos = "delantero"
            elif "luneta" in desc:
                pos = "trasero"
            else:
                pos = None

        #normalizar lado
        if not lado or lado == "nan":
            if "izq" in desc:
                lado = "izquierda"
            elif "der" in desc:
                lado = "derecha"
            else:
                lado = None

        return pd.Series({"posicion": pos, "lado": lado})
    
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica la limpieza base y normaliza el catálogo.
        - Convierte valores nulos de pandas a `None`.
        - Limpia textos (trim y colapsa espacios).
        - Completa posición y lado con inferencias de `infer_posicion_y_lado`.
        - Redondea/preformatea columnas de precios con formato `$X.XX`.
        """
        df = super().clean(df)
        df = df.replace({pd.NA: None})

        #eliminar espacios en blanco
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.replace(r"\s+", " ", regex=True)  #colapsa espacios múltiples en uno
            )

        #inferir posición y lado si faltan
        inferidos = df.apply(self.infer_posicion_y_lado, axis=1)
        df["posicion"] = inferidos["posicion"]
        df["lado"] = inferidos["lado"]

        #redondear precios y formatear con símbolo $
        price_cols = [c for c in df.columns if "precio" in c or "total" in c or "instalacion" in c]
        for col in price_cols:
            #intentar convertir a float si no lo está
            df[col] = pd.to_numeric(df[col], errors="coerce").round(2)
            #reemplazar NaN por None
            df[col] = df[col].where(df[col].notna(), None)
            #convertir a texto con formato $X.XX cuando hay valor numérico
            df[col] = df[col].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else None)

        return df

    def to_json(self, output_path: str):
        """Limpia y exporta el catálogo a JSON."""
        if self.data is None:
            raise ValueError("No hay datos cargados. Ejecute extract() primero.")

        df = self.clean(self.data)

        #si las columnas tienen nombres tipo "unnamed", se eliminan
        df = df.loc[:, ~df.columns.str.contains("^unnamed")]

        data = df.to_dict(orient="records")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Catálogo exportado a {output_path}")
