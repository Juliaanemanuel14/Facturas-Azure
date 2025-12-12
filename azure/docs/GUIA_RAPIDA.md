# 🚀 Guía Rápida - Extractor de Facturas

## Inicio Rápido (3 pasos)

### 1️⃣ Instalar (solo la primera vez)
```bash
pip install -r requirements.txt
```

### 2️⃣ Configurar (solo la primera vez)
Verifica que el archivo `.env` tenga tus credenciales

### 3️⃣ Ejecutar
```bash
# Opción A: Doble clic en Windows
iniciar_app.bat

# Opción B: Desde terminal
streamlit run app.py
```

## 📱 Usar la Aplicación Web

1. **Se abre el navegador automáticamente** en `http://localhost:8501`

2. **Arrastra tus facturas** o haz clic para seleccionarlas
   - Formatos: JPG, PNG, PDF
   - Puedes subir múltiples archivos

3. **Haz clic en "Procesar Facturas"**
   - Verás el progreso en tiempo real
   - Cada archivo se procesa individualmente

4. **Revisa los resultados**
   - Tabla interactiva con todos los datos
   - Estadísticas automáticas
   - Vista previa por archivo

5. **Descarga el Excel**
   - Botón "Descargar Excel"
   - Archivo con timestamp
   - Listo para usar

## ✨ Características Principales

### Vista Previa en Tiempo Real
- Verás cada archivo conforme se procesa
- Expandir/contraer resultados por archivo
- Tabla interactiva con todos los datos

### Estadísticas Automáticas
- **Total Ítems**: Cantidad total extraída
- **Total Facturas**: Archivos procesados
- **Total $**: Suma de todos los subtotales
- **Promedio**: Ítems por factura

### Descarga Inmediata
- Excel formateado automáticamente
- Columnas ajustadas
- Nombre con fecha y hora
- Un clic para descargar

## 🎯 Ejemplo de Uso

### Caso 1: Una Factura
1. Selecciona "Archivo único"
2. Arrastra tu factura
3. Click en "Procesar"
4. Descarga el Excel

**Tiempo estimado**: 10-15 segundos

### Caso 2: Múltiples Facturas
1. Selecciona "Múltiples archivos"
2. Arrastra todas las facturas (hasta 10 recomendado)
3. Click en "Procesar"
4. Revisa los resultados por archivo
5. Descarga el Excel consolidado

**Tiempo estimado**: 15-30 segundos por archivo

## 🔧 Panel Lateral (Sidebar)

### Información del Sistema
- Modelos activos (Azure y Gemini)
- Estado del servicio
- Formatos soportados

### Configuración
- Mostrar/ocultar detalles técnicos
- Endpoint de Azure
- Información de credenciales (oculta)

## 💡 Consejos

### Para Mejores Resultados:
1. **Imágenes claras**: Buena iluminación, enfoque nítido
2. **PDFs de calidad**: Evitar escaneos borrosos
3. **Orientación correcta**: Facturas en posición vertical
4. **Texto legible**: Evitar facturas con texto muy pequeño

### Límites Recomendados:
- **Archivos simultáneos**: Máximo 10
- **Tamaño de archivo**: Hasta 10 MB por archivo
- **Formato preferido**: JPG o PNG para imágenes

## ⚡ Solución Rápida de Problemas

### La app no se abre:
```bash
# Reinstalar dependencias
pip install -r requirements.txt

# Verificar configuración
python config.py
```

### Puerto ocupado:
```bash
# Usar otro puerto
streamlit run app.py --server.port 8502
```

### Error de credenciales:
- Verifica que `.env` exista
- Confirma que tenga `AZURE_ENDPOINT`, `AZURE_KEY` y `GEMINI_API_KEY`

### Procesamiento lento:
- Conexión a internet lenta
- Archivos muy grandes
- Procesa menos archivos simultáneamente

## 🛑 Detener la Aplicación

- Cierra la ventana del navegador
- En la terminal: `Ctrl + C`
- O simplemente cierra la ventana de terminal

## 📞 Más Información

- **Documentación completa**: Ver `README.md`
- **Seguridad**: Ver `SECURITY.md`
- **Instrucciones detalladas**: Ver `EJECUTAR_APP.md`
- **Logs**: Revisar `logs/processing.log`

---

**¿Listo?** → Doble clic en `iniciar_app.bat` y comienza a extraer datos! 🚀
