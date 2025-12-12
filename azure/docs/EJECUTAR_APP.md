# 🚀 Cómo Ejecutar la Aplicación Visual

## Opción 1: Usando el script de inicio (Recomendado)

### Windows:
Doble clic en `iniciar_app.bat` (próximamente)

O desde la terminal:
```bash
cd "c:\Users\gesti\GESTION COMPARTIDA Dropbox\Departamento Gestion\0001 - Control de Gestion (1)\Desarrollo\azure"
streamlit run app.py
```

## Opción 2: Desde la terminal

1. Abre una terminal (CMD o PowerShell)

2. Navega a la carpeta del proyecto:
```bash
cd "c:\Users\gesti\GESTION COMPARTIDA Dropbox\Departamento Gestion\0001 - Control de Gestion (1)\Desarrollo\azure"
```

3. Ejecuta la aplicación:
```bash
streamlit run app.py
```

4. La aplicación se abrirá automáticamente en tu navegador en:
```
http://localhost:8501
```

## 📋 Características de la Aplicación

### ✨ Funcionalidades:

1. **Carga de Archivos**
   - Modo archivo único
   - Modo múltiples archivos
   - Arrastrar y soltar
   - Formatos: JPG, JPEG, PNG, PDF

2. **Procesamiento Inteligente**
   - Extracción automática con Azure Document Intelligence
   - Fallback a Gemini AI si es necesario
   - Barra de progreso en tiempo real
   - Vista previa de cada archivo procesado

3. **Visualización de Resultados**
   - Tabla interactiva con todos los ítems
   - Estadísticas en tiempo real:
     - Total de ítems extraídos
     - Número de facturas procesadas
     - Total monetario
     - Promedio de ítems por factura

4. **Exportación**
   - Descarga de Excel con todos los datos
   - Nombre de archivo con timestamp
   - Columnas formateadas automáticamente

### 🎨 Interfaz:

- **Panel lateral**: Información del sistema y configuración
- **Área principal**: Carga de archivos y procesamiento
- **Resultados**: Vista previa y estadísticas
- **Descarga**: Botón para obtener el Excel generado

## 🔧 Solución de Problemas

### La aplicación no se abre:

1. Verifica que las dependencias estén instaladas:
```bash
pip install -r requirements.txt
```

2. Verifica que el archivo `.env` esté configurado correctamente

3. Revisa los logs en `logs/processing.log`

### Error de puerto ocupado:

Si el puerto 8501 está ocupado, puedes usar otro:
```bash
streamlit run app.py --server.port 8502
```

### Error de credenciales:

Asegúrate de que `.env` contiene:
- `AZURE_ENDPOINT`
- `AZURE_KEY`
- `GEMINI_API_KEY`

## 🛑 Detener la Aplicación

En la terminal donde se ejecutó, presiona:
- **Windows**: `Ctrl + C`
- **Mac/Linux**: `Ctrl + C`

## 💡 Consejos de Uso

1. **Calidad de las imágenes**: Usa imágenes claras y bien iluminadas para mejores resultados

2. **Múltiples archivos**: Procesa hasta 10 archivos a la vez para mejor rendimiento

3. **Formatos PDF**: Los PDFs de mejor calidad dan mejores resultados

4. **Conexión**: Asegúrate de tener conexión a internet (para Azure y Gemini)

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs en `logs/processing.log`
2. Consulta el archivo `README.md`
3. Verifica la configuración en `config.py`

---

**Última actualización**: Noviembre 2024
