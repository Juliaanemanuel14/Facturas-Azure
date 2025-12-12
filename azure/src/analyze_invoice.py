# analyze_drive_invoices.py
# -*- coding: utf-8 -*-
import io
import re
import os
import sys
import json
import math
import time
import pkgutil
import importlib
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Callable
from decimal import Decimal, InvalidOperation

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# === Gemini (tu conector) ===
from src.connect_gemini import model

# === Configuración centralizada ===
import config.config as cfg
import config.logger as logging_module

# Extraer configuraciones
AZURE_ENDPOINT = cfg.AZURE_ENDPOINT
AZURE_KEY = cfg.AZURE_KEY
SKIP_AZURE = cfg.SKIP_AZURE
DRIVE_FOLDER_ID = cfg.DRIVE_FOLDER_ID
DRIVE_CREDENTIALS_FILE = cfg.DRIVE_CREDENTIALS_FILE
DRIVE_SCOPES = cfg.DRIVE_SCOPES
ALLOWED_MIME_TYPES = cfg.ALLOWED_MIME_TYPES
MAX_ITEMS_DISPLAY = cfg.MAX_ITEMS_DISPLAY
SLEEP_BETWEEN_FILES = cfg.SLEEP_BETWEEN_FILES
CALCULATION_TOLERANCE = cfg.CALCULATION_TOLERANCE
OUTPUT_FILE = cfg.OUTPUT_FILE
GEMINI_TEMPERATURE = cfg.GEMINI_TEMPERATURE
GEMINI_MAX_TOKENS = cfg.GEMINI_MAX_TOKENS
validate_setup = cfg.validate_setup

# Extraer funciones de logging
get_logger = logging_module.get_logger
log_items_summary = logging_module.log_items_summary
log_processing_start = logging_module.log_processing_start
log_processing_complete = logging_module.log_processing_complete
log_error = logging_module.log_error
log_config_warning = logging_module.log_config_warning
log_plugin_loaded = logging_module.log_plugin_loaded

# Configurar logger
logger = get_logger(__name__)

# =========================
# CONFIG (usando variables centralizadas)
# =========================
SERVICE_ACCOUNT_FILE = str(DRIVE_CREDENTIALS_FILE)
SCOPES = DRIVE_SCOPES
FOLDER_ID = DRIVE_FOLDER_ID
ALLOWED_MIME = ALLOWED_MIME_TYPES

ENDPOINT = AZURE_ENDPOINT
KEY = AZURE_KEY

# =========================
# CLIENTES
# =========================
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive = build('drive', 'v3', credentials=creds)

az_client = DocumentAnalysisClient(ENDPOINT, AzureKeyCredential(KEY))

# =========================
# UTILS (delegadas a logger)
# =========================
# Las funciones de logging ahora usan el módulo logger centralizado
_print_items = log_items_summary

# =========================
# HELPERS NUMÉRICOS / TEXTO
# =========================
def _has_digits(s: str) -> bool:
    return any(ch.isdigit() for ch in s)

def _to_float(x):
    """
    Convierte a float si es posible. Acepta:
      - int/float/Decimal
      - numpy numeric
      - str con símbolos ($, espacios, miles . y decimal ,)
    Devuelve float o None. Si no hay dígitos en el string, se considera vacío (None).
    """
    if x is None:
        return None
    if isinstance(x, float):
        return x
    if isinstance(x, int):
        return float(x)
    if isinstance(x, Decimal):
        try:
            return float(x)
        except (ValueError, InvalidOperation):
            return None
    try:
        import numpy as np  # type: ignore
        if isinstance(x, (np.integer, np.floating)):
            return float(x)
    except Exception:
        pass
    if isinstance(x, str):
        s = x.strip()
        if s == "":
            return None
        if not _has_digits(s):
            return None
        s = s.replace("$", "").replace("\u00A0", " ").strip()
        s = re.sub(r"(?<=\d)\.(?=\d{3}\b)", "", s)
        s = s.replace(",", ".")
        s = s.replace(" ", "")
        try:
            return float(s)
        except Exception:
            return None
    return None

def _is_nan(v) -> bool:
    try:
        return isinstance(v, float) and math.isnan(v)
    except Exception:
        return False

