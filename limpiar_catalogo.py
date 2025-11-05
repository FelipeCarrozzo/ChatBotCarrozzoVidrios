"""Script para limpiar y estructurar catálogos de autopartes desde un PDF.

Este módulo extrae tablas utilizando Camelot (con Tabula como alternativa),
normaliza el contenido y genera un JSON listo para ser consumido por flujos
de Node-RED. También produce registros de extracción y validación.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Configuración de registros
# ---------------------------------------------------------------------------


def _configure_logger(log_path: Path, name: str) -> logging.Logger:
    """Crea y configura un *logger* que escribe en ``log_path``."""

    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Evita añadir múltiples *handlers* cuando se llama varias veces.
    if not logger.handlers:
        handler = logging.FileHandler(log_path, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# ---------------------------------------------------------------------------
# Estructuras auxiliares
# ---------------------------------------------------------------------------


@dataclass
class ExtractionResult:
    tables: List[pd.DataFrame]
    processed: int
    failed: int


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def load_mapping(mapping_path: Optional[Path]) -> Dict[str, str]:
    """Carga el archivo de mapeo de columnas.

    El archivo debe contener un diccionario JSON donde las claves representan
    los encabezados originales (en cualquier combinación de mayúsculas y
    minúsculas) y los valores los nombres normalizados deseados.
    """

    if not mapping_path:
        return {}

    if not mapping_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de mapeo: {mapping_path}")

    with mapping_path.open("r", encoding="utf-8") as fh:
        mapping_data = json.load(fh)

    return {key.strip().upper(): value.strip().lower() for key, value in mapping_data.items()}


def extract_tables(pdf_path: Path, extraction_logger: logging.Logger) -> ExtractionResult:
    """Extrae todas las tablas presentes en un PDF.

    Intenta primero con Camelot (sabor *lattice*), y si falla recurre a
    Tabula-py. Devuelve un ``ExtractionResult`` con las tablas y métricas
    relacionadas para los registros.
    """

    tables: List[pd.DataFrame] = []
    processed = 0
    failed = 0

    try:
        import camelot

        extraction_logger.info("Extrayendo tablas con Camelot...")
        camelot_tables = camelot.read_pdf(
            str(pdf_path), pages="all", flavor="lattice", strip_text="\n"
        )
        processed = len(camelot_tables)
        tables.extend(table.df for table in camelot_tables)
        extraction_logger.info("Camelot extrajo %s tablas.", processed)
    except Exception as camelot_error:  # pragma: no cover - dependencias externas
        extraction_logger.error("Falló Camelot: %s", camelot_error)
        try:
            import tabula

            extraction_logger.info("Intentando extracción con Tabula-py...")
            tabula_tables = tabula.read_pdf(
                str(pdf_path), pages="all", multiple_tables=True, lattice=True
            )
            processed = len(tabula_tables)
            tables.extend(tabula_tables)
            extraction_logger.info("Tabula-py extrajo %s tablas.", processed)
        except Exception as tabula_error:  # pragma: no cover - dependencias externas
            extraction_logger.error("Falló Tabula-py: %s", tabula_error)
            failed = 1

    if processed == 0 and not tables:
        extraction_logger.warning("No se extrajeron tablas del PDF %s", pdf_path)
        failed = 1 if failed == 0 else failed

    return ExtractionResult(tables=tables, processed=processed, failed=failed)


def normalize_columns(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """Normaliza los encabezados de ``df`` utilizando ``mapping`` y reglas internas."""

    df = df.copy()
    normalized_columns: Dict[str, str] = {}

    # Reglas internas (valores por defecto) en caso de que no exista mapeo.
    default_mapping = {
        "MARCA": "marca",
        "MODELO": "modelo",
        "MODELO/ANIO": "modelo",
        "MODELO/AÑO": "modelo",
        "PIEZA": "pieza",
        "DESCRIPCION": "pieza",
        "DESCRIPCIÓN": "pieza",
        "COD": "codigo",
        "CODIGO": "codigo",
        "CÓDIGO": "codigo",
        "PRECIO": "precio",
        "PVP": "precio",
        "DIMENSION": "dimensiones",
        "DIMENSIONES": "dimensiones",
        "COLOR": "color",
        "DEGRADE": "degrade",
        "DEGRADÉ": "degrade",
    }

    merged_mapping = {**default_mapping, **mapping}

    for column in df.columns:
        normalized = merged_mapping.get(column.strip().upper(), column.strip().lower())
        normalized_columns[column] = normalized

    df.rename(columns=normalized_columns, inplace=True)
    return df


def clean_text(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica operaciones de limpieza a todas las columnas de texto en ``df``."""

    df = df.copy()

    for column in df.columns:
        if df[column].dtype == object:
            df[column] = (
                df[column]
                .fillna("")
                .astype(str)
                .str.replace("\s+", " ", regex=True)
                .str.replace("\n", " ", regex=False)
                .str.strip()
                .str.upper()
            )
        else:
            df[column] = df[column]

    # Reemplaza cadenas vacías por NaN para simplificar validaciones posteriores.
    df.replace({"": np.nan, "NAN": np.nan}, inplace=True)
    return df


