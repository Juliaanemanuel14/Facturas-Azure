# test.py
# -*- coding: utf-8 -*-
"""
Prueba simple: extraer items (Codigo, Descripcion, Cantidad, PrecioUnitario, Subtotal)
desde UNA imagen/PDF usando Azure Document Intelligence (prebuilt-invoice).

Uso:
    1. Configura las variables de entorno en .env
    2. Especifica FILE_PATH como argumento o usa la variable de entorno TEST_FILE_PATH
    3. Ejecuta: python test.py [ruta_al_archivo]
"""

import os
import sys
from typing import Any, Dict, List, Optional
from decimal import Decimal
from pathlib import Path
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Importar configuración centralizada
import config.config as cfg
import config.logger as logging_module

AZURE_ENDPOINT = cfg.AZURE_ENDPOINT
AZURE_KEY = cfg.AZURE_KEY
get_logger = logging_module.get_logger

# Configurar logger
logger = get_logger(__name__)

# ======== CONFIGURACIÓN ========
ENDPOINT = AZURE_ENDPOINT
KEY = AZURE_KEY

# FILE_PATH puede venir de:
# 1. Argumento de línea de comandos
# 2. Variable de entorno TEST_FILE_PATH
# 3. Valor por defecto (None - se pedirá al usuario)
FILE_PATH = (
    sys.argv[1] if len(sys.argv) > 1
    else os.getenv("TEST_FILE_PATH")
)
# =================================

def _unwrap_azure_num(x: Any) -> Optional[float]:
    """
    Convierte valores numéricos de Azure a float:
      - CurrencyValue (tiene .amount) -> float(amount)
      - int/float/Decimal -> float
      - str -> intenta float (sin normalizar)
    """
    if x is None:
        return None
    amt = getattr(x, "amount", None)
    if amt is not None:
        try:
            return float(amt)
        except Exception:
            return None
    if isinstance(x, (int, float, Decimal)):
        try:
            return float(x)
        except Exception:
            return None
    if isinstance(x, str):
        try:
            return float(x)
        except Exception:
            return None
    return None

def extract_items_from_file(path: str) -> List[Dict]:
    client = DocumentAnalysisClient(endpoint=ENDPOINT, credential=AzureKeyCredential(KEY))
    with open(path, "rb") as f:
        content = f.read()

    poller = client.begin_analyze_document(model_id="prebuilt-invoice", document=content)
    result = poller.result()

    items: List[Dict] = []
    for doc in result.documents:
        items_field = doc.fields.get("Items")
        if not items_field or not items_field.value:
            continue

        for it in items_field.value:
            flds = it.value or {}
            def v(name: str):
                fld = flds.get(name)
                return getattr(fld, "value", None) if fld else None

            qty        = _unwrap_azure_num(v("Quantity"))
            unit_price = _unwrap_azure_num(v("UnitPrice"))
            amount     = _unwrap_azure_num(v("Amount"))
            subtotal   = amount if amount is not None else (qty * unit_price if (qty is not None and unit_price is not None) else None)

            items.append({
                "Codigo":        v("ProductCode"),
                "Descripcion":   v("Description"),
                "Cantidad":      qty,
                "PrecioUnitario":unit_price,
                "Subtotal":      subtotal,
            })
    return items

def main():
    if not FILE_PATH:
        logger.error("No se especificó archivo de entrada.")
        print("\nUso: python test.py <ruta_al_archivo>")
        print("  O configura TEST_FILE_PATH en .env")
        sys.exit(1)

    file_path = Path(FILE_PATH)
    if not file_path.exists():
        logger.error(f"Archivo no encontrado: {file_path}")
        sys.exit(1)

    logger.info(f"Procesando archivo: {file_path}")

    try:
        rows = extract_items_from_file(str(file_path))
        if not rows:
            logger.warning("Sin ítems detectados.")
            return

        # Print prolijo
        logger.info(f"Items detectados: {len(rows)}\n")
        for i, r in enumerate(rows, 1):
            print(f"{i:02d}. Codigo={r['Codigo']!r} | Desc={r['Descripcion']!r} | "
                  f"Qty={r['Cantidad']} | Unit={r['PrecioUnitario']} | Subtotal={r['Subtotal']}")
    except Exception as e:
        logger.error(f"Error procesando archivo: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