def _is_empty_numeric(val) -> bool:
    """
    True solo si realmente está vacío:
      - None o "" → True
      - String SIN dígitos (p.ej. "-", "n/a") → True
      - NaN → True
      - Cualquier valor con dígitos (incluye "0", "0,00", "$ 0") → False si parsea.
    """
    if val is None:
        return True
    if isinstance(val, str):
        if val.strip() == "":
            return True
        if not _has_digits(val):
            return True
    f = _to_float(val)
    if f is None:
        return True
    return _is_nan(f)

def _normalize_desc(desc) -> str:
    if desc is None:
        return ""
    s = str(desc)
    s = s.replace("\r\n", " ").replace("\n", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _unwrap_azure_num(x):
    """
    Devuelve un float a partir de valores de Azure:
    - CurrencyValue (tiene .amount) -> float(amount)
    - int/float/Decimal -> float
    - str -> _to_float(str)
    - otros -> _to_float(x)
    """
    if x is None:
        return None
    amt = getattr(x, "amount", None)
    if amt is not None:
        try:
            return float(amt)
        except Exception:
            pass
    if isinstance(x, (int, float, Decimal)):
        try:
            return float(x)
        except Exception:
            return None
    return _to_float(x)

# =========================
# PROVEEDORES: prompt + transformaciones + condicionales
# =========================
SupplierTransform = Callable[[List[Dict]], List[Dict]]
SupplierShould = Callable[[List[Dict]], Tuple[bool, List[str]]]

def resolve_supplier_plugin(filename: str) -> Tuple[str, Optional[str], Optional[SupplierTransform], Optional[SupplierTransform], Optional[SupplierShould]]:
    proveedores_path = Path("proveedores")
    if not proveedores_path.exists() or not proveedores_path.is_dir():
        return "", None, None, None, None

    parent = str(proveedores_path.parent.resolve())
    if parent not in sys.path:
        sys.path.insert(0, parent)

    # 1) proveedores/archivos.py (opcional)
    try:
        mod_archivos = importlib.import_module("proveedores.archivos")
        if hasattr(mod_archivos, "get_prompt_for_filename"):
            try:
                p = mod_archivos.get_prompt_for_filename(filename)  # type: ignore[attr-defined]
                if p:
                    return (
                        str(p),
                        "proveedores/archivos.py",
                        getattr(mod_archivos, "transform_azure", None),
                        getattr(mod_archivos, "transform_items", None),
                        getattr(mod_archivos, "should_full_handoff_custom", None),
                    )
            except Exception as e:
                print(f"    [proveedores/archivos.py] error en get_prompt_for_filename: {e}")
    except ModuleNotFoundError:
        pass
    except Exception as e:
        print(f"    [proveedores/archivos.py] error importando módulo: {e}")

    # 2) plugins *.py
    try:
        pkg = importlib.import_module("proveedores")
        for _, mod_name, is_pkg in pkgutil.iter_modules(pkg.__path__):  # type: ignore[arg-type]
            if is_pkg or mod_name in ("archivos", "__init__"):
                continue
            try:
                full_name = f"proveedores.{mod_name}"
                mod = importlib.import_module(full_name)
                patterns = getattr(mod, "PATTERNS", None)
                prompt   = getattr(mod, "PROMPT", None)
                if prompt is None:
                    prompt = ""
                if patterns and isinstance(patterns, (list, tuple)):
                    for pat in patterns:
                        try:
                            if isinstance(pat, str):
                                if re.search(pat, filename, flags=re.I):
                                    return (
                                        str(prompt),
                                        f"{full_name}.py",
                                        getattr(mod, "transform_azure", None),
                                        getattr(mod, "transform_items", None),
                                        getattr(mod, "should_full_handoff_custom", None),
                                    )
                            elif hasattr(pat, "search"):
                                if pat.search(filename):
                                    return (
                                        str(prompt),
                                        f"{full_name}.py",
                                        getattr(mod, "transform_azure", None),
                                        getattr(mod, "transform_items", None),
                                        getattr(mod, "should_full_handoff_custom", None),
                                    )
                        except Exception:
                            continue
            except Exception as e:
                print(f"    [proveedores plugin] error importando {mod_name}: {e}")
    except Exception as e:
        print(f"    [proveedores] error escaneando paquete: {e}")

    return "", None, None, None, None

# =========================
# AZURE: analizar bytes (con unwrap de CurrencyValue)
# =========================
def analyze_invoice_bytes(content: bytes) -> List[Dict]:
    """
    Ejecuta Azure Form Recognizer (prebuilt-invoice) y devuelve lista de ítems normalizada.
    Lanza excepción ante cualquier error — el caller (main) maneja fallback a Gemini.
    """
    poller = az_client.begin_analyze_document(
        model_id="prebuilt-invoice",
        document=content
    )
    result = poller.result()

    items_out: List[Dict] = []
    for doc in result.documents:
        items_field = doc.fields.get("Items")
        if not items_field or not items_field.value:
            continue

        for it in items_field.value:
            flds = it.value

            def v(name: str):
                f = flds.get(name)
                return getattr(f, "value", None) if f else None

            qty        = _unwrap_azure_num(v("Quantity"))
            unit_price = _unwrap_azure_num(v("UnitPrice"))
            amount     = _unwrap_azure_num(v("Amount"))

            subtotal = amount if amount is not None else (
                round(qty * unit_price, 2) if (qty is not None and unit_price is not None) else None
            )

            items_out.append({
                "Codigo": v("ProductCode"),
                "Descripcion": v("Description"),
                "Cantidad": qty,
                "PrecioUnitario": unit_price,
                "Subtotal": subtotal,
            })
    return items_out

# =========================
# SANITIZADO POST-AZURE
# =========================
def _sanitize_azure_items(items: List[Dict]) -> List[Dict]:
    out = []
    for it in items:
        desc = _normalize_desc(it.get("Descripcion"))
        qty  = _to_float(it.get("Cantidad"))
        unit = _to_float(it.get("PrecioUnitario"))
        sub  = _to_float(it.get("Subtotal"))

        if (sub is None or _is_nan(sub)) and (qty is not None and not _is_nan(qty)) and (unit is not None and not _is_nan(unit)):
            sub = round(qty * unit, 2)

        out.append({
            "Codigo": it.get("Codigo"),
            "Descripcion": desc,
            "Cantidad": qty,
            "PrecioUnitario": unit,
            "Subtotal": sub,
        })
    return out

# =========================
# FULL-HANDOFF (DEFAULT CORREGIDO)
# =========================
def should_full_handoff_default(items: List[Dict]) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    EPS = CALCULATION_TOLERANCE

    for idx, it in enumerate(items, start=1):
        desc = _normalize_desc(it.get("Descripcion"))
        if desc == "":
            reasons.append(f"Fila {idx}: Descripcion vacía")
            return True, reasons

        qty_raw  = it.get("Cantidad")
        unit_raw = it.get("PrecioUnitario")
        sub_raw  = it.get("Subtotal")

        if _is_empty_numeric(qty_raw) or _is_empty_numeric(unit_raw) or _is_empty_numeric(sub_raw):
            reasons.append(
                f"Fila {idx}: campo numérico vacío/no convertible "
                f"(qty={qty_raw}, unit={unit_raw}, subtotal={sub_raw})"
            )
            return True, reasons

        qty  = _to_float(qty_raw)
        unit = _to_float(unit_raw)
        sub  = _to_float(sub_raw)

        if qty is None or unit is None or sub is None or _is_nan(qty) or _is_nan(unit) or _is_nan(sub):
            reasons.append(
                f"Fila {idx}: campo numérico NaN/no convertible "
                f"(qty={qty_raw}, unit={unit_raw}, subtotal={sub_raw})"
            )
            return True, reasons

        calc = round(unit * qty, 2)
        sub_r = round(sub, 2)
        if abs(calc - sub_r) > EPS:
            reasons.append(
                f"Fila {idx}: unit*qty - subtotal fuera de tolerancia "
                f"({unit}*{qty}={calc} vs {sub_r}, diff={calc - sub_r})"
            )
            return True, reasons

    return False, reasons

# =========================
# GEMINI: parsing robusto
# =========================
EXPECTED_KEYS = {"Codigo","Descripcion","Cantidad","PrecioUnitario","Subtotal"}

def _extract_json_block(text: str) -> str:
    if text is None:
        raise ValueError("Respuesta vacía de Gemini")
    text = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "").strip()
    m = re.search(r"(\{.*\}|\[.*\])", text, flags=re.DOTALL)
    return m.group(1).strip() if m else text.strip()

