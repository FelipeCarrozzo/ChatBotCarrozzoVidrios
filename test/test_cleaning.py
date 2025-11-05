import pandas as pd
from src.cleaning import clean_text_columns, safe_strip, normalize_whitespace_df


def test_safe_strip_varios_tipos():
    assert safe_strip("  hola   mundo  ") == "hola mundo"
    assert safe_strip(123) == 123        # no debe convertir ni romper
    assert safe_strip(None) is None      # idem
    assert safe_strip(12.5) == 12.5


def test_clean_text_columns_detecta_texto_sin_romper_numeros():
    df = pd.DataFrame({
        "codigo": [1001, 1002, 1003],                 # ints: no tocar
        "descripcion": ["  vidrio  templado ", None, "LAMINADO   3+3  "],
        "precio": [1234.5, 999.99, None],             # floats/None: no tocar
        "nota": ["  oferta   especial", 0, 1],        # mixto: hay strings, así que limpia SOLO strings
    })

    out = clean_text_columns(df)

    # columnas numéricas se conservan idénticas
    assert out["codigo"].tolist() == [1001, 1002, 1003]
    import math

    vals = out["precio"].tolist()
    assert vals[0] == 1234.5
    assert vals[1] == 999.99
    assert math.isnan(vals[2])  # permite NaN sin error

    # strings limpiados
    assert out["descripcion"].tolist() == ["vidrio templado", None, "LAMINADO 3+3"]
    # 'nota' tenía mezcla; los strings se limpian, los ints quedan igual
    assert out["nota"].tolist() == ["oferta especial", 0, 1]


def test_normalize_whitespace_df_equivale_a_clean_text_columns():
    df = pd.DataFrame({
        "a": ["  x  y ", " z "],
        "b": [1, "  dos   "],
    })
    out1 = clean_text_columns(df)
    out2 = normalize_whitespace_df(df)
    pd.testing.assert_frame_equal(out1, out2)
