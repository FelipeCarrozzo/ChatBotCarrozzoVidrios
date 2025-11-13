from scripts.catalog_processor import ExcelCatalogProcessor

processor = ExcelCatalogProcessor("data/catalogos/pilkington.xlsx", sheet_name=0)
df = processor.extract()
processor.to_json("data/output/pilkington.json")