def _coerce_items_schema(data: Any) -> List[Dict]:
    if isinstance(data, dict):
        if "items" in data and isinstance(data["items"], list):
            data = data["items"]
        elif set(data.keys()) & EXPECTED_KEYS:
            data = [data]
        else:
            raise ValueError("Objeto JSON no contiene 'items' ni tiene forma de ítem.")

    if not isinstance(data, list):
        raise ValueError("La raíz JSON debe ser una lista o un objeto con 'items'.")

    items: List[Dict] = []
    for idx, elem in enumerate(data, start=1):
        if isinstance(elem, str):
            try:
                elem = json.loads(elem)
            except Exception as e:
                raise ValueError(f"Ítem {idx} es string no parseable a JSON: {e}")

        if not isinstance(elem, dict):
            raise ValueError(f"Ítem {idx} no es dict")

        item = {k: elem.get(k, None) for k in EXPECTED_KEYS}
        items.append(item)

    return items

def _call_gemini(prompt: str, image_part: Dict, temperature: Optional[float] = None) -> str:
    if temperature is None:
        temperature = GEMINI_TEMPERATURE

    resp = model.generate_content(
        [prompt, image_part],
        generation_config={
            "temperature": temperature,
            "max_output_tokens": GEMINI_MAX_TOKENS,
            "response_mime_type": "application/json",
        }
    )
    raw = getattr(resp, "text", None)
    if not raw and hasattr(resp, "candidates") and resp.candidates and resp.candidates[0].content.parts:
        raw = resp.candidates[0].content.parts[0].text
    if not raw:
        raise ValueError("Gemini devolvió respuesta vacía.")
    return raw

