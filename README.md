# Chatbot de Búsqueda de Cristalería Automotriz

Este proyecto consiste en el desarrollo de un **chatbot inteligente en Telegram**, integrado con Node-RED, que permite agilizar la búsqueda de precios y disponibilidad de cristales automotrices (parabrisas, lunetas, ventanillas, etc.) dentro de un catálogo extenso de productos.

El sistema busca resolver una problemática frecuente: la dificultad para encontrar rápidamente información específica sobre piezas, marcas y modelos de vehículos, considerando la gran variedad existente y la actualización constante de precios en el mercado argentino.

Para lograrlo, el proyecto se estructura en dos partes principales:

1. Procesamiento de datos: Un script en Python se encarga de limpiar y estandarizar los archivos Excel provistos por el fabricante o distribuidor, transformándolos en un formato JSON estructurado que Node-RED puede interpretar fácilmente. Este proceso prepara la información de forma automatizada para mantener el catálogo siempre actualizado.

2. Interfaz conversacional: A través de Telegram, el usuario puede interactuar con el chatbot mediante comandos simples como /buscar, especificando categoría, marca, modelo y año del vehículo. Node-RED procesa la consulta, filtra los datos del catálogo y devuelve la información correspondiente — incluyendo precio, categoría y disponibilidad — de manera clara y rápida.

## Cómo ejecutar `limpiar_catalogo.py`

El script `limpiar_catalogo.py` convierte un catálogo PDF en un JSON limpio. Para probarlo con tu propio archivo PDF sigue estos pasos:

