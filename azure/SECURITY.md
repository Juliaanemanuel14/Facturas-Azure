# ⚠️ ACCIÓN INMEDIATA REQUERIDA - SEGURIDAD

## 🔴 CRÍTICO: Credenciales Expuestas

Se detectaron **API keys y credenciales hardcodeadas** en el código del proyecto. Esto es un **riesgo de seguridad CRÍTICO**.

### Credenciales que deben ser rotadas INMEDIATAMENTE:

#### 1. Azure Document Intelligence
- **Archivo afectado**: `test.py`, `analyze_invoice.py`
- **Acción requerida**:
  1. Ve a [Azure Portal](https://portal.azure.com/)
  2. Navega a tu recurso "gestiontrenesng"
  3. En "Keys and Endpoint", regenera las claves
  4. Actualiza el archivo `.env` con la nueva clave

#### 2. Google Gemini API
- **Archivos afectados**: `connect_gemini.py`
- **Acción requerida**:
  1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
  2. Revoca la API key expuesta
  3. Genera una nueva API key
  4. Actualiza el archivo `.env` con la nueva clave

#### 3. Archivo .env
- **Estado**: Contiene credenciales sensibles
- **Acción requerida**:
  1. Verifica que `.env` está en `.gitignore` ✅ (ya implementado)
  2. NUNCA commitees este archivo

## 🔍 Verificación del Historial de Git

Si ya commiteaste credenciales al repositorio, ejecuta:

```bash
# Ver historial de commits
git log --all --full-history --oneline

# Buscar archivos que contengan claves (reemplaza TU_CLAVE con la clave a buscar)
git grep -i "TU_CLAVE_EXPUESTA_AQUI" $(git rev-list --all)
```

Si encuentras las credenciales en el historial:

### Opción 1: Repositorio Privado (Recomendado)
1. Rota todas las credenciales inmediatamente
2. Haz un commit con el código limpio
3. Considera usar `git filter-branch` o BFG Repo-Cleaner para limpiar el historial

### Opción 2: Repositorio Público (URGENTE)
1. **ROTA TODAS LAS CREDENCIALES AHORA**
2. Considera eliminar el repositorio y crear uno nuevo
3. Usa `git filter-branch` o BFG Repo-Cleaner para limpiar el historial
4. Fuerza un push limpio

## ✅ Checklist de Seguridad

Antes de continuar, verifica que:

- [ ] He rotado la clave de Azure Document Intelligence
- [ ] He rotado la API key de Google Gemini
- [ ] El archivo `.env` contiene las nuevas credenciales
- [ ] `.env` está en `.gitignore`
- [ ] He verificado que no hay credenciales en el historial de git
- [ ] He eliminado las credenciales hardcodeadas de todos los archivos `.py`
- [ ] He actualizado `credentials/credentials.json` si corresponde

## 🛡️ Mejores Prácticas Implementadas

El proyecto ahora usa:

1. **Variables de entorno** (`.env`) para todas las credenciales
2. **`.gitignore`** configurado para proteger archivos sensibles
3. **Configuración centralizada** (`config.py`) que valida credenciales
4. **Logging seguro** que no expone claves en logs

## 📝 Próximos Pasos

1. **ROTAR CREDENCIALES** (si no lo has hecho)
2. Copiar `.env.example` a `.env`:
   ```bash
   cp .env.example .env
   ```
3. Completar `.env` con las **nuevas** credenciales
4. Ejecutar validación:
   ```bash
   python config.py
   ```
5. Verificar que todo funciona:
   ```bash
   python test.py ruta/a/factura.jpg
   ```

## 🚨 En caso de incidente de seguridad

Si sospechas que las credenciales fueron comprometidas:

1. **Rota inmediatamente** todas las claves
2. Revisa los logs de Azure/Google para actividad sospechosa
3. Habilita alertas de seguridad en Azure Portal
4. Considera implementar Azure Key Vault o Google Secret Manager para el futuro

## 📞 Contacto

Para dudas sobre seguridad, contacta al equipo de desarrollo.

---

**Fecha de creación**: Noviembre 2024
**Estado**: ⚠️ REQUIERE ACCIÓN INMEDIATA
