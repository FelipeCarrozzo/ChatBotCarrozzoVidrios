from __future__ import annotations
import re
import pandas as pd
from typing import Any


_WS_RE = re.compile(r"\s+")


def safe_strip(x: Any) -> Any:
    """
    Si es string, quita espacios al inicio/fin y comprime espacios internos.
    Si no es string, lo devuelve tal cual (NO lo convierte a string).
    """
    if isinstance(x, str):
        x = x.strip()
        # normalizar múltiples espacios internos a uno solo
        x = _WS_RE.sub(" ", x)
    return x


def clean_text_columns(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """
    Aplica safe_strip SOLO a columnas 'object' o 'string' (texto).
    Si 'columns' es None, intenta detectar columnas de texto automáticamente.
    No convierte enteros/floats a string; respeta sus tipos.
    """
    df = df.copy()

    if columns is None:
        # Detectar columnas que contienen strings (dtype 'object' puede mezclar tipos)
        # Estrategia: si hay al menos un str en la columna, la tratamos como texto.
        columns = []
        for col in df.columns:
            ser = df[col]
            # rápido: si dtype es 'string' o 'object'
            if ser.dtype == "string":
                columns.append(col)
            elif ser.dtype == object:
                # ¿hay algún string?
                if ser.map(lambda v: isinstance(v, str)).any():
                    columns.append(col)

    for col in columns:
        df[col] = df[col].map(safe_strip)

    return df


def normalize_whitespace_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Atajo: aplica safe_strip a TODAS las columnas que contengan al menos un string.
    (útil cuando el DF viene heterogéneo de OCR/extractores).
    """
    return clean_text_columns(df)
