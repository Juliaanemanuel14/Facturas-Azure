# app.py
# -*- coding: utf-8 -*-
"""
Interfaz web con Streamlit para extracción de datos de facturas.
Permite cargar archivos y procesarlos con Azure + Gemini.

Uso:
    streamlit run app.py
"""

import io
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

import streamlit as st
import pandas as pd
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

# Importar módulos del proyecto
from config import (
    AZURE_ENDPOINT,
    AZURE_KEY,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    ALLOWED_MIME_TYPES,
)
from logger import get_logger
from test import (
    _unwrap_azure_num,
    extract_items_from_file,
)

# Configurar logger
logger = get_logger(__name__)

# Configuración de la página
st.set_page_config(
    page_title="Extractor de Facturas",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #e8f5e9;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4caf50;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #ffebee;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f44336;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #1565c0;
    }
</style>
""", unsafe_allow_html=True)


def process_single_file(file_bytes: bytes, filename: str) -> tuple[List[Dict], str]:
    """
    Procesa un archivo de factura y extrae los ítems.

    Args:
        file_bytes: Contenido del archivo en bytes
        filename: Nombre del archivo

    Returns:
        Tupla de (items, método_usado)
    """
    try:
        # Guardar temporalmente el archivo
        temp_path = Path("temp") / filename
        temp_path.parent.mkdir(exist_ok=True)

        with open(temp_path, "wb") as f:
            f.write(file_bytes)

        # Procesar con Azure
        items = extract_items_from_file(str(temp_path))

        # Limpiar archivo temporal
        temp_path.unlink()

        return items, "Azure Document Intelligence"

    except Exception as e:
        logger.error(f"Error procesando {filename}: {e}")
        raise e


def create_excel_download(items: List[Dict], filename_prefix: str = "facturas") -> bytes:
    """
    Crea un archivo Excel con los ítems extraídos.

    Args:
        items: Lista de ítems extraídos
        filename_prefix: Prefijo para el nombre del archivo

    Returns:
        Bytes del archivo Excel
    """
    df = pd.DataFrame(items)

    # Reordenar columnas
    cols_order = ["Archivo", "Codigo", "Descripcion", "Cantidad", "PrecioUnitario", "Subtotal"]
    available_cols = [c for c in cols_order if c in df.columns]
    df = df[available_cols]

    # Crear Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Items')

        # Ajustar ancho de columnas
        worksheet = writer.sheets['Items']
        for idx, col in enumerate(df.columns, 1):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            )
            worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 50)

    output.seek(0)
    return output.getvalue()


def main():
    """Función principal de la aplicación."""

    # Header
    st.markdown('<h1 class="main-header">📄 Extractor de Datos de Facturas</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar - Información
    with st.sidebar:
        st.header("📋 Formatos Soportados")
        st.write("- 📷 Imágenes: JPG, JPEG, PNG")
        st.write("- 📄 Documentos: PDF")

        st.markdown("---")

        st.info("💡 Arrastra tus facturas o haz clic para seleccionarlas")

    # Área principal
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("📤 Cargar Facturas")

        # Modo de carga
        upload_mode = st.radio(
            "Selecciona el modo de carga:",
            ["Archivo único", "Múltiples archivos"],
            horizontal=True
        )

        if upload_mode == "Archivo único":
            uploaded_file = st.file_uploader(
                "Arrastra tu factura aquí o haz clic para seleccionar",
                type=['jpg', 'jpeg', 'png', 'pdf'],
                help="Formatos soportados: JPG, PNG, PDF"
            )
            uploaded_files = [uploaded_file] if uploaded_file else []
        else:
            uploaded_files = st.file_uploader(
                "Arrastra tus facturas aquí o haz clic para seleccionar",
                type=['jpg', 'jpeg', 'png', 'pdf'],
                accept_multiple_files=True,
                help="Formatos soportados: JPG, PNG, PDF"
            )

    with col2:
        st.header("📊 Estadísticas")

        if uploaded_files:
            st.metric("Archivos cargados", len(uploaded_files))
            total_size = sum(f.size for f in uploaded_files if f) / 1024  # KB
            st.metric("Tamaño total", f"{total_size:.1f} KB")
        else:
            st.info("No hay archivos cargados")

    # Procesar archivos
    if uploaded_files and any(uploaded_files):
        st.markdown("---")

        if st.button("🚀 Procesar Facturas", type="primary"):
            all_items = []

            # Barra de progreso
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Contenedor para resultados
            results_container = st.container()

            for idx, uploaded_file in enumerate(uploaded_files):
                if not uploaded_file:
                    continue

                progress = (idx + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                status_text.text(f"Procesando: {uploaded_file.name} ({idx + 1}/{len(uploaded_files)})")

                try:
                    # Leer bytes del archivo
                    file_bytes = uploaded_file.read()

                    # Procesar archivo
                    with st.spinner(f"Analizando {uploaded_file.name}..."):
                        items, method = process_single_file(file_bytes, uploaded_file.name)

                    # Agregar nombre de archivo a cada ítem
                    for item in items:
                        item['Archivo'] = uploaded_file.name

                    all_items.extend(items)

                    # Mostrar resultado individual
                    with results_container:
                        with st.expander(f"✅ {uploaded_file.name} - {len(items)} ítems extraídos"):
                            if items:
                                df_preview = pd.DataFrame(items)
                                st.dataframe(df_preview, use_container_width=True)
                            else:
                                st.warning("No se encontraron ítems en este archivo")

                except Exception as e:
                    with results_container:
                        st.error(f"❌ Error en {uploaded_file.name}: {str(e)}")
                    logger.error(f"Error procesando {uploaded_file.name}: {e}", exc_info=True)

            # Limpiar barra de progreso
            progress_bar.empty()
            status_text.empty()

            # Mostrar resultados finales
            st.markdown("---")
            st.header("📊 Resultados Finales")

            if all_items:
                st.success(f"✅ Procesamiento completado: {len(all_items)} ítems extraídos de {len(uploaded_files)} archivos")

                # DataFrame completo
                df_final = pd.DataFrame(all_items)

                # Mostrar tabla
                st.subheader("📋 Vista Previa de Datos")
                st.dataframe(df_final, use_container_width=True, height=400)

                # Estadísticas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Ítems", len(df_final))
                with col2:
                    st.metric("Total Facturas", df_final['Archivo'].nunique())
                with col3:
                    total_amount = df_final['Subtotal'].sum()
                    st.metric("Total $", f"${total_amount:,.2f}")
                with col4:
                    avg_items = len(df_final) / df_final['Archivo'].nunique()
                    st.metric("Promedio ítems/factura", f"{avg_items:.1f}")

                # Botón de descarga
                st.markdown("---")
                st.subheader("💾 Descargar Resultados")

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"facturas_extraidas_{timestamp}.xlsx"

                excel_bytes = create_excel_download(all_items, "facturas")

                st.download_button(
                    label="📥 Descargar Excel",
                    data=excel_bytes,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )

                st.success(f"✅ Archivo listo para descargar: {filename}")
            else:
                st.warning("⚠️ No se pudieron extraer ítems de los archivos procesados")

    else:
        # Mensaje de bienvenida
        st.info("👋 ¡Bienvenido al Extractor de Facturas!")

        st.markdown("""
        Este sistema utiliza **inteligencia artificial** para extraer automáticamente los datos de tus facturas.
        """)

        st.markdown("### 📝 Pasos para comenzar:")

        st.markdown("""
        1. **Selecciona el modo de carga** (único o múltiple)
        2. **Arrastra o selecciona** tus archivos de factura
        3. **Haz clic** en "Procesar Facturas"
        4. **Revisa los resultados** y descarga el Excel generado
        """)

        # Ejemplo visual
        st.markdown("---")
        st.markdown("### 📸 Requisitos de las Facturas")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.success("✅ Imágenes claras y legibles")
        with col2:
            st.success("✅ Formatos: JPG, PNG, PDF")
        with col3:
            st.success("✅ Campos bien definidos")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>💡 <b>Consejo:</b> Para mejores resultados, asegúrate de que las facturas sean legibles y estén bien iluminadas.</p>
        <p>🔧 Desarrollado con Azure Document Intelligence y Google Gemini AI</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
