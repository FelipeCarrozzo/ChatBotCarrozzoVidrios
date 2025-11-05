import pandas as pd
import math
from src.price import parse_price, clean_price_column


def test_parse_price_formato_internacional():
    assert parse_price("321,694.32") == 321694.32
    assert parse_price("$ 48,293.94") == 48293.94
    assert parse_price("1.234,56") == 1234.56


def test_parse_price_casos_invalidos():
    for inval in ["", "-", "–", "CONSULTAR", "0", None]:
        assert parse_price(inval) is None

def test_clean_price_column_devuelve_floats():
    df = pd.DataFrame({"Incoloro": ["321,694.32", "0", "-", " 48,293.94 "]})
    out = clean_price_column(df, "Incoloro")
    vals = out["Incoloro"].tolist()

    assert vals[0] == 321694.32
    assert math.isnan(vals[1])        # ← acepta NaN
    assert math.isnan(vals[2])        # ← acepta NaN
    assert vals[3] == 48293.94