def _parse_price(value: object) -> Optional[float]:
    """Convierte una representación textual de precio a ``float``."""

    if value is None or (isinstance(value, float) and np.isnan(value)):
        return np.nan

    text = str(value)
    if not text:
        return np.nan

    # Elimina símbolos de moneda y otros caracteres.
    cleaned = re.sub(r"[^0-9,.-]", "", text)

    if cleaned.count(",") > 1 and cleaned.count(".") > 0:
        # Formato europeo tipo 1.234,56 -> 1234.56
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif cleaned.count(",") == 1 and cleaned.count(".") == 0:
        cleaned = cleaned.replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")

    try:
        return float(cleaned)
    except ValueError:
        return np.nan


def parse_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza la columna ``precio`` si existe."""

    df = df.copy()
    if "precio" in df.columns:
        df["precio"] = df["precio"].apply(_parse_price)
    return df


def _row_text(row: pd.Series, reference_columns: Iterable[str]) -> str:
    """Obtiene un texto de referencia concatenado para detección jerárquica."""

    values = [str(row[col]) for col in reference_columns if isinstance(row.get(col), str)]
    text = " ".join(v for v in values if v)
    return text.strip()


def enrich_hierarchy(df: pd.DataFrame) -> pd.DataFrame:
    """Identifica y propaga marcas y modelos a las filas de ``df``."""

    df = df.copy()

    # Define columnas de texto relevantes.
    reference_columns: List[str] = []
    for candidate in ["pieza", "descripcion", "detalle", df.columns[0]]:
        if candidate in df.columns and candidate not in reference_columns:
            reference_columns.append(candidate)

    marca_actual: Optional[str] = None
    modelo_actual: Optional[str] = None
    filas_a_descartar: List[int] = []

    marca_regex = re.compile(r"^[A-ZÁÉÍÓÚÜÑ\s]+$")
    modelo_regex = re.compile(r"(MOD\.|MOD |\b\d{4}\b|\/|')")

    for index, row in df.iterrows():
        texto = _row_text(row, reference_columns)
        es_precio = any(
            isinstance(row.get(col), (int, float))
            or (isinstance(row.get(col), str) and re.search(r"\d", row.get(col)))
            for col in ["precio", "codigo"]
            if col in df.columns
        )

        if texto and marca_regex.fullmatch(texto) and not es_precio:
            marca_actual = texto.strip()
            modelo_actual = None
            filas_a_descartar.append(index)
            continue

        if texto and modelo_regex.search(texto) and not es_precio:
            modelo_actual = texto.strip()
            filas_a_descartar.append(index)
            continue

        if marca_actual:
            df.at[index, "marca"] = marca_actual
        if modelo_actual:
            df.at[index, "modelo"] = modelo_actual

    if filas_a_descartar:
        df.drop(index=filas_a_descartar, inplace=True)

    df.reset_index(drop=True, inplace=True)
    return df


def validate_rows(df: pd.DataFrame, validation_logger: logging.Logger) -> pd.DataFrame:
    """Valida las filas requeridas y escribe el resumen en ``validation_logger``."""

    required_columns = ["marca", "modelo", "pieza", "precio"]

    total_filas = len(df)
    validas = 0
    descartadas = 0

    motivos_descartes: Dict[str, int] = {}

    registros_validos: List[pd.Series] = []

    for _, row in df.iterrows():
        motivos: List[str] = []
        for column in required_columns:
            valor = row.get(column)
            if (isinstance(valor, float) and np.isnan(valor)) or not valor:
                motivos.append(f"{column} vacío")

        if motivos:
            descartadas += 1
            motivo_clave = ", ".join(sorted(motivos))
            motivos_descartes[motivo_clave] = motivos_descartes.get(motivo_clave, 0) + 1
            continue

        validas += 1
        registros_validos.append(row)

    validation_logger.info("Filas procesadas: %s", total_filas)
    validation_logger.info("Filas válidas: %s", validas)
    validation_logger.info("Filas descartadas: %s", descartadas)
    for motivo, cantidad in motivos_descartes.items():
        validation_logger.info(" - %s: %s", motivo, cantidad)

    if registros_validos:
        return pd.DataFrame(registros_validos)
    return pd.DataFrame(columns=df.columns)


def export_json(df: pd.DataFrame, output_path: Path) -> None:
    """Exporta ``df`` como JSON plano en ``output_path``."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    records = df.replace({np.nan: None}).to_dict(orient="records")
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(records, fh, ensure_ascii=False, indent=2)


def process_catalog(
    pdf_path: Path,
    mapping_path: Optional[Path],
    output_path: Path,
    extraction_logger: logging.Logger,
    validation_logger: logging.Logger,
) -> None:
    """Ejecuta el flujo completo de procesamiento del catálogo."""

    if not pdf_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo PDF: {pdf_path}")

    mapping = load_mapping(mapping_path)
    extraction_logger.info("Procesando catálogo: %s", pdf_path)

    extraction = extract_tables(pdf_path, extraction_logger)

    if not extraction.tables:
        extraction_logger.warning("No hay tablas para procesar. Finalizando.")
        export_json(pd.DataFrame(), output_path)
        return

    combined_df = pd.concat(extraction.tables, ignore_index=True, sort=False)
    extraction_logger.info("Total de filas extraídas: %s", len(combined_df))

    normalized_df = normalize_columns(clean_text(combined_df), mapping)
    normalized_df = parse_prices(normalized_df)
    enriched_df = enrich_hierarchy(normalized_df)

    # Elimina duplicados y filas completamente vacías.
    enriched_df.dropna(how="all", inplace=True)
    enriched_df.drop_duplicates(inplace=True)

    validated_df = validate_rows(enriched_df, validation_logger)
    export_json(validated_df, output_path)

    extraction_logger.info("Exportación completada: %s", output_path)


def parse_arguments(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Define y analiza los argumentos de línea de comandos."""

    parser = argparse.ArgumentParser(description="Limpia y estandariza un catálogo PDF")
    parser.add_argument(
        "pdf",
        type=Path,
        help="Ruta del PDF del catálogo",
    )
    parser.add_argument(
        "--mapeo",
        type=Path,
        default=None,
        help="Ruta del archivo JSON con el mapeo de columnas",
    )
    parser.add_argument(
        "--salida",
        type=Path,
        default=Path("data/catalogo.json"),
        help="Ruta del archivo JSON de salida",
    )
    parser.add_argument(
        "--log-extraccion",
        type=Path,
        default=Path("logs/extraccion.log"),
        help="Ruta del log de extracción",
    )
    parser.add_argument(
        "--log-validacion",
        type=Path,
        default=Path("logs/validacion.log"),
        help="Ruta del log de validación",
    )

    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_arguments(argv)

    extraction_logger = _configure_logger(args.log_extraccion, "extraccion")
    validation_logger = _configure_logger(args.log_validacion, "validacion")

    try:
        process_catalog(
            pdf_path=args.pdf,
            mapping_path=args.mapeo,
            output_path=args.salida,
            extraction_logger=extraction_logger,
            validation_logger=validation_logger,
        )
    except Exception as error:  # pragma: no cover - ejecución CLI
        extraction_logger.error("Error procesando el catálogo: %s", error)
        print(f"Error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - entrada script
    sys.exit(main())

