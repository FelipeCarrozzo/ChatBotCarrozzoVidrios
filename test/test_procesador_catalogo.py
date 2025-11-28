#dependencias
import unittest
from unittest.mock import mock_open, patch
import pandas as pd
from scripts.catalog_processor import CatalogProcessor, ExcelCatalogProcessor

class DummyCatalogProcessor(CatalogProcessor):
    """Implementación dummy para pruebas unitarias."""
    def extract(self):
        return pd.DataFrame()

    def to_json(self, output_path: str):
        return output_path


class TestCatalogProcessorBase(unittest.TestCase):
    """Pruebas unitarias para la clase base CatalogProcessor."""
    def setUp(self):
        self.processor = DummyCatalogProcessor("dummy.xlsx")

    def test_clean_lowers_column_names_and_drops_empty_rows(self):
        df = pd.DataFrame(
            {
                " Columna ": ["  VALOR  ", None],
                "Otra": [1, None],
            }
        )

        cleaned = self.processor.clean(df)

        self.assertEqual(cleaned.columns.tolist(), ["columna", "otra"])
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned.iloc[0]["otra"], 1)


class TestExcelCatalogProcessor(unittest.TestCase):
    """Pruebas unitarias para ExcelCatalogProcessor."""
    def setUp(self):
        self.processor = ExcelCatalogProcessor("fake.xlsx")

    def test_infer_posicion_y_lado_from_description(self):
        row = pd.Series({"cristal": "Parabrisas DER templado", "posicion": None, "lado": None})

        result = self.processor.infer_posicion_y_lado(row)

        self.assertEqual(result["posicion"], "delantero")
        self.assertEqual(result["lado"], "derecha")

    def test_infer_posicion_y_lado_preserves_existing_values(self):
        row = pd.Series({"cristal": "otro", "posicion": "Trasero", "lado": "Izquierda"})

        result = self.processor.infer_posicion_y_lado(row)

        self.assertEqual(result["posicion"], "trasero")
        self.assertEqual(result["lado"], "izquierda")

    def test_clean_normalizes_text_and_prices(self):
        df = pd.DataFrame(
            {
                " Cristal ": ["  Luneta IZQ   "],
                "posicion": [pd.NA],
                "lado": [pd.NA],
                "precio_total": ["2000.1"],
                "costo_instalacion": ["nan"],
            }
        )

        cleaned = self.processor.clean(df)

        self.assertEqual(cleaned.columns.tolist(), ["cristal", "posicion", "lado", "precio_total", "costo_instalacion"])
        self.assertEqual(cleaned.loc[0, "cristal"], "Luneta IZQ")
        self.assertEqual(cleaned.loc[0, "posicion"], "trasero")
        self.assertEqual(cleaned.loc[0, "lado"], "izquierda")
        self.assertEqual(cleaned.loc[0, "precio_total"], "$2,000.10")
        self.assertIsNone(cleaned.loc[0, "costo_instalacion"])

    @patch("scripts.catalog_processor.pd.read_excel")
    def test_extract_reads_excel_and_sets_data(self, mock_read_excel):
        sample = pd.DataFrame({"codigo": [1]})
        mock_read_excel.return_value = sample

        processor = ExcelCatalogProcessor("file.xlsx", sheet_name="Hoja1", header_row=2)
        result = processor.extract()

        mock_read_excel.assert_called_once_with("file.xlsx", sheet_name="Hoja1", header=2)
        self.assertIs(result, sample)
        self.assertIs(processor.data, sample)

    @patch("scripts.catalog_processor.pd.read_excel")
    def test_extract_wraps_errors(self, mock_read_excel):
        mock_read_excel.side_effect = ValueError("bad excel")

        with self.assertRaises(RuntimeError) as ctx:
            self.processor.extract()

        self.assertIn("Error leyendo Excel", str(ctx.exception))

    def test_to_json_requires_data(self):
        with self.assertRaises(ValueError):
            self.processor.to_json("output.json")

    def test_to_json_serializes_clean_output(self):
        self.processor.data = pd.DataFrame({"dummy": [1]})
        clean_df = pd.DataFrame({"codigo": ["A1"], "unnamed: 0": ["x"]})

        with patch.object(ExcelCatalogProcessor, "clean", return_value=clean_df) as mock_clean, \
                patch("builtins.open", mock_open()) as mocked_file, \
                patch("scripts.catalog_processor.json.dump") as mock_dump:
            self.processor.to_json("output.json")

            mock_clean.assert_called_once_with(self.processor.data)
            mocked_file.assert_called_once_with("output.json", "w", encoding="utf-8")
            dumped_data = mock_dump.call_args[0][0]
            self.assertEqual(dumped_data, [{"codigo": "A1"}])


if __name__ == "__main__":
    unittest.main()
