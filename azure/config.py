# config.py
# -*- coding: utf-8 -*-
"""
Configuración centralizada del proyecto de extracción de facturas.
Maneja todas las variables de entorno y configuraciones del sistema.
Soporta Streamlit Cloud secrets.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno desde .env (para ejecución local)
load_dotenv()

# Detectar si estamos en Streamlit Cloud
try:
    import streamlit as st
    # Try to access secrets, if it fails, we're not on cloud
    try:
        RUNNING_ON_STREAMLIT_CLOUD = hasattr(st, 'secrets') and len(st.secrets) > 0
    except Exception:
        # Si no hay secrets.toml, no estamos en cloud
        RUNNING_ON_STREAMLIT_CLOUD = False
except ImportError:
    RUNNING_ON_STREAMLIT_CLOUD = False

# =========================
# VALIDACIÓN DE ENTORNO
# =========================
class ConfigurationError(Exception):
    """Excepción para errores de configuración."""
    pass


def _get_required_env(var_name: str) -> str:
    """
    Obtiene una variable de entorno requerida.
    Soporta tanto .env como Streamlit secrets.
    Lanza ConfigurationError si no existe.
    """
    # Primero intentar Streamlit secrets (si está disponible)
    if RUNNING_ON_STREAMLIT_CLOUD:
        try:
            import streamlit as st
            if var_name in st.secrets:
                return str(st.secrets[var_name])
        except Exception:
            pass

    # Fallback a variables de entorno
    value = os.getenv(var_name)
    if not value:
        raise ConfigurationError(
            f"Variable de entorno requerida no encontrada: {var_name}\n"
            f"Por favor, configúrala en el archivo .env o en Streamlit Cloud secrets"
        )
    return value


def _get_optional_env(var_name: str, default: str = "") -> str:
    """
    Obtiene una variable de entorno opcional con valor por defecto.
    Soporta tanto .env como Streamlit secrets.
    """
    # Primero intentar Streamlit secrets (si está disponible)
    if RUNNING_ON_STREAMLIT_CLOUD:
        try:
            import streamlit as st
            if var_name in st.secrets:
                return str(st.secrets[var_name])
        except Exception:
            pass

    # Fallback a variables de entorno
    return os.getenv(var_name, default)


# =========================
# AZURE DOCUMENT INTELLIGENCE
# =========================
AZURE_ENDPOINT = _get_required_env("AZURE_ENDPOINT")
AZURE_KEY = _get_required_env("AZURE_KEY")
SKIP_AZURE = _get_optional_env("SKIP_AZURE", "0").lower() in ("1", "true", "t", "yes", "y")

# =========================
# GEMINI (Google AI)
# =========================
GEMINI_API_KEY = _get_required_env("GEMINI_API_KEY")
GEMINI_MODEL = _get_optional_env("GEMINI_MODEL", "gemini-2.5-pro")
GEMINI_TEMPERATURE = float(_get_optional_env("GEMINI_TEMPERATURE", "0.1"))
GEMINI_MAX_TOKENS = int(_get_optional_env("GEMINI_MAX_TOKENS", "4096"))

# =========================
# GOOGLE DRIVE
# =========================
DRIVE_FOLDER_ID = _get_optional_env("FOLDER_ID", "1Zax30lsPpeMiHby58RmV_iCT80M0lHPQ")
DRIVE_CREDENTIALS_FILE = Path(_get_optional_env(
    "DRIVE_CREDENTIALS_FILE",
    "credentials/credentials.json"
))
DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# =========================
# PROCESAMIENTO
# =========================
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'application/pdf'}
MAX_ITEMS_DISPLAY = int(_get_optional_env("MAX_ITEMS_DISPLAY", "50"))
SLEEP_BETWEEN_FILES = float(_get_optional_env("SLEEP_BETWEEN_FILES", "0.4"))

# Tolerancia para validación de cálculos (Cantidad * Precio ≈ Subtotal)
CALCULATION_TOLERANCE = float(_get_optional_env("CALCULATION_TOLERANCE", "0.01"))

# =========================
# OUTPUTS
# =========================
OUTPUT_FILE = Path(_get_optional_env("OUTPUT_FILE", "items.xlsx"))
LOG_FILE = Path(_get_optional_env("LOG_FILE", "logs/processing.log"))

# Crear directorio de logs si no existe
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# =========================
# PATHS DEL PROYECTO
# =========================
PROJECT_ROOT = Path(__file__).parent.resolve()
PROVEEDORES_DIR = PROJECT_ROOT / "proveedores"

# Agregar al path si es necesario
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# =========================
# VALIDACIÓN DE ARCHIVOS REQUERIDOS
# =========================
def validate_setup() -> None:
    """
    Valida que todos los archivos y configuraciones requeridas existan.
    Lanza ConfigurationError si algo falta.
    """
    errors = []

    # Validar credenciales de Drive
    if not DRIVE_CREDENTIALS_FILE.exists():
        errors.append(
            f"Archivo de credenciales de Google Drive no encontrado: {DRIVE_CREDENTIALS_FILE}\n"
            f"Descarga las credenciales desde Google Cloud Console."
        )

    # Validar directorio de proveedores
    if not PROVEEDORES_DIR.exists():
        errors.append(
            f"Directorio de proveedores no encontrado: {PROVEEDORES_DIR}\n"
            f"Crea el directorio 'proveedores/' en la raíz del proyecto."
        )

    if errors:
        raise ConfigurationError("\n\n".join(errors))

# =========================
# LOGGING CONFIGURATION
# =========================
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': str(LOG_FILE),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8'
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'file']
    }
}


# =========================
# INFORMACIÓN DEL SISTEMA
# =========================
def print_config_summary() -> None:
    """Imprime un resumen de la configuración actual (sin mostrar claves)."""
    print("=" * 60)
    print("CONFIGURACIÓN DEL SISTEMA")
    print("=" * 60)
    print(f"Azure Endpoint: {AZURE_ENDPOINT}")
    print(f"Azure Key: {'*' * 40} (oculta)")
    print(f"Skip Azure: {SKIP_AZURE}")
    print(f"Gemini Model: {GEMINI_MODEL}")
    print(f"Gemini API Key: {'*' * 30} (oculta)")
    print(f"Drive Folder ID: {DRIVE_FOLDER_ID}")
    print(f"Drive Credentials: {DRIVE_CREDENTIALS_FILE}")
    print(f"Output File: {OUTPUT_FILE}")
    print(f"Log File: {LOG_FILE}")
    print(f"Proveedores Dir: {PROVEEDORES_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    # Test de configuración
    try:
        validate_setup()
        print_config_summary()
        print("\n[OK] Configuracion valida!")
    except ConfigurationError as e:
        print(f"\n[ERROR] Error de configuracion:\n{e}")
        sys.exit(1)
