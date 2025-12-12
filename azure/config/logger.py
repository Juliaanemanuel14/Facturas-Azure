# logger.py
# -*- coding: utf-8 -*-
"""
Sistema de logging centralizado para el proyecto de extracción de facturas.
"""

import logging
import logging.config
from typing import Dict, List, Optional
import config.config as cfg

LOGGING_CONFIG = cfg.LOGGING_CONFIG


def setup_logging() -> None:
    """Configura el sistema de logging del proyecto."""
    logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger configurado para el módulo especificado.

    Args:
        name: Nombre del módulo (usa __name__ generalmente)

    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


# Utilidades para logging de ítems
def log_items_summary(logger: logging.Logger, tag: str, items: List[Dict],
                      max_items: Optional[int] = None) -> None:
    """
    Registra un resumen de los ítems extraídos.

    Args:
        logger: Logger a utilizar
        tag: Etiqueta descriptiva (ej: "Azure", "Gemini")
        items: Lista de ítems a registrar
        max_items: Número máximo de ítems a mostrar en detalle
    """
    n = len(items)
    logger.info(f"[{tag}] {n} ítems detectados")

    if n == 0:
        return

    to_show = items if max_items is None else items[:max_items]

    for idx, it in enumerate(to_show, start=1):
        item_str = (
            f"Codigo={it.get('Codigo')!r}, "
            f"Desc={it.get('Descripcion')!r}, "
            f"Cantidad={it.get('Cantidad')}, "
            f"PrecioUnit={it.get('PrecioUnitario')}, "
            f"Subtotal={it.get('Subtotal')}"
        )
        logger.debug(f"  {idx:02d}. {item_str}")

    if max_items is not None and n > max_items:
        logger.debug(f"  ... ({n - max_items} ítems más)")


def log_processing_start(logger: logging.Logger, file_name: str,
                         current: int, total: int) -> None:
    """Registra el inicio del procesamiento de un archivo."""
    logger.info(f"[{current}/{total}] Procesando: {file_name}")


def log_processing_complete(logger: logging.Logger, file_name: str,
                           items_count: int, used_gemini: bool) -> None:
    """Registra la finalización del procesamiento de un archivo."""
    source = "Gemini Full" if used_gemini else "Azure"
    logger.info(f"✓ {file_name}: {items_count} ítems extraídos ({source})")


def log_error(logger: logging.Logger, file_name: str, error: Exception) -> None:
    """Registra un error durante el procesamiento."""
    logger.error(f"✗ Error en {file_name}: {type(error).__name__}: {error}",
                exc_info=True)


def log_config_warning(logger: logging.Logger, message: str) -> None:
    """Registra una advertencia de configuración."""
    logger.warning(f"⚠ {message}")


def log_plugin_loaded(logger: logging.Logger, plugin_name: str, file_name: str) -> None:
    """Registra la carga de un plugin de proveedor."""
    logger.info(f"➕ Plugin detectado: {plugin_name} para {file_name}")


# Inicializar logging al importar el módulo
setup_logging()
