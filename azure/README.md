# Sistema de Extracción de Datos de Facturas

Sistema automatizado para extraer información de facturas usando **Azure Document Intelligence** y **Google Gemini AI**, con integración a Google Drive y una **interfaz web visual**.

## 🎯 Características

- ✅ **Interfaz Web Visual** con Streamlit (¡NUEVO!)
- ✅ Extracción automática de ítems de facturas (imágenes y PDFs)
- ✅ Procesamiento híbrido: Azure Document Intelligence + Gemini AI
- ✅ Sistema de plugins por proveedor para personalización
- ✅ Integración con Google Drive para procesamiento masivo
- ✅ Exportación a Excel con resumen detallado
- ✅ Logging completo con niveles de detalle
- ✅ Configuración centralizada y segura
- ✅ Carga de archivos por arrastrar y soltar
- ✅ Procesamiento de múltiples facturas simultáneamente
- ✅ Vista previa de resultados en tiempo real

## 📋 Requisitos

- Python 3.8+
- Cuenta de Azure con Document Intelligence habilitado
- API Key de Google Gemini
- Credenciales de Google Cloud (Service Account) para Drive

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd azure
```

### 2. Crear entorno virtual

```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar credenciales

#### a) Crear archivo `.env`

Copia el archivo `.env.example` (o crea uno nuevo) con el siguiente contenido:

```env
# Azure Document Intelligence
AZURE_ENDPOINT=https://tu-recurso.cognitiveservices.azure.com/
AZURE_KEY=tu_clave_azure_aqui

# Google Gemini AI
GEMINI_API_KEY=tu_api_key_gemini_aqui
GEMINI_MODEL=gemini-2.0-flash

# Google Drive
FOLDER_ID=id_de_carpeta_drive
DRIVE_CREDENTIALS_FILE=credentials/credentials.json

# Opcional: Desactivar Azure (usa solo Gemini)
# SKIP_AZURE=1

# Opcional: Configuraciones avanzadas
# OUTPUT_FILE=mi_archivo.xlsx
# MAX_ITEMS_DISPLAY=50
# CALCULATION_TOLERANCE=0.01
# SLEEP_BETWEEN_FILES=0.4
```

#### b) Obtener credenciales de Google Drive

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto o selecciona uno existente
3. Habilita la API de Google Drive
4. Crea una cuenta de servicio (Service Account)
5. Descarga el archivo JSON de credenciales
6. Guárdalo en `credentials/credentials.json`

### 5. Validar configuración

```bash
python config.py
```

Esto verificará que todas las variables de entorno y archivos necesarios estén configurados correctamente.

## 📖 Uso

### 🎨 Opción 1: Interfaz Web Visual (Recomendado)

La forma más fácil de usar el sistema es mediante la interfaz web:

#### Windows:
```bash
# Doble clic en el archivo:
iniciar_app.bat
```

#### Terminal:
```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

**Funcionalidades de la interfaz:**
- 📤 Carga de archivos por arrastrar y soltar
- 🔄 Procesamiento de uno o múltiples archivos
- 📊 Vista previa de resultados en tiempo real
- 💾 Descarga directa del Excel generado
- 📈 Estadísticas automáticas (total ítems, monto total, etc.)
- 🎯 Interfaz intuitiva y fácil de usar

### 🖥️ Opción 2: Procesamiento masivo desde Google Drive

```bash
python analyze_invoice.py
```

Este script:
1. Lee todos los archivos de la carpeta de Drive configurada
2. Procesa cada imagen/PDF extrayendo los ítems de la factura
3. Aplica plugins de proveedor si están disponibles
4. Genera un archivo Excel (`items.xlsx`) con:
   - **Hoja "items"**: Todos los ítems extraídos
   - **Hoja "resumen"**: Estadísticas por archivo

### 🔬 Opción 3: Prueba desde línea de comandos

Para probar con un solo archivo desde la terminal:

```bash
python test.py ruta/al/archivo.jpg
```

O configura `TEST_FILE_PATH` en `.env` y ejecuta:

```bash
python test.py
```

## 🆚 Comparación de Métodos

| Característica | Interfaz Web | Línea de Comandos | Drive Masivo |
|----------------|--------------|-------------------|--------------|
| **Facilidad de uso** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Vista previa** | ✅ Sí | ❌ No | ❌ No |
| **Múltiples archivos** | ✅ Sí | ❌ No | ✅ Sí |
| **Descarga inmediata** | ✅ Sí | ❌ No | ✅ Sí |
| **Estadísticas visuales** | ✅ Sí | ❌ No | Archivo Excel |
| **Ideal para** | Usuarios finales | Testing | Automatización |

## 🔧 Estructura del Proyecto

```
azure/
├── .env                      # Variables de entorno (NO commitear)
├── .env.example             # Plantilla de configuración
├── .gitignore               # Archivos a ignorar en git
├── config.py                # Configuración centralizada
├── logger.py                # Sistema de logging
├── requirements.txt         # Dependencias del proyecto
├── README.md                # Este archivo
├── SECURITY.md              # Guía de seguridad
├── EJECUTAR_APP.md          # Instrucciones para la interfaz web
│
├── app.py                   # ⭐ Interfaz web visual (NUEVO)
├── iniciar_app.bat          # ⭐ Script de inicio Windows (NUEVO)
├── analyze_invoice.py       # Script principal (procesamiento masivo)
├── test.py                  # Script de prueba (archivo individual)
├── connect_gemini.py        # Conector con Gemini AI
│
├── credentials/             # Credenciales de Google (NO commitear)
│   └── credentials.json
│
├── proveedores/             # Plugins por proveedor
│   ├── __init__.py
│   ├── ejemplo_proveedor.py
│   └── ...
│
├── temp/                    # Archivos temporales (generado automáticamente)
│
└── logs/                    # Logs de procesamiento
    └── processing.log
```

## 🔌 Sistema de Plugins de Proveedores

Puedes crear plugins personalizados para cada proveedor en la carpeta `proveedores/`.

### Ejemplo de plugin:

```python
# proveedores/mi_proveedor.py

import re

# Patrones para detectar el proveedor por nombre de archivo
PATTERNS = [
    r"mi_proveedor",
    r"PROVEEDOR_SA",
]

# Prompt adicional para Gemini
PROMPT = """
Este proveedor usa un formato especial:
- Los códigos tienen el prefijo "MP-"
- Las cantidades pueden estar en cajas de 12 unidades
"""

def transform_azure(items):
    """
    Transforma los ítems extraídos por Azure.
    Se ejecuta ANTES de validar si hacer handoff a Gemini.
    """
    for item in items:
        # Ejemplo: normalizar códigos
        codigo = item.get("Codigo")
        if codigo and not codigo.startswith("MP-"):
            item["Codigo"] = f"MP-{codigo}"
    return items

def transform_items(items):
    """
    Transforma los ítems finales (generalmente de Gemini).
    Se ejecuta DESPUÉS de la extracción completa.
    """
    for item in items:
        # Ejemplo: convertir cajas a unidades
        cantidad = item.get("Cantidad")
        if cantidad and cantidad > 100:
            item["Cantidad"] = cantidad * 12
    return items

def should_full_handoff_custom(items):
    """
    Decide si hacer handoff completo a Gemini.
    Retorna: (bool, List[str])
    """
    # Lógica personalizada
    if len(items) < 5:
        return True, ["Muy pocos ítems detectados por Azure"]
    return False, []
```

## 📊 Formato de Salida

El archivo Excel generado contiene:

### Hoja "items"
| Archivo | FileId | Codigo | Descripcion | Cantidad | PrecioUnitario | Subtotal |
|---------|--------|--------|-------------|----------|----------------|----------|
| factura1.pdf | abc123 | COD001 | Producto A | 10 | 100.50 | 1005.00 |

### Hoja "resumen"
| Archivo | ItemsDetectados | UsoGeminiFull | UsoTransformProveedor | Issues | PluginProveedor |
|---------|-----------------|---------------|----------------------|--------|-----------------|
| factura1.pdf | 15 | True | True | None | proveedores.ejemplo |

## 🐛 Troubleshooting

### Error: "Variable de entorno requerida no encontrada"

Asegúrate de tener todas las variables requeridas en tu archivo `.env`:
- `AZURE_ENDPOINT`
- `AZURE_KEY`
- `GEMINI_API_KEY`

### Error: "Archivo de credenciales no encontrado"

Verifica que el archivo `credentials/credentials.json` existe y la ruta en `.env` es correcta.

### Azure no detecta ítems correctamente

1. Verifica que el formato de factura sea compatible
2. Intenta con `SKIP_AZURE=1` para usar solo Gemini
3. Crea un plugin de proveedor con `transform_azure()` para normalizar los datos

### Los logs no se generan

Verifica que la carpeta `logs/` tenga permisos de escritura.

## 🔒 Seguridad

**⚠️ IMPORTANTE: NUNCA commitees credenciales al repositorio**

- El archivo `.gitignore` ya está configurado para ignorar:
  - `.env`
  - `credentials/`
  - `*.log`
  - `items.xlsx`

Antes de compartir el código:
1. Verifica que no hay claves hardcodeadas
2. Revisa el historial de git con `git log`
3. Si accidentalmente commiteaste credenciales:
   - Rótalas INMEDIATAMENTE desde las consolas de Azure/Google
   - Limpia el historial de git

## 📝 Logs

Los logs se guardan en dos niveles:

1. **Consola (INFO)**: Mensajes importantes del procesamiento
2. **Archivo (DEBUG)**: Detalles completos en `logs/processing.log`

Para ver logs detallados:
```bash
tail -f logs/processing.log
```

## 🤝 Contribuir

1. Crea un branch para tu feature: `git checkout -b feature/nueva-funcionalidad`
2. Haz commit de tus cambios: `git commit -m "Agrega nueva funcionalidad"`
3. Push al branch: `git push origin feature/nueva-funcionalidad`
4. Abre un Pull Request

## 📄 Licencia

[Especifica tu licencia aquí]

## 👤 Autor

[Tu nombre/organización]

## 🆘 Soporte

Para reportar bugs o solicitar features, abre un issue en el repositorio.

---

**Última actualización**: Noviembre 2024
