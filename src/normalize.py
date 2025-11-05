import unicodedata
import pandas as pd
from typing import Dict

def normalize_column_name(name: str) -> str:
    """
    Normaliza un nombre de columna:
    - pasa a minúsculas
    - elimina tildes
    - quita caracteres especiales y espacios
    """
    # minusculas
    name = name.lower().strip()
    # eliminar tildes
    name = unicodedata.normalize("NFKD", name)
    name = "".join([c for c in name if not unicodedata.combining(c)])
    # reemplazar espacios, guiones, puntos
    name = name.replace(" ", "_").replace("-", "_").replace(".", "")
    return name


def normalize_column_names(df: pd.DataFrame, mapping: Dict[str, str] | None = None) -> pd.DataFrame:
    """
    Aplica normalización a los nombres de columnas del DataFrame.
    Si se pasa un mapping, renombra según ese diccionario.

    mapping = {
        "codigo": ["cod", "codigo", "cód", "cód."],
        "descripcion": ["desc", "descripcion", "producto", "detalle"],
        "precio": ["precio", "p_u", "p.unit", "valor"],
        "marca": ["marca", "fabricante"],
    }
    """
    df = df.copy()

    # 1️⃣ Normalizar todos los nombres crudos
    normalized = [normalize_column_name(c) for c in df.columns]
    df.columns = normalized

    if mapping:
        reverse_map = {}
        # crear reverse map: sinónimos -> nombre estándar
        for canonical, aliases in mapping.items():
            for alias in aliases:
                reverse_map[normalize_column_name(alias)] = canonical

        new_columns = [reverse_map.get(c, c) for c in df.columns]
        df.columns = new_columns

    return df


def ensure_columns(df: pd.DataFrame, required: list[str]) -> pd.DataFrame:
    """
    Asegura que existan las columnas requeridas; si no, las crea vacías.
    """
    df = df.copy()
    for col in required:
        if col not in df.columns:
            df[col] = None
    return df

    