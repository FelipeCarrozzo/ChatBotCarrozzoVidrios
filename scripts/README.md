## Descripción general

`catalog_processor.py` contiene la infraestructura para procesar catálogos de cristales en distintos formatos. Está dividido en una clase base abstracta que define el contrato (`CatalogProcessor`) y una implementación concreta para archivos Excel (`ExcelCatalogProcessor`).

## CatalogProcessor

- **Responsabilidad:** encapsular la ruta del archivo y definir el flujo mínimo de procesamiento.
- **Atributos principales:**
  - `path`: ruta al archivo fuente.
  - `data`: `DataFrame` con los datos extraídos; se asigna en `extract`.
- **Métodos:**
  - `extract()`: abstracto; cada subclase decide cómo leer el origen.
  - `clean(df)`: limpieza básica reutilizable que copia el `DataFrame`, normaliza encabezados (trim + lower) y elimina filas completamente vacías.
  - `to_json(output_path)`: abstracto; exporta el resultado con la estructura estandarizada.

## ExcelCatalogProcessor

Implementa el contrato para catálogos almacenados en Excel.

- **Inicialización (`__init__`)**
  - Parámetros: `path`, `sheet_name` (nombre o índice), `header_row` (fila de encabezados 0-indexada).
  - Guarda los parámetros y aprovecha el constructor de la clase base.

- **Extracción (`extract`)**
  - Usa `pandas.read_excel` con los argumentos configurados.
  - Envuelve errores en un `RuntimeError` claro.
  - La tabla cargada se guarda en `self.data`.

- **Inferencia (`infer_posicion_y_lado`)**
  - Normaliza los campos `posicion` y `lado`, contemplando `None`, `NaN` y textos como `"nan"`/`"none"`.
  - Si faltan datos, analiza la descripción (`cristal`) para deducir:
    - `"parabrisas"` → `posicion = "delantero"`.
    - `"luneta"` → `posicion = "trasero"`.
    - `"izq"` / `"der"` → `lado = "izquierda"` / `"derecha"`.
  - Devuelve una `pd.Series` con los valores resultantes.

- **Limpieza completa (`clean`)**
  1. Aplica la limpieza base de `CatalogProcessor`.
  2. Reemplaza `pd.NA` por `None` para homogenizar vacíos.
  3. Normaliza todas las columnas de texto (trim + colapso de espacios múltiples).
  4. Completa `posicion` y `lado` usando `infer_posicion_y_lado`.
  5. Detecta columnas monetarias buscando `precio`, `total` o `instalacion` en su nombre:
     - Convierte a numérico tolerante a errores.
     - Redondea a dos decimales.
     - Convierte a formato de texto `$X,XXX.XX`, dejando `None` si no hay valor válido.

- **Exportación (`to_json`)**
  - Requiere que `self.data` exista (se debe llamar antes a `extract`).
  - Limpia el `DataFrame`, elimina columnas cuyo nombre inicia con `"unnamed"` y serializa el resultado a JSON (UTF-8, `ensure_ascii=False`, indentación 2).
  - Informa por consola la ruta de salida.

## Dependencias y extensiones

- **Dependencias principales:** `pandas` para la manipulación tabular, `json` para la exportación y `abc` para la abstracción.
- **Cómo extender:**
  1. Crear nuevas subclases de `CatalogProcessor` para otras fuentes (PDF, CSV, APIs, etc.).
  2. Implementar `extract` y `to_json` según las necesidades del formato.
  3. Sobrescribir `clean` si se requieren reglas adicionales sin perder la normalización básica.
