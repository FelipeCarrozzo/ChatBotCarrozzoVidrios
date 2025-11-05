import re
import math
import pandas as pd
from typing import Any


def parse_price(value: Any) -> float | None:
    """
    Convierte un valor de texto a float.
    Maneja formatos tipo '321,694.32', '$48,293.94', '–', 'CONSULTAR', '0'.
    Devuelve None si no se puede interpretar como precio válido.
    """
    if value is None:
        return None

    # Si ya es numérico
    if isinstance(value, (int, float)):
        if value == 0 or math.isnan(value):
            return None
        return float(value)

    # Convertir a string y limpiar
    s = str(value).strip().upper()

    # Casos que no son precios
    if s in ("", "-", "–", "CONSULTAR", "N/A", "NONE", "SIN DATO", "S/D"):
        return None

    # Quitar símbolos comunes
    s = re.sub(r"[^0-9,.-]", "", s)

    if not s or s in ("0", "0.0", "0,0"):
        return None

    # Si hay más comas que puntos, probablemente usa coma decimal
    # Si hay más comas que puntos, o si hay ambos y la coma va después del punto,
    # probablemente es formato latino (punto de miles, coma decimal)
    if s.count(",") > s.count(".") or ("," in s and "." in s and s.find(",") > s.find(".")):
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", "")


    try:
        val = float(s)
        return val if val != 0 else None
    except ValueError:
        return None


def clean_price_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    Aplica parse_price a una columna del DataFrame.
    Devuelve una nueva columna limpia con tipo float.
    """
    df = df.copy()
    df[column] = df[column].map(parse_price)
    return df
