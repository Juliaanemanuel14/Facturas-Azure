@echo off
:: Script para iniciar la aplicacion web de extraccion de facturas
:: Doble clic para ejecutar

echo ========================================
echo   EXTRACTOR DE FACTURAS - INTERFACE WEB
echo ========================================
echo.

cd /d "%~dp0"

echo Verificando entorno...
echo.

:: Verificar que existe .env
if not exist ".env" (
    echo [ERROR] Archivo .env no encontrado
    echo Por favor, crea el archivo .env con tus credenciales
    echo.
    pause
    exit /b 1
)

echo [OK] Archivo .env encontrado
echo.

echo Iniciando aplicacion web...
echo La aplicacion se abrira automaticamente en tu navegador
echo En: http://localhost:8501
echo.
echo Para detener la aplicacion, cierra esta ventana o presiona Ctrl+C
echo.
echo ========================================
echo.

streamlit run app.py

pause