def gemini_full_extract_items(image_bytes: bytes, mime_type: str, extra_prompt: str = "") -> List[Dict]:
    image_part = {"mime_type": mime_type, "data": image_bytes}

    prompt_base = (
        "Sos un extractor de ítems de una factura. Recibís una imagen/PDF de factura.\n"
        "Devolvés SOLO un JSON (sin texto adicional) con una **lista** de objetos con estas claves EXACTAS:\n"
        '["Codigo","Descripcion","Cantidad","PrecioUnitario","Subtotal"]\n'
        "Reglas:\n"
        "- No inventes líneas; solo las presentes en la factura.\n"
        "- Para cada ítem: Subtotal = Cantidad * PrecioUnitario (redondeo 2 decimales).\n"
        "- Si algún dato no se puede leer con certeza, devolvelo como null.\n"
        "- Campos numéricos como números (no strings).\n"
        "- La raíz del JSON debe ser SIEMPRE un array. No envuelvas en objetos.\n"
        "- Mantener el orden natural de lectura."
    )

    if extra_prompt:
        prompt_base += "\n\n**Contexto específico del proveedor:**\n" + extra_prompt

    # Intento 1
    raw1 = _call_gemini(prompt_base, image_part, temperature=0.1)
    logger.debug(f"[Gemini RAW len={len(raw1)}] {raw1[:300].replace(chr(10),' ')}{'...' if len(raw1)>300 else ''}")
    try:
        js1 = _extract_json_block(raw1)
        data1 = json.loads(js1)
        items1 = _coerce_items_schema(data1)
        return items1
    except Exception as e1:
        logger.debug(f"[Gemini parse] intento 1 falló: {e1}")

    # Intento 2 (más estricto)
    prompt_retry = prompt_base + "\n\nIMPORTANTE: si no podés devolver un ARRAY JSON de ítems con esas claves, devolvé `[]`."
    raw2 = _call_gemini(prompt_retry, image_part, temperature=0.0)
    logger.debug(f"[Gemini RAW(retry) len={len(raw2)}] {raw2[:300].replace(chr(10),' ')}{'...' if len(raw2)>300 else ''}")
    js2 = _extract_json_block(raw2)
    data2 = json.loads(js2)
    items2 = _coerce_items_schema(data2)
    return items2

