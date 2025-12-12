# 🧹 Limpiar Repositorio de Credenciales

GitHub detectó credenciales en tu historial de git. Aquí está cómo solucionarlo:

## ⚠️ PASO CRÍTICO: Rotar Credenciales PRIMERO

Antes de continuar, **DEBES** rotar tus credenciales porque ya están en GitHub:

### 1. Azure Document Intelligence
1. Ve a [Azure Portal](https://portal.azure.com)
2. Busca tu recurso "gestiontrenesng"
3. Ve a "Keys and Endpoint"
4. Click en "Regenerate Key 1" o "Regenerate Key 2"
5. **Copia la nueva clave**

### 2. Google Gemini API
1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Encuentra tu clave actual
3. Click en "Delete" o "Revoke"
4. Click en "Create API Key"
5. **Copia la nueva clave**

### 3. Actualizar tu .env local
Actualiza el archivo `.env` con las NUEVAS credenciales.

## 🔄 Opción 1: Rehacer el Repositorio (Recomendado)

Esta es la forma más segura:

```bash
# 1. Ir a la carpeta del proyecto
cd "c:/Users/gesti/GESTION COMPARTIDA Dropbox/Departamento Gestion/0001 - Control de Gestion (1)/Desarrollo/azure"

# 2. Eliminar el repositorio git actual
rm -rf .git

# 3. Inicializar nuevo repositorio
git init

# 4. Agregar solo archivos seguros (el .gitignore ya está configurado)
git add .

# 5. Crear commit inicial limpio
git commit -m "Initial commit: Extractor de facturas con Streamlit"

# 6. Forzar push al repositorio remoto (reemplaza el historial)
git branch -M main
git remote add origin https://github.com/Juliaanemanuel14/Facturas-Azure.git
git push -u --force origin main
```

⚠️ **ADVERTENCIA**: `--force` reemplazará TODO el historial del repositorio remoto.

## 🔄 Opción 2: Usar BFG Repo-Cleaner (Alternativa)

Si prefieres limpiar el historial sin rehacerlo:

1. Descarga [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
2. Ejecuta:
```bash
java -jar bfg.jar --delete-files credentials.json
java -jar bfg.jar --delete-files .env
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

## ✅ Después de Limpiar

1. Verifica que el push funcione:
```bash
git push origin main
```

2. Si GitHub sigue bloqueando, ve a:
   - https://github.com/Juliaanemanuel14/Facturas-Azure/settings/security_analysis
   - Revisa las alertas y márcalas como resueltas

3. Continúa con el deployment en Streamlit Cloud

## 🎯 Resumen

1. ✅ Rotar Azure Key
2. ✅ Rotar Gemini API Key
3. ✅ Actualizar .env local
4. ✅ Limpiar repositorio (Opción 1 o 2)
5. ✅ Push exitoso
6. ✅ Deploy en Streamlit Cloud

---

**Nota**: Esta es una situación común. Lo importante es que rotaste las credenciales comprometidas.
