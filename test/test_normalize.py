import pandas as pd
from src.normalize import normalize_column_names, ensure_columns

def test_normalize_column_names_basico():
    df = pd.DataFrame(columns=["Cód.", "Descripción", "P.Unit", "Marca"])
    mapping = {
        "codigo": ["cod", "codigo", "cód", "cód."],
        "descripcion": ["desc", "descripcion", "producto", "detalle"],
        "precio": ["precio", "p_u", "p.unit", "valor"],
        "marca": ["marca", "fabricante"],
    }

    out = normalize_column_names(df, mapping)
    assert set(out.columns) == {"codigo", "descripcion", "precio", "marca"}


def test_normalize_column_names_sin_mapping():
    df = pd.DataFrame(columns=["CÓDIGO", " Descripción Producto ", "Precio."])
    out = normalize_column_names(df)
    assert set(out.columns) == {"codigo", "descripcion_producto", "precio"}


def test_ensure_columns_agrega_faltantes():
    df = pd.DataFrame(columns=["codigo", "descripcion"])
    out = ensure_columns(df, ["codigo", "descripcion", "precio", "marca"])
    assert set(out.columns) == {"codigo", "descripcion", "precio", "marca"}
    assert out["precio"].isna().all()