1. **Prepara el entorno de Python** (opcional pero recomendado):

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows usa: .venv\Scripts\activate
   pip install pandas numpy camelot-py[cv] tabula-py
   ```

   > **Nota:** Camelot requiere tener instalado Ghostscript y, si usas `tabula-py`, necesitas Java.

2. **Ejecuta el script indicando la ruta del PDF** (y opcionalmente los parámetros disponibles):

   ```bash
   python limpiar_catalogo.py ruta/al/catalogo.pdf \
       --mapeo data/mapeo_columnas.json \
       --salida data/catalogo.json \
       --log-extraccion logs/extraccion.log \
       --log-validacion logs/validacion.log
   ```

   - `--mapeo` es opcional y permite indicar un JSON con el mapeo de nombres de columnas personalizados.
   - `--salida` define el archivo JSON generado (por defecto `data/catalogo.json`).
   - `--log-extraccion` y `--log-validacion` especifican dónde se guardan los registros.

3. **Revisa los resultados:**

   - El JSON limpio estará en la ruta indicada en `--salida`.
   - Los archivos de log detallan el proceso de extracción y validación.

El sistema está diseñado con un enfoque modular, escalable y automatizable, permitiendo:

- Integrar nuevas categorías de productos sin modificar la lógica base.

- Actualizar los datos automáticamente ante nuevos catálogos del proveedor.

- Enviar alertas o reportes en caso de errores o cambios en el formato de los archivos.

---

## Plan inicial de desarrollo:

### **FASE 1 — Diseño y planificación**

> Objetivo: Definir la estructura lógica del sistema y la organización de datos.

Tareas:

- Definir el flujo general del sistema:

    - Entrada de datos (catálogo del proveedor).

    - Limpieza y estandarización.

    - Búsqueda y filtrado.

    - Respuesta al usuario en Telegram.

1. Diseñar la estructura estándar del catálogo JSON.

    Ejemplo de campos posibles según los datos:

    ```[
    {
    "categoria": "parabrisas",
    "marca": "Ford",
    "modelo": "Focus",
    "año_desde": 2015,
    "año_hasta": 2018,
    "precio": 85000
    }
    ]
    ```
2. Identificar las categorías principales (parabrisas, luneta, ventanillas, etc.) y posibles subcategorías.

3. Definir los comandos de interacción del chatbot:

    - /start → bienvenida.

    - /buscar → iniciar búsqueda.

    - V/ayuda → guía de uso.

    - Crear un mapa de nodos de Node-RED (diagrama lógico).

---

### **FASE 2 — Preparación y limpieza de datos**

> Objetivo: Convertir los catálogos del proveedor (en formato PDF) a un conjunto de datos estructurados, limpios y legibles para Node-RED.

Tareas:

1. Extracción inicial del PDF

- Implementar un script en Python que:

    - Lea el archivo PDF del proveedor (por ejemplo, catalogo_favicur.pdf).

    - Extraiga las tablas de cada página utilizando una librería de parsing tabular (preferentemente camelot
    o tabula-py
    ).

    - Combine todas las tablas en un único DataFrame de trabajo.

    - Genere un log con las páginas procesadas y posibles errores (páginas vacías o con layout irregular).

2. Normalización del texto

- Limpiar los datos crudos:

    - Eliminar filas vacías, espacios múltiples y saltos de línea.

    - Convertir todo a mayúsculas para uniformidad.

    - Eliminar símbolos de moneda ($, .) y convertir los precios a número.

    - Estandarizar los nombres de columnas (por ejemplo: "Nombre Parante" → parante).

    - Reemplazar guiones o abreviaturas (MOD.'08 EN ADEL. → 2008+).


3. Detección de jerarquía (marca → modelo → producto)


- a. Identificación de marcas

    - Las marcas aparecen como títulos en mayúsculas completas, alineadas a la izquierda (línea verde en el catálogo). Regla: si la línea contiene solo letras y espacios, y no hay precios ni dimensiones, se marca como marca actual.

- b. Identificación de modelos

    - Los modelos aparecen justo debajo de la marca, también en mayúsculas, pero con estructuras como: A3, S 3, TIGGO, ASTRA, AGILE, etc. Frecuentemente acompañados por versiones de año: MOD.'05/'12, EN ADEL., etc.

    - Regla: si una fila tiene texto sin precio pero contiene MOD. o ' o /, se interpreta como modelo actual.

- c. Detección jerárquica (marca y modelo)

    - Marca: línea en mayúsculas completas, sin precio ni dimensiones (ej. CHEVROLET, BMW).

    - Modelo: línea inmediatamente debajo de la marca, también en mayúsculas, con patrones tipo MOD.'05/'12 o EN ADEL..

    - Asignación: cada producto hereda la última marca y modelo detectados hasta que aparezcan nuevos encabezados.

- d. Validaciones

    - Verificar que cada registro tenga: marca y modelo asignados, precio numérico, pieza (descripción) no vacía, eliminar duplicados y filas incompletas generar un log de control en logs/validacion.log con resumen de: Total de filas leídas, válidas y descartadas.

- e. Exportación a JSON plano

    - Estructura de salida (una entrada por producto):

```
[
  {
    "marca": "CHEVROLET",
    "modelo": "ASTRA",
    "pieza": "PUERTA TRAS.IZQ.",
    "codigo": "31193",
    "precio": 238788.11,
    "dimensiones": "497x745",
    "color": "INCOLORO",
    "degrade": "NO"
  },
  {
    "marca": "CHEVROLET",
    "modelo": "ASTRA",
    "pieza": "PUERTA TRAS.DER.",
    "codigo": "31192",
    "precio": 244879.20,
    "dimensiones": "497x745"
  }
]
```

---

### **FASE 3 — Proceso semiautomático controlado de actualización**

> Objetivo: Automatizar la detección y validación de nuevos catálogos.

Tareas:

1. En Node-RED:

    - Usar el nodo “watch” para detectar nuevos archivos en la carpeta data/catalogos_nuevos/.

    - Ejecutar automáticamente el script de limpieza mediante un nodo “exec”.

2. Crear una rutina de validación:

    - Verificar la presencia de campos obligatorios (marca, modelo, precio).

    - Comparar cantidad de filas y precios con el catálogo anterior.

3. Detectar valores nulos o inconsistentes.

- Implementar alertas automáticas (por Telegram o dashboard interno) ante errores de formato o validación.

- Si el nuevo catálogo es correcto, mover el archivo a data/catalogos_procesados/ y actualizar el JSON principal.

---

### **FASE 4 — Lógica de búsqueda y filtrado en Node-RED**

> Objetivo: Permitir consultas precisas sobre el catálogo desde el chatbot.

Tareas:

1. Implementar el comando /buscar en el nodo telegram command.

2. Analizar el texto del usuario:

- Detectar la categoría (parabrisas, luneta, etc.).

- Detectar marca, modelo y año.

- Normalizar texto (mayúsculas, tildes, etc.).

3. Leer el archivo catalogo.json con el nodo file in.

4. Filtrar los datos mediante un nodo function que use coincidencias parciales y rango de años.

5. Formatear la respuesta y enviarla al usuario con un nodo telegram sender.

6. Manejar respuestas de error o sin resultados.

---

### **FASE 5 — Interfaz de usuario y flujo conversacional**

> Objetivo: Hacer la interacción amigable y guiada.

Tareas:

1. Diseñar mensajes claros para cada etapa:

- Bienvenida y ayuda inicial.

- Ejemplo de búsqueda (/buscar parabrisas ford focus 2018).

- Mensajes de error o sugerencias.

2. Implementar botones interactivos (inline keyboards) opcionales:

- Selección de categoría.

- Confirmación de búsqueda.

3. Configurar nodos de depuración y logs para observar la comunicación con Telegram.

### **FASE 6 — Validación y pruebas**

> Objetivo: Asegurar la estabilidad y confiabilidad del sistema.

Tareas:

1. Crear un set de casos de prueba (búsquedas correctas, errores de tipeo, modelo inexistente, etc.).

2. Verificar tiempos de respuesta y comportamiento ante múltiples consultas.

3. Simular actualización de catálogo para probar el flujo de detección y limpieza.

4. Documentar resultados y posibles mejoras.

---

### **FASE 7 — Mantenimiento y evolución**

> Objetivo: Mantener el sistema actualizado y preparado para nuevas funciones.

Tareas:

1. Incorporar un panel de administración (con Node-RED Dashboard) que muestre:

- Fecha de último catálogo cargado.

- Cantidad de registros.

- Historial de errores de validación.

2. Evaluar integración con una base de datos local (SQLite) si el volumen de datos crece.

3. Agregar registro de estadísticas de uso del bot.

4. Documentar todo el flujo final (para presentación o memoria del proyecto).

---

## **Resultado esperado**

Un sistema completo donde:

- El proveedor envía un catálogo nuevo → Node-RED lo detecta, lo limpia y valida.

- El usuario consulta por Telegram → obtiene respuesta rápida, limpia y actualizada.

- El administrador puede monitorear el estado de los datos y recibir alertas ante errores.