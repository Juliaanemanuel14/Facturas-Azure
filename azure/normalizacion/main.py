"""
Sistema de Normalización de Productos - Clustering Jerárquico
Migración de VBA a Python con mejoras de rendimiento

Autor: Sistema de Normalización
Fecha: 2025-01-26
"""

import pandas as pd
import numpy as np
import re
from typing import Tuple, Dict, List, Optional
from pathlib import Path
from rapidfuzz import fuzz
from tqdm import tqdm
import warnings

warnings.filterwarnings('ignore')


# ============================================================================
# 1. MÓDULO DE PROCESAMIENTO Y AUDITORÍA (ETL)
# ============================================================================

def parse_columna_concatenada(valor: str) -> Dict[str, str]:
    """
    Extrae información de la columna A concatenada usando REGEX.

    Formato esperado: "Tipo - Num - Fecha - Prov - OC"
    Ejemplo: "FC - 0001-12345678 - 2024-01-15 - PROVEEDOR SA - OC001"

    Args:
        valor: String concatenado de la columna A

    Returns:
        Diccionario con los campos extraídos
    """
    resultado = {
        'tipo': None,
        'numero': None,
        'fecha': None,
        'proveedor': None,
        'orden_compra': None
    }

    try:
        # Dividir por guiones (considerando espacios)
        partes = [p.strip() for p in str(valor).split('-')]

        if len(partes) >= 1:
            resultado['tipo'] = partes[0]

        if len(partes) >= 2:
            # Extraer número (puede tener formato XXXX-XXXXXXXX)
            resultado['numero'] = partes[1]

        if len(partes) >= 3:
            # Extraer fecha (formato YYYY-MM-DD o DD/MM/YYYY)
            fecha_match = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})', partes[2])
            if fecha_match:
                resultado['fecha'] = fecha_match.group(1)

        if len(partes) >= 4:
            resultado['proveedor'] = partes[3]

        if len(partes) >= 5:
            # OC puede estar en la última parte
            resultado['orden_compra'] = '-'.join(partes[4:])

    except Exception as e:
        print(f"Error parseando '{valor}': {e}")

    return resultado


def rescatar_valores_numericos(row: pd.Series) -> pd.Series:
    """
    Aplica lógica de rescate numérico para Cantidad, Precio y Subtotal.
    Si falta 1 de los 3, lo calcula. Si faltan 2+, marca como insalvable.

    Args:
        row: Fila del DataFrame con columnas 'Cantidad', 'Precio_Unitario', 'Subtotal'

    Returns:
        Fila modificada con valores rescatados y flag 'Salvable'
    """
    cantidad = row.get('Cantidad', np.nan)
    precio = row.get('Precio_Unitario', np.nan)
    subtotal = row.get('Subtotal', np.nan)

    # Contar cuántos valores faltan
    valores = [cantidad, precio, subtotal]
    faltantes = sum(1 for v in valores if pd.isna(v) or v == 0)

    # Si faltan 2 o más -> Insalvable
    if faltantes >= 2:
        row['Salvable'] = False
        return row

    # Si falta 1, intentar calcular
    try:
        if pd.isna(cantidad) or cantidad == 0:
            if precio != 0:
                row['Cantidad'] = subtotal / precio
            else:
                row['Salvable'] = False
                return row

        elif pd.isna(precio) or precio == 0:
            if cantidad != 0:
                row['Precio_Unitario'] = subtotal / cantidad
            else:
                row['Salvable'] = False
                return row

        elif pd.isna(subtotal) or subtotal == 0:
            row['Subtotal'] = cantidad * precio

        row['Salvable'] = True

    except Exception as e:
        print(f"Error en rescate numérico: {e}")
        row['Salvable'] = False

    return row


def procesar_facturas_con_auditoria(
    archivo_excel: str,
    hoja: str = 'Datos'
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Carga y procesa el archivo Excel de facturas, aplicando auditoría y rescate.

    Args:
        archivo_excel: Path al archivo Excel
        hoja: Nombre de la hoja a procesar

    Returns:
        Tupla (df_procesados, df_insalvables)
    """
    print(f"\n{'='*60}")
    print("MÓDULO 1: PROCESAMIENTO Y AUDITORÍA")
    print(f"{'='*60}")

    # Cargar Excel
    print(f"\n📂 Cargando archivo: {archivo_excel}")
    df = pd.read_excel(archivo_excel, sheet_name=hoja)
    print(f"✓ Registros cargados: {len(df):,}")

    # Parsear columna concatenada (asumiendo que está en columna A o 'Info')
    if 'Info' in df.columns or df.columns[0]:
        columna_info = 'Info' if 'Info' in df.columns else df.columns[0]
        print(f"\n🔍 Parseando columna concatenada: '{columna_info}'")

        info_parseada = df[columna_info].apply(parse_columna_concatenada)
        df_info = pd.DataFrame(info_parseada.tolist())
        df = pd.concat([df_info, df], axis=1)

    # Asegurar que existan las columnas necesarias
    columnas_requeridas = ['Cantidad', 'Precio_Unitario', 'Subtotal', 'Descripcion']
    for col in columnas_requeridas:
        if col not in df.columns:
            print(f"⚠️  Advertencia: Columna '{col}' no encontrada")

    # Aplicar rescate numérico
    print("\n💾 Aplicando lógica de rescate numérico...")
    df['Salvable'] = True
    df = df.apply(rescatar_valores_numericos, axis=1)

    # Separar procesados vs insalvables
    df_procesados = df[df['Salvable'] == True].copy()
    df_insalvables = df[df['Salvable'] == False].copy()

    print(f"\n✅ Registros procesados: {len(df_procesados):,}")
    print(f"❌ Registros insalvables: {len(df_insalvables):,}")

    return df_procesados, df_insalvables


# ============================================================================
# 2. MÓDULO DE ANÁLISIS DE FRECUENCIA (PARETO)
# ============================================================================

def analisis_pareto(
    df: pd.DataFrame,
    columna_descripcion: str = 'Descripcion',
    columna_cantidad: str = 'Cantidad'
) -> pd.DataFrame:
    """
    Calcula frecuencia y volumen de cada descripción única.
    Categoriza usando percentiles acumulados (Pareto).

    Args:
        df: DataFrame procesado
        columna_descripcion: Nombre de la columna con descripciones
        columna_cantidad: Nombre de la columna con cantidades

    Returns:
        DataFrame con análisis de frecuencia agregado
    """
    print(f"\n{'='*60}")
    print("MÓDULO 2: ANÁLISIS DE FRECUENCIA (PARETO)")
    print(f"{'='*60}")

    # Agrupar por descripción
    print(f"\n📊 Calculando frecuencias y volúmenes...")

    df_freq = df.groupby(columna_descripcion).agg({
        columna_cantidad: ['count', 'sum']
    }).reset_index()

    df_freq.columns = ['Descripcion', 'Frecuencia', 'Volumen_Total']

    # Calcular volumen ponderado
    df_freq['Volumen_Ponderado'] = df_freq['Frecuencia'] * df_freq['Volumen_Total']

    # Ordenar por volumen ponderado descendente
    df_freq = df_freq.sort_values('Volumen_Ponderado', ascending=False).reset_index(drop=True)

    # Calcular percentiles acumulados
    df_freq['Acumulado'] = df_freq['Volumen_Ponderado'].cumsum()
    df_freq['Percentil_Acumulado'] = (df_freq['Acumulado'] / df_freq['Volumen_Ponderado'].sum()) * 100

    # Categorizar según Pareto
    def categorizar_pareto(percentil):
        if percentil <= 40:
            return 'Excelente'
        elif percentil <= 60:
            return 'Muy Bueno'
        elif percentil <= 80:
            return 'Bueno'
        elif percentil <= 95:
            return 'Regular'
        else:
            return 'Ruido'

    df_freq['Categoria_Pareto'] = df_freq['Percentil_Acumulado'].apply(categorizar_pareto)

    print(f"\n✓ Descripciones únicas: {len(df_freq):,}")
    print("\nDistribución por categoría:")
    print(df_freq['Categoria_Pareto'].value_counts())

    # Merge con el dataframe original
    df_resultado = df.merge(
        df_freq[['Descripcion', 'Frecuencia', 'Categoria_Pareto']],
        left_on=columna_descripcion,
        right_on='Descripcion',
        how='left'
    )

    return df_resultado


# ============================================================================
# 3. MÓDULO DE CLUSTERING JERÁRQUICO (NÚCLEO)
# ============================================================================

def clustering_jerarquico(
    df: pd.DataFrame,
    columna_descripcion: str = 'Descripcion',
    umbrales: List[int] = [85, 75, 65, 55],
    usar_token_sort: bool = True
) -> pd.DataFrame:
    """
    Aplica clustering jerárquico en cascada (4 niveles).
    Usa rapidfuzz para cálculo eficiente de similitud.

    Args:
        df: DataFrame con análisis de frecuencia
        columna_descripcion: Columna con descripciones
        umbrales: Lista de umbrales de similitud por nivel [N1, N2, N3, N4]
        usar_token_sort: Si True, usa token_sort_ratio (tolera orden diferente)

    Returns:
        DataFrame con columnas Familia_N1, Familia_N2, Familia_N3, Familia_N4
    """
    print(f"\n{'='*60}")
    print("MÓDULO 3: CLUSTERING JERÁRQUICO")
    print(f"{'='*60}")
    print(f"\n🎯 Umbrales de similitud: {umbrales}")
    print(f"🔧 Método: {'token_sort_ratio' if usar_token_sort else 'ratio'}")

    # Obtener descripciones únicas ordenadas por frecuencia
    if 'Frecuencia' in df.columns:
        df_unique = df.groupby(columna_descripcion).agg({
            'Frecuencia': 'first'
        }).reset_index().sort_values('Frecuencia', ascending=False)
    else:
        df_unique = pd.DataFrame({
            columna_descripcion: df[columna_descripcion].unique()
        })
        df_unique['Frecuencia'] = 1

    descripciones = df_unique[columna_descripcion].tolist()
    n_descripciones = len(descripciones)

    print(f"\n📝 Descripciones únicas a agrupar: {n_descripciones:,}")

    # Función de similitud
    similitud_func = fuzz.token_sort_ratio if usar_token_sort else fuzz.ratio

    # Diccionarios para almacenar familias por nivel
    familias = {f'Nivel_{i+1}': {} for i in range(len(umbrales))}

    # Nivel 1: Agrupación inicial
    print(f"\n{'='*60}")
    print(f"NIVEL 1 - Similitud > {umbrales[0]}%")
    print(f"{'='*60}")

    maestras_n1 = {}
    asignadas_n1 = set()

    for i, desc in enumerate(tqdm(descripciones, desc="Nivel 1")):
        if desc in asignadas_n1:
            continue

        # Esta descripción es la maestra de su grupo
        maestras_n1[desc] = desc
        asignadas_n1.add(desc)

        # Buscar similares
        for j in range(i + 1, n_descripciones):
            desc_candidata = descripciones[j]

            if desc_candidata in asignadas_n1:
                continue

            similitud = similitud_func(desc, desc_candidata)

            if similitud > umbrales[0]:
                maestras_n1[desc_candidata] = desc
                asignadas_n1.add(desc_candidata)

    print(f"✓ Familias generadas: {len(set(maestras_n1.values())):,}")

    # Niveles 2-4: Agrupación en cascada
    nivel_anterior = maestras_n1

    for nivel in range(1, len(umbrales)):
        print(f"\n{'='*60}")
        print(f"NIVEL {nivel + 1} - Similitud > {umbrales[nivel]}%")
        print(f"{'='*60}")

        # Obtener maestras únicas del nivel anterior
        maestras_previas = list(set(nivel_anterior.values()))
        n_maestras = len(maestras_previas)

        print(f"Maestras del nivel anterior: {n_maestras:,}")

        maestras_nivel = {}
        asignadas_nivel = set()

        for i, maestra in enumerate(tqdm(maestras_previas, desc=f"Nivel {nivel + 1}")):
            if maestra in asignadas_nivel:
                continue

            # Esta maestra es la representante de su familia
            maestras_nivel[maestra] = maestra
            asignadas_nivel.add(maestra)

            # Buscar maestras similares
            for j in range(i + 1, n_maestras):
                candidata = maestras_previas[j]

                if candidata in asignadas_nivel:
                    continue

                similitud = similitud_func(maestra, candidata)

                if similitud > umbrales[nivel]:
                    maestras_nivel[candidata] = maestra
                    asignadas_nivel.add(candidata)

        print(f"✓ Familias generadas: {len(set(maestras_nivel.values())):,}")

        # Propagar asignaciones a todas las descripciones originales
        nivel_completo = {}
        for desc_original, maestra_anterior in nivel_anterior.items():
            nivel_completo[desc_original] = maestras_nivel.get(maestra_anterior, maestra_anterior)

        familias[f'Nivel_{nivel + 1}'] = nivel_completo
        nivel_anterior = nivel_completo

    # Agregar Nivel 1 a familias
    familias['Nivel_1'] = maestras_n1

    # Crear DataFrame con todas las asignaciones
    print(f"\n{'='*60}")
    print("CONSOLIDANDO RESULTADOS")
    print(f"{'='*60}")

    df_familias = pd.DataFrame({
        columna_descripcion: descripciones
    })

    for nivel_num in range(1, len(umbrales) + 1):
        nombre_col = f'Familia_N{nivel_num}'
        df_familias[nombre_col] = df_familias[columna_descripcion].map(
            familias[f'Nivel_{nivel_num}']
        )

    # Merge con el dataframe original
    df_resultado = df.merge(
        df_familias,
        on=columna_descripcion,
        how='left'
    )

    print(f"\n✅ Clustering completado exitosamente")

    return df_resultado


# ============================================================================
# 4. FUNCIÓN PRINCIPAL Y EJECUCIÓN
# ============================================================================

def normalizar_productos(
    archivo_entrada: str,
    archivo_salida: str = None,
    hoja_entrada: str = 'Datos',
    columna_descripcion: str = 'Descripcion',
    columna_cantidad: str = 'Cantidad',
    umbrales_clustering: List[int] = [85, 75, 65, 55],
    generar_insalvables: bool = True
) -> pd.DataFrame:
    """
    Función principal que ejecuta todo el pipeline de normalización.

    Args:
        archivo_entrada: Path del archivo Excel de entrada
        archivo_salida: Path del archivo Excel de salida (opcional)
        hoja_entrada: Nombre de la hoja a procesar
        columna_descripcion: Nombre de la columna con descripciones
        columna_cantidad: Nombre de la columna con cantidades
        umbrales_clustering: Umbrales de similitud por nivel
        generar_insalvables: Si True, genera hoja separada con insalvables

    Returns:
        DataFrame con toda la información procesada
    """
    print("\n" + "="*60)
    print("  SISTEMA DE NORMALIZACIÓN DE PRODUCTOS")
    print("  Clustering Jerárquico - Python Edition")
    print("="*60)

    # Validar archivo de entrada
    if not Path(archivo_entrada).exists():
        raise FileNotFoundError(f"No se encuentra el archivo: {archivo_entrada}")

    # 1. ETL y Auditoría
    df_procesados, df_insalvables = procesar_facturas_con_auditoria(
        archivo_entrada,
        hoja_entrada
    )

    # 2. Análisis de Frecuencia (Pareto)
    df_con_frecuencia = analisis_pareto(
        df_procesados,
        columna_descripcion,
        columna_cantidad
    )

    # 3. Clustering Jerárquico
    df_final = clustering_jerarquico(
        df_con_frecuencia,
        columna_descripcion,
        umbrales_clustering
    )

    # 4. Guardar resultados
    if archivo_salida:
        print(f"\n{'='*60}")
        print("GUARDANDO RESULTADOS")
        print(f"{'='*60}")

        archivo_salida = Path(archivo_salida)

        with pd.ExcelWriter(archivo_salida, engine='openpyxl') as writer:
            df_final.to_excel(writer, sheet_name='Procesados', index=False)

            if generar_insalvables and len(df_insalvables) > 0:
                df_insalvables.to_excel(writer, sheet_name='Insalvables', index=False)

            # Generar resumen
            resumen = {
                'Métrica': [
                    'Total Registros',
                    'Registros Procesados',
                    'Registros Insalvables',
                    'Descripciones Únicas',
                    'Familias Nivel 1',
                    'Familias Nivel 2',
                    'Familias Nivel 3',
                    'Familias Nivel 4'
                ],
                'Valor': [
                    len(df_procesados) + len(df_insalvables),
                    len(df_procesados),
                    len(df_insalvables),
                    df_final['Descripcion'].nunique(),
                    df_final['Familia_N1'].nunique() if 'Familia_N1' in df_final.columns else 0,
                    df_final['Familia_N2'].nunique() if 'Familia_N2' in df_final.columns else 0,
                    df_final['Familia_N3'].nunique() if 'Familia_N3' in df_final.columns else 0,
                    df_final['Familia_N4'].nunique() if 'Familia_N4' in df_final.columns else 0
                ]
            }

            pd.DataFrame(resumen).to_excel(writer, sheet_name='Resumen', index=False)

        print(f"\n✅ Archivo guardado: {archivo_salida}")
        print(f"   - Hoja 'Procesados': {len(df_final):,} registros")
        if generar_insalvables:
            print(f"   - Hoja 'Insalvables': {len(df_insalvables):,} registros")
        print(f"   - Hoja 'Resumen': Métricas del proceso")

    print(f"\n{'='*60}")
    print("✅ PROCESO COMPLETADO EXITOSAMENTE")
    print(f"{'='*60}\n")

    return df_final


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    """
    Ejemplo de ejecución del script.
    Ajusta las rutas según tu estructura de archivos.
    """

    # Configuración
    ARCHIVO_ENTRADA = "facturas_input.xlsx"  # 👈 CAMBIAR ESTA RUTA
    ARCHIVO_SALIDA = "facturas_normalizadas.xlsx"

    # Ejecutar normalización
    try:
        df_resultado = normalizar_productos(
            archivo_entrada=ARCHIVO_ENTRADA,
            archivo_salida=ARCHIVO_SALIDA,
            hoja_entrada='Datos',
            columna_descripcion='Descripcion',
            columna_cantidad='Cantidad',
            umbrales_clustering=[85, 75, 65, 55],
            generar_insalvables=True
        )

        # Mostrar muestra de resultados
        print("\n" + "="*60)
        print("MUESTRA DE RESULTADOS")
        print("="*60)
        print(df_resultado[['Descripcion', 'Familia_N1', 'Familia_N2', 'Familia_N3', 'Familia_N4']].head(10))

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
