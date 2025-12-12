# 🚀 Guía de Deployment en Streamlit Cloud

Esta guía te ayudará a subir tu aplicación a Streamlit Community Cloud para que esté disponible online 24/7.

## 📋 Requisitos Previos

1. **Cuenta de GitHub** (gratuita)
2. **Cuenta de Streamlit** (gratuita) - Regístrate en [share.streamlit.io](https://share.streamlit.io)
3. **Tus credenciales** de Azure y Gemini

## 🔧 Paso 1: Preparar el Repositorio

### 1.1 Crear Repositorio en GitHub

1. Ve a [github.com](https://github.com) y haz login
2. Click en "New repository" (botón verde)
3. Nombre sugerido: `extractor-facturas`
4. Descripción: `Sistema de extracción de datos de facturas con AI`
5. Selecciona: **Private** (para proteger tus datos)
6. **NO marques** "Add a README" ni ".gitignore" (ya los tenemos)
7. Click en "Create repository"

### 1.2 Subir el Código

Desde tu terminal/PowerShell en la carpeta del proyecto:

```bash
# Inicializar git (si no está inicializado)
git init

# Agregar todos los archivos
git add .

# Crear el primer commit
git commit -m "Initial commit: Extractor de facturas con Streamlit"

# Conectar con tu repositorio de GitHub
# Reemplaza 'TU-USUARIO' con tu usuario de GitHub
git remote add origin https://github.com/TU-USUARIO/extractor-facturas.git

# Subir el código
git branch -M main
git push -u origin main
```

**⚠️ IMPORTANTE**: Verifica que `.env` NO se haya subido:
```bash
git status
# No debe aparecer .env en la lista
```

## 🌐 Paso 2: Crear Aplicación en Streamlit Cloud

### 2.1 Conectar GitHub

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Click en "Sign in" y usa tu cuenta de GitHub
3. Autoriza a Streamlit a acceder a tus repositorios

### 2.2 Crear Nueva App

1. Click en "New app"
2. Selecciona:
   - **Repository**: `extractor-facturas` (o el nombre que usaste)
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**: Puedes personalizarla (ej: `extractor-facturas-tuempresa`)

3. **NO hagas click en "Deploy" todavía**

## 🔐 Paso 3: Configurar Secrets (MUY IMPORTANTE)

Antes de desplegar, necesitas configurar tus credenciales de forma segura.

### 3.1 En Streamlit Cloud

1. En la página de configuración de tu app, busca "Advanced settings"
2. Click en "Secrets"
3. Copia y pega el siguiente contenido, **reemplazando con tus valores reales**:

```toml
# Azure Document Intelligence
AZURE_ENDPOINT = "https://gestiontrenesng.cognitiveservices.azure.com/"
AZURE_KEY = "TU_CLAVE_AZURE_AQUI"

# Google Gemini AI
GEMINI_API_KEY = "TU_API_KEY_GEMINI_AQUI"
GEMINI_MODEL = "gemini-2.0-flash"

# Opcional: Google Drive (solo si usas analyze_invoice.py)
FOLDER_ID = "1Zax30lsPpeMiHby58RmV_iCT80M0lHPQ"
DRIVE_CREDENTIALS_FILE = "credentials/credentials.json"
```

4. Click en "Save"

### 3.2 Obtener tus Credenciales

**Azure Key:**
- Ve a [Azure Portal](https://portal.azure.com)
- Busca tu recurso "gestiontrenesng"
- En el menú izquierdo: "Keys and Endpoint"
- Copia "KEY 1" o "KEY 2"

**Gemini API Key:**
- Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
- Click en "Create API Key"
- Copia la clave generada

## 🚀 Paso 4: Desplegar

1. Ahora sí, click en **"Deploy"**
2. Espera 2-5 minutos mientras se instalan las dependencias
3. La aplicación se desplegará automáticamente

### Seguir el Progreso

Verás un log en tiempo real mostrando:
```
[00:00:10] Installing dependencies...
[00:01:30] Starting up...
[00:02:00] App is running!
```

## ✅ Paso 5: Verificar y Compartir

### 5.1 Verificar

1. Una vez desplegada, se abrirá automáticamente tu app
2. URL será algo como: `https://extractor-facturas.streamlit.app`
3. Prueba subiendo una factura de prueba
4. Verifica que el procesamiento funcione correctamente

### 5.2 Compartir

Ahora puedes compartir la URL con:
- Tu equipo
- Clientes
- Colaboradores

**Nota**: Todos podrán usar la aplicación sin instalar nada.

## 🔧 Administración

### Ver Logs

1. En [share.streamlit.io](https://share.streamlit.io)
2. Click en tu aplicación
3. Click en "Manage app"
4. Click en "Logs" para ver errores o actividad

### Actualizar la Aplicación

Cuando hagas cambios en tu código:

```bash
# Hacer cambios en los archivos
# ...

# Guardar cambios
git add .
git commit -m "Descripción de tus cambios"
git push

# Streamlit detectará los cambios automáticamente
# y redesplegará en 1-2 minutos
```

### Actualizar Secrets

1. En "Manage app"
2. Click en "Settings" → "Secrets"
3. Edita los valores
4. Click en "Save"
5. La app se reiniciará automáticamente

## ⚡ Solución de Problemas

### Error: "Module not found"

Verifica que `requirements.txt` esté actualizado:
```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements"
git push
```

### Error: "Missing secrets"

1. Verifica que configuraste los secrets correctamente
2. Los nombres deben coincidir exactamente (case-sensitive)
3. No debe haber espacios extra en los nombres

### La app está lenta

- Streamlit Cloud tiene límites de recursos
- Considera:
  - Procesar menos archivos simultáneamente
  - Optimizar el código
  - Usar caché de Streamlit (`@st.cache_data`)

### Error: "Authentication failed"

- Verifica que las credenciales de Azure y Gemini sean correctas
- Asegúrate de que las claves no hayan expirado
- Revisa que el endpoint de Azure sea correcto

## 📊 Límites de Streamlit Community Cloud

### Plan Gratuito:
- ✅ 1 app privada o ilimitadas públicas
- ✅ 1 GB de RAM
- ✅ 1 CPU
- ✅ Almacenamiento limitado
- ✅ Sin límite de usuarios

### Si necesitas más:
- Considera [Streamlit Cloud Teams](https://streamlit.io/cloud) (de pago)
- O despliega en tu propio servidor

## 🎉 ¡Listo!

Tu aplicación está ahora disponible online 24/7 en:
```
https://tu-app.streamlit.app
```

## 📞 Soporte

- **Documentación oficial**: [docs.streamlit.io/streamlit-community-cloud](https://docs.streamlit.io/streamlit-community-cloud)
- **Foro de Streamlit**: [discuss.streamlit.io](https://discuss.streamlit.io)
- **Issues de GitHub**: En tu repositorio

---

**¡Éxito con tu deployment!** 🚀