# =========================
# DRIVE: listar y descargar
# =========================
def list_folder_files(folder_id: str):
    q = f"'{folder_id}' in parents and trashed=false"
    page_token = None
    while True:
        resp = drive.files().list(
            q=q,
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=page_token
        ).execute()
        for f in resp.get('files', []):
            yield f
        page_token = resp.get('nextPageToken')
        if not page_token:
            break

def download_file_bytes(file_id: str) -> bytes:
    req = drive.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, req)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return fh.getvalue()

# =========================
# MAIN
# =========================
def main():
    # Validar configuración antes de empezar
    try:
        validate_setup()
    except Exception as e:
        logger.error(f"Error de configuración: {e}")
        sys.exit(1)

    logger.info("=== Iniciando procesamiento de facturas ===")
    if SKIP_AZURE:
        log_config_warning(logger, "Azure Document Intelligence desactivado (SKIP_AZURE=1)")

    rows_items: List[Dict] = []
    rows_summary: List[Dict] = []

    files = list(list_folder_files(FOLDER_ID))
    total_files = len(files)
    logger.info(f"Encontrados {total_files} archivos en la carpeta Drive")

    for i, f in enumerate(files, 1):
        name = f["name"]
        mime = f["mimeType"]
        fid  = f["id"]

        if mime not in ALLOWED_MIME:
            logger.info(f"[{i}/{total_files}] Omitido (mime no soportado): {name} ({mime})")
            continue

        try:
            content = download_file_bytes(fid)

            log_processing_start(logger, f"{name} ({mime})", i, total_files)

            # ----------------------------------------
            # 1) Azure (con fallback a Gemini si falla o si SKIP_AZURE=1)
            # ----------------------------------------
            items_azure: List[Dict] = []
            items_final: List[Dict] = []
            used_gemini = False
            used_transform = False
            used_transform_azure = False
            issues: List[str] = []
            azure_error: Optional[str] = None

            if SKIP_AZURE:
                azure_error = "Azure desactivado (SKIP_AZURE=1)"
                logger.warning(f"  ⚠ {azure_error}")
            else:
                try:
                    items_azure = analyze_invoice_bytes(content)
                    items_azure = _sanitize_azure_items(items_azure)
                    logger.info("  ▶ Azure:")
                    _print_items(logger, "Azure ítems", items_azure, max_items=MAX_ITEMS_DISPLAY)
                except Exception as az_e:
                    azure_error = f"{type(az_e).__name__}: {az_e}"
                    logger.error(f"  ✖ Azure falló: {azure_error}")
                    issues.append(f"Azure error: {azure_error}")

            # Resolver plugin
            extra_prompt, plugin_src, transform_azure_fn, transform_items_fn, should_fn = resolve_supplier_plugin(name)
            if plugin_src:
                log_plugin_loaded(logger, plugin_src, name)
                if extra_prompt:
                    logger.info("     ↳ Prompt proveedor aplicado.")

            # 1.b) Transformación específica sobre Azure
            if items_azure and transform_azure_fn:
                try:
                    items_azure_tx = transform_azure_fn(items_azure)
                    if isinstance(items_azure_tx, list):
                        items_azure = items_azure_tx
                        used_transform_azure = True
                        logger.info("  🔧 Transform AZURE proveedor aplicada:")
                        _print_items(logger, "Azure ítems transformados", items_azure, max_items=MAX_ITEMS_DISPLAY)
                    else:
                        logger.warning("  ⚠ transform_azure no devolvió lista; se ignora.")
                except Exception as e:
                    logger.error(f"  ✖ Error en transform_azure: {e}")
                    issues.append(f"transform_azure error: {e}")

            # 2) Decidir si FULL handoff a Gemini
            do_full = False
            reasons: List[str] = []

            if azure_error:
                do_full = True
                reasons.append("Azure falló / desactivado → forzar Gemini FULL")
            elif not items_azure:
                do_full = True
                reasons.append("Azure sin ítems → Gemini FULL")
            else:
                try:
                    if should_fn:
                        do_full, reasons = should_fn(items_azure)
                    else:
                        do_full, reasons = should_full_handoff_default(items_azure)
                except Exception as e:
                    logger.error(f"  ✖ should_full_handoff falló: {e}")
                    issues.append(f"should_full_handoff error: {e}")
                    do_full, reasons = False, []

            for r in reasons:
                logger.warning(f"  ⚠ Disparador FULL: {r}")

            # 3) Ejecutar Gemini si corresponde
            if do_full:
                try:
                    items_final = gemini_full_extract_items(content, mime, extra_prompt=extra_prompt)
                    used_gemini = True
                    logger.info("  ▶ Gemini FULL:")
                    _print_items(logger, "Gemini ítems", items_final, max_items=MAX_ITEMS_DISPLAY)

                    # 4) Transformación post-Gemini (si existe)
                    if transform_items_fn:
                        try:
                            items_tx = transform_items_fn(items_final)
                            if isinstance(items_tx, list):
                                items_final = items_tx
                                used_transform = True
                                logger.info("  🔧 Transform proveedor aplicada (post-Gemini):")
                                _print_items(logger, "Ítems transformados", items_final, max_items=MAX_ITEMS_DISPLAY)
                            else:
                                logger.warning("  ⚠ transform_items no devolvió lista; se ignora.")
                        except Exception as e:
                            logger.error(f"  ✖ Error en transform_items: {e}")
                            issues.append(f"transform_items error: {e}")
                except Exception as e:
                    issues.append(f"Error Gemini Full: {e}")
                    logger.error(f"  ✖ Error Gemini Full: {e}")
                    items_final = items_azure
                    if not items_final:
                        logger.warning("  ↩ Sin ítems utilizables tras fallo de Gemini y Azure.")
            else:
                items_final = items_azure
                logger.info("  ✓ No se requiere FULL. Se mantienen ítems de Azure (con transform_azure si aplicó).")

            # DF de ítems (finales)
            for it in items_final:
                rows_items.append({"Archivo": name, "FileId": fid, **it})

            # Resumen
            n_items = len(items_final)
            rows_summary.append({
                "Archivo": name,
                "FileId": fid,
                "MimeType": mime,
                "ItemsDetectados": n_items,
                "UsoGeminiFull": used_gemini,
                "UsoTransformProveedor": used_transform,
                "UsoTransformAzure": used_transform_azure,
                "Issues": "; ".join(issues) if issues else None,
                "PluginProveedor": plugin_src or None
            })

            log_processing_complete(logger, name, n_items, used_gemini)
            logger.debug(f"  TransformAzure={used_transform_azure}, Transform={used_transform}")
            time.sleep(SLEEP_BETWEEN_FILES)

        except Exception as e:
            log_error(logger, name, e)
            rows_summary.append({
                "Archivo": name,
                "FileId": fid,
                "MimeType": mime,
                "ItemsDetectados": 0,
                "UsoGeminiFull": False,
                "UsoTransformProveedor": False,
                "UsoTransformAzure": False,
                "Issues": f"ERROR: {e}",
                "PluginProveedor": None
            })

    # DataFrames
    df_items = pd.DataFrame(rows_items)
    if not df_items.empty:
        cols = ["Archivo", "FileId", "Codigo", "Descripcion", "Cantidad",
                "PrecioUnitario", "Subtotal"]
        present = [c for c in cols if c in df_items.columns]
        df_items = df_items.reindex(columns=present)
        df_items = df_items.sort_values(by=["Archivo", "Descripcion"], na_position="last").reset_index(drop=True)

    df_summary = pd.DataFrame(rows_summary).sort_values(
        by=["ItemsDetectados", "Archivo"], ascending=[False, True]
    ).reset_index(drop=True)

    output_path = str(OUTPUT_FILE)
    with pd.ExcelWriter(output_path, engine="openpyxl") as xw:
        if not df_items.empty:
            df_items.to_excel(xw, index=False, sheet_name="items")
        df_summary.to_excel(xw, index=False, sheet_name="resumen")

    logger.info("\n=== RESULTADO ===")
    logger.info(f"Archivos procesados: {total_files}")
    logger.info(f"Archivos con ítems: {df_summary[df_summary['ItemsDetectados']>0].shape[0]}")
    if not df_items.empty:
        logger.info(f"Total ítems final: {df_items.shape[0]}")
    logger.info(f"Archivo generado: {output_path}")

if __name__ == "__main__":
    main()
