# Chatbot - Búsqueda de Cristalería Automotriz

Este proyecto consiste en un chatbot inteligente en Telegram, integrado con Node-RED, que permite agilizar la búsqueda de precios y disponibilidad de cristales automotrices (parabrisas, lunetas, ventanillas, etc.) dentro de un catálogo extenso de productos.

El sistema busca resolver una problemática frecuente: la dificultad para encontrar rápidamente información específica sobre cristales de vehículos, considerando la gran variedad existente y la actualización constante de precios en el mercado argentino.

---

## Arquitectura del proyecto

El proyecto se estructura en dos partes principales:

### 1. Procesamiento de datos

Un script en Python se encarga de:

* Limpiar y estandarizar los archivos Excel provistos por fabricantes/proveedores.
* Generar un archivo JSON estructurado para que Node-RED lo interprete fácilmente.
* Mantener los datos siempre actualizados de forma automatizada.

### 2. Interfaz conversacional

A través de Telegram, el usuario interactúa con el chatbot indicando:

* Marca del vehículo
* Modelo
* Tipo de cristal

Node-RED procesa la consulta, filtra el catálogo y devuelve información clave:

* Código de producto
* Compatibilidad
* Años de fabricación
* Color / características
* Precio

El sistema está diseñado con un enfoque modular, escalable y simple de mantener.

## Tecnologías utilizadas

- Node-RED – Desarrollo de flujos y lógica conversacional.
- JavaScript (Node.js) – Procesamiento de mensajes y validaciones.
- Python – Transformación de datos (Excel → JSON).
- Telegram Bot API – Comunicación con usuarios.
- JSON – Almacenamiento estructurado.
- Git & GitHub – Control de versiones.

---

## Cómo ejecutar el proyecto

### 1. Requisitos

* Node-RED v3+
* Python 3.10+
* Token del bot creado en Telegram (BotFather)
* Catálogo en Excel del proveedor
* Librerías Python del archivo `requirements.txt`

---

### 2. Instalación

1. Clonar el repositorio:

```bash
git clone https://github.com/tu_usuario/ChatBotCarrozzoVidrios.git
cd chatbot-cristales
```

2. Instalar dependencias del script Python:

```bash
pip install -r requirements.txt
```

3. Procesar el catálogo para generar el archivo JSON:

```bash
python procesar_catalogo.py
```

4. Abrir Node-RED y importar el flujo desde `flow.json`.

5. Configurar la variable de entorno con tu token:

```
TELEGRAM_BOT_TOKEN=123456:ABC-...
```

---

### 3. Ejecutar el chatbot

1. Iniciar Node-RED:

```bash
node-red
```
2. Buscar en telegram "CarrozzoVidriosBot"
2. Enviar /start al bot desde el chat de Telegram.
3. Realizar una consulta, por ejemplo:

   * `Ford`
   * `Focus`
   * `Parabrisas`

El bot responderá con el producto correspondiente si existe en el catálogo.

---

## Estructura del proyecto

```
/
├── flow.json       # Flujo completo de Node-RED
├── flows_cred.json # Subflujos reutilizables    
│
├── data/
│   ├── catalogos/
│       └── pilkington.xlsx   # Catálogo original del proveedor
│   ├── output/
│       └── pilkington.json   # Catálogo procesado para Node-RED
│
├── scripts/
│   └── procesar_catalogo.py  # Normalizador y exportador a JSON
│
├── test/
│   └── test_procesador_catalogo.py  # Tester para el procesador de catálogo
│
├── README.md
└── requirements.txt
```

---

## Componentes clave del flujo (Node-RED)

* Router de inputs — Separa comandos (/start, /ayuda) de mensajes normales.
* Normalizador de texto — Estandariza mensajes ingresados por el usuario.
* Gestor de opciones — Orquesta el paso actual: marca → modelo → cristal.
* Funciones de búsqueda — Filtrado por marca, modelo y tipo de cristal.
* Manejo de errores — Notificación interna por Telegram en caso de fallas.
* Integración con Telegram — Entrada y salida desde el bot real.

---

## Mejoras futuras

### Nuevas características

* Calculadora de precios por medidas (alto/ancho de cristales genéricos).
* Historial de consultas y favoritos por usuario.
* Comandos adicionales como `/ultimo` o `/buscar codigo`.

### Mejoras internas

* Actualización automática del catálogo desde Google Drive, S3 o FTP.
* Validaciones avanzadas en el flujo conversacional.
* Panel web para administrar el catálogo.

### Robustez

* Logs avanzados con estadísticas de uso.
* Alertas automáticas si un proveedor cambia el formato del Excel.

---

## Autor

* Felipe Carrozzo
- Contacto: [felipe.carrozzo@ingenieria.uner.edu.ar](felipe.carrozzo@ingenieria.uner.edu.ar) 
