"""
Sistema de Normalización de Productos con Tabla Auxiliar
Usa un archivo Excel de referencia para normalizar nombres de productos

Autor: Sistema de Normalización
Fecha: 2025-01-26
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict
from pathlib import Path
from rapidfuzz import fuzz, process
from tqdm import tqdm
import warnings

warnings.filterwarnings('ignore')


def cargar_tabla_auxiliar(
    archivo_auxiliar: str,
    hoja: str = 'Sheet1',
    columna_variante: str = 'Nombre Gestion',
    columna_base: str = 'Base'
) -> pd.DataFrame:
    """
    Carga la tabla auxiliar de normalización.

    Args:
        archivo_auxiliar: Path al archivo Excel con la tabla de normalización
        hoja: Nombre de la hoja
        columna_variante: Nombre de la columna con variantes
        columna_base: Nombre de la columna con nombres base (normalizados)

    Returns:
        DataFrame con la tabla de normalización
    """
    print(f"\n{'='*60}")
    print("CARGANDO TABLA AUXILIAR DE NORMALIZACIÓN")
    print(f"{'='*60}")

    if not Path(archivo_auxiliar).exists():
        raise FileNotFoundError(f"No se encuentra el archivo auxiliar: {archivo_auxiliar}")

    df_aux = pd.read_excel(archivo_auxiliar, sheet_name=hoja)

    # Validar que existan las columnas requeridas
    if columna_variante not in df_aux.columns or columna_base not in df_aux.columns:
        raise ValueError(
            f"El archivo debe tener las columnas '{columna_variante}' y '{columna_base}'. "
            f"Columnas encontradas: {list(df_aux.columns)}"
        )

    # Limpiar espacios y convertir a string
    df_aux[columna_variante] = df_aux[columna_variante].astype(str).str.strip()
    df_aux[columna_base] = df_aux[columna_base].astype(str).str.strip()

    # Eliminar filas vacías
    df_aux = df_aux[
        (df_aux[columna_variante].notna()) &
        (df_aux[columna_variante] != '') &
        (df_aux[columna_base].notna()) &
        (df_aux[columna_base] != '')
    ].copy()

    print(f"✓ Registros de normalización cargados: {len(df_aux):,}")
    print(f"✓ Nombres base únicos: {df_aux[columna_base].nunique():,}")

    return df_aux


def normalizar_con_fuzzy_matching(
    df_datos: pd.DataFrame,
    df_auxiliar: pd.DataFrame,
    columna_descripcion: str = 'Descripcion',
    columna_variante: str = 'Nombre Gestion',
    columna_base: str = 'Base',
    umbral_similitud: int = 80,
    metodo: str = 'token_sort_ratio'
) -> pd.DataFrame:
    """
    Normaliza las descripciones usando fuzzy matching contra la tabla auxiliar.

    Args:
        df_datos: DataFrame con los datos a normalizar
        df_auxiliar: DataFrame con la tabla de normalización
        columna_descripcion: Columna con las descripciones en df_datos
        columna_variante: Columna con variantes en df_auxiliar
        columna_base: Columna con nombres base en df_auxiliar
        umbral_similitud: Umbral mínimo de similitud (0-100)
        metodo: Método de similitud ('token_sort_ratio', 'ratio', 'partial_ratio')

    Returns:
        DataFrame con columna adicional 'Descripcion_Normalizada'
    """
    print(f"\n{'='*60}")
    print("NORMALIZANDO DESCRIPCIONES CON FUZZY MATCHING")
    print(f"{'='*60}")
    print(f"Método de similitud: {metodo}")
    print(f"Umbral mínimo: {umbral_similitud}%")

    # Crear diccionario de mapeo variante -> base
    mapa_normalizacion = dict(zip(
        df_auxiliar[columna_variante],
        df_auxiliar[columna_base]
    ))

    # Obtener lista de variantes para matching
    variantes = list(mapa_normalizacion.keys())

    # Seleccionar función de similitud
    if metodo == 'token_sort_ratio':
        scorer = fuzz.token_sort_ratio
    elif metodo == 'partial_ratio':
        scorer = fuzz.partial_ratio
    else:
        scorer = fuzz.ratio

    # Normalizar cada descripción
    descripciones_unicas = df_datos[columna_descripcion].unique()
    mapa_resultados = {}

    print(f"\nProcesando {len(descripciones_unicas):,} descripciones únicas...")

    for desc in tqdm(descripciones_unicas, desc="Normalizando"):
        if pd.isna(desc) or str(desc).strip() == '':
            mapa_resultados[desc] = {
                'normalizada': '',
                'similitud': 0,
                'metodo': 'Sin descripción'
            }
            continue

        desc_limpia = str(desc).strip()

        # Buscar coincidencia exacta primero (case-insensitive)
        coincidencia_exacta = None
        for variante in variantes:
            if desc_limpia.upper() == variante.upper():
                coincidencia_exacta = variante
                break

        if coincidencia_exacta:
            mapa_resultados[desc] = {
                'normalizada': mapa_normalizacion[coincidencia_exacta],
                'similitud': 100,
                'metodo': 'Exacta'
            }
        else:
            # Fuzzy matching
            resultado = process.extractOne(
                desc_limpia,
                variantes,
                scorer=scorer
            )

            if resultado and resultado[1] >= umbral_similitud:
                mejor_match, similitud, _ = resultado
                mapa_resultados[desc] = {
                    'normalizada': mapa_normalizacion[mejor_match],
                    'similitud': similitud,
                    'metodo': 'Fuzzy',
                    'match_original': mejor_match
                }
            else:
                # No se encontró match suficientemente bueno
                mapa_resultados[desc] = {
                    'normalizada': desc_limpia,  # Mantener original
                    'similitud': resultado[1] if resultado else 0,
                    'metodo': 'Sin match'
                }

    # Aplicar normalización al DataFrame
    df_resultado = df_datos.copy()

    df_resultado['Descripcion_Normalizada'] = df_resultado[columna_descripcion].map(
        lambda x: mapa_resultados.get(x, {}).get('normalizada', str(x))
    )

    df_resultado['Similitud_Match'] = df_resultado[columna_descripcion].map(
        lambda x: mapa_resultados.get(x, {}).get('similitud', 0)
    )

    df_resultado['Metodo_Match'] = df_resultado[columna_descripcion].map(
        lambda x: mapa_resultados.get(x, {}).get('metodo', 'Desconocido')
    )

    # Estadísticas
    print(f"\n{'='*60}")
    print("ESTADÍSTICAS DE NORMALIZACIÓN")
    print(f"{'='*60}")

    stats = df_resultado.groupby('Metodo_Match').size()
    for metodo, cantidad in stats.items():
        porcentaje = (cantidad / len(df_resultado)) * 100
        print(f"{metodo:15s}: {cantidad:6,} ({porcentaje:5.1f}%)")

    print(f"\n✓ Productos normalizados exitosamente")

    return df_resultado


def generar_reporte_calidad(
    df_normalizado: pd.DataFrame,
    archivo_salida: str = None
) -> pd.DataFrame:
    """
    Genera un reporte de calidad de normalización.

    Args:
        df_normalizado: DataFrame con normalización aplicada
        archivo_salida: Path para guardar el reporte (opcional)

    Returns:
        DataFrame con el reporte de calidad
    """
    print(f"\n{'='*60}")
    print("GENERANDO REPORTE DE CALIDAD")
    print(f"{'='*60}")

    # Agrupar por descripción original y normalizada
    reporte = df_normalizado.groupby(
        ['Descripcion', 'Descripcion_Normalizada', 'Metodo_Match']
    ).agg({
        'Similitud_Match': 'first',
        'Cantidad': 'sum'
    }).reset_index()

    reporte.columns = [
        'Descripcion_Original',
        'Descripcion_Normalizada',
        'Metodo_Match',
        'Similitud',
        'Volumen_Total'
    ]

    # Ordenar por volumen
    reporte = reporte.sort_values('Volumen_Total', ascending=False)

    # Calcular impacto
    reporte['Porcentaje_Volumen'] = (
        reporte['Volumen_Total'] / reporte['Volumen_Total'].sum() * 100
    )

    print(f"\n✓ Reporte generado con {len(reporte):,} registros")

    if archivo_salida:
        reporte.to_excel(archivo_salida, index=False)
        print(f"✓ Reporte guardado en: {archivo_salida}")

    return reporte


def normalizar_productos_con_auxiliar(
    archivo_datos: str,
    archivo_auxiliar: str,
    archivo_salida: str = None,
    hoja_datos: str = 'Items',
    hoja_auxiliar: str = 'Sheet1',
    columna_descripcion: str = 'Descripcion',
    columna_variante: str = 'Nombre Gestion',
    columna_base: str = 'Base',
    umbral_similitud: int = 80,
    metodo_similitud: str = 'token_sort_ratio',
    generar_reporte: bool = True
) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Función principal para normalizar productos usando tabla auxiliar.

    Args:
        archivo_datos: Path al Excel con los datos a normalizar
        archivo_auxiliar: Path al Excel con la tabla de normalización
        archivo_salida: Path para guardar resultados (opcional)
        hoja_datos: Nombre de la hoja en archivo_datos
        hoja_auxiliar: Nombre de la hoja en archivo_auxiliar
        columna_descripcion: Columna con descripciones en datos
        columna_variante: Columna con variantes en auxiliar
        columna_base: Columna con nombres base en auxiliar
        umbral_similitud: Umbral mínimo de similitud (0-100)
        metodo_similitud: Método de similitud a usar
        generar_reporte: Si True, genera reporte de calidad

    Returns:
        Tupla (df_normalizado, df_reporte)
    """
    print("\n" + "="*60)
    print("  NORMALIZACIÓN DE PRODUCTOS CON TABLA AUXILIAR")
    print("="*60)

    # 1. Cargar datos
    print(f"\n📂 Cargando datos: {archivo_datos}")
    df_datos = pd.read_excel(archivo_datos, sheet_name=hoja_datos)
    print(f"✓ Registros cargados: {len(df_datos):,}")

    # 2. Cargar tabla auxiliar
    df_auxiliar = cargar_tabla_auxiliar(
        archivo_auxiliar,
        hoja_auxiliar,
        columna_variante,
        columna_base
    )

    # 3. Normalizar
    df_normalizado = normalizar_con_fuzzy_matching(
        df_datos,
        df_auxiliar,
        columna_descripcion,
        columna_variante,
        columna_base,
        umbral_similitud,
        metodo_similitud
    )

    # 4. Generar reporte de calidad
    df_reporte = None
    if generar_reporte:
        df_reporte = generar_reporte_calidad(df_normalizado)

    # 5. Guardar resultados
    if archivo_salida:
        print(f"\n{'='*60}")
        print("GUARDANDO RESULTADOS")
        print(f"{'='*60}")

        with pd.ExcelWriter(archivo_salida, engine='openpyxl') as writer:
            # Hoja principal con datos normalizados
            df_normalizado.to_excel(writer, sheet_name='Datos_Normalizados', index=False)

            # Reporte de calidad
            if df_reporte is not None:
                df_reporte.to_excel(writer, sheet_name='Reporte_Calidad', index=False)

            # Resumen ejecutivo
            resumen = {
                'Métrica': [
                    'Total Registros',
                    'Descripciones Únicas Originales',
                    'Descripciones Únicas Normalizadas',
                    'Matches Exactos',
                    'Matches Fuzzy',
                    'Sin Match',
                    'Similitud Promedio (%)'
                ],
                'Valor': [
                    len(df_normalizado),
                    df_normalizado['Descripcion'].nunique(),
                    df_normalizado['Descripcion_Normalizada'].nunique(),
                    (df_normalizado['Metodo_Match'] == 'Exacta').sum(),
                    (df_normalizado['Metodo_Match'] == 'Fuzzy').sum(),
                    (df_normalizado['Metodo_Match'] == 'Sin match').sum(),
                    df_normalizado['Similitud_Match'].mean()
                ]
            }

            pd.DataFrame(resumen).to_excel(writer, sheet_name='Resumen', index=False)

        print(f"\n✅ Archivo guardado: {archivo_salida}")

    print(f"\n{'='*60}")
    print("✅ NORMALIZACIÓN COMPLETADA")
    print(f"{'='*60}\n")

    return df_normalizado, df_reporte


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    """
    Ejemplo de ejecución del script.
    """

    # Configuración
    ARCHIVO_DATOS = "facturas_extraidas_20251126_174957.xlsx"  # 👈 Tu archivo de datos
    ARCHIVO_AUXILIAR = "tabla_normalizacion.xlsx"  # 👈 Tu tabla auxiliar
    ARCHIVO_SALIDA = "facturas_normalizadas.xlsx"

    try:
        df_normalizado, df_reporte = normalizar_productos_con_auxiliar(
            archivo_datos=ARCHIVO_DATOS,
            archivo_auxiliar=ARCHIVO_AUXILIAR,
            archivo_salida=ARCHIVO_SALIDA,
            hoja_datos='Items',
            hoja_auxiliar='Sheet1',
            columna_descripcion='Descripcion',
            columna_variante='Nombre Gestion',
            columna_base='Base',
            umbral_similitud=80,
            metodo_similitud='token_sort_ratio',
            generar_reporte=True
        )

        # Mostrar muestra de resultados
        print("\n" + "="*60)
        print("MUESTRA DE RESULTADOS")
        print("="*60)
        print(df_normalizado[[
            'Descripcion',
            'Descripcion_Normalizada',
            'Metodo_Match',
            'Similitud_Match'
        ]].head(20))

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
