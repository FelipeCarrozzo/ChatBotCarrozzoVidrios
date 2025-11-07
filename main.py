from scripts.pdf_extractor import ColumnMapper, PDFExtractor

column_mapper = ColumnMapper({
    "codigo": (46.5, 66.0),
    "descripcion": (50, 328.6),
    "parante": (328.6, 445.0),
    "incoloro": (445.2, 476.8),
    "color": (506.8, 527.6),
    "degrade": (546.5, 578.5)
})

extractor = PDFExtractor(
    pdf_path="data/catalogo_favicur_septiembre2025.pdf",
    marcas_path="data/marcas.json",
    column_mapper=column_mapper
)

extractor.extract()
extractor.to_json("data/out_meta1_marcas.json")

print("Total registros extraídos:", len(extractor.data))
