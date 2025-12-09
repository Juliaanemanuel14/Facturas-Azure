"""
Ejemplo Simple de Uso - Normalización con Tabla Auxiliar

Este script muestra cómo usar el normalizador con tu archivo de facturas
y la tabla auxiliar de normalización.
"""

from normalizacion_con_auxiliar import normalizar_productos_con_auxiliar

# ============================================================================
# CONFIGURACIÓN - AJUSTA ESTAS RUTAS A TUS ARCHIVOS
# ============================================================================

# Archivo con los datos extraídos (el que genera tu app de Streamlit)
ARCHIVO_DATOS = r"c:\Users\gesti\GESTION COMPARTIDA Dropbox\Departamento Gestion\0001 - Control de Gestion (1)\Desarrollo\azure\facturas_extraidas_20251126_174957.xlsx"

# Archivo con la tabla de normalización (Nombre Gestion -> Base)
ARCHIVO_AUXILIAR = r"c:\Users\gesti\GESTION COMPARTIDA Dropbox\Departamento Gestion\0001 - Control de Gestion (1)\Desarrollo\azure\tabla_normalizacion.xlsx"

# Archivo de salida
ARCHIVO_SALIDA = r"c:\Users\gesti\GESTION COMPARTIDA Dropbox\Departamento Gestion\0001 - Control de Gestion (1)\Desarrollo\azure\facturas_normalizadas.xlsx"

# ============================================================================
# EJECUCIÓN
# ============================================================================

if __name__ == "__main__":
    print("Iniciando normalización de productos...")

    try:
        # Ejecutar normalización
        df_normalizado, df_reporte = normalizar_productos_con_auxiliar(
            archivo_datos=ARCHIVO_DATOS,
            archivo_auxiliar=ARCHIVO_AUXILIAR,
            archivo_salida=ARCHIVO_SALIDA,
            hoja_datos='Items',                    # Hoja en tu archivo de datos
            hoja_auxiliar='Sheet1',                 # Hoja en la tabla auxiliar
            columna_descripcion='Descripcion',      # Columna con descripciones en datos
            columna_variante='Nombre Gestion',      # Columna con variantes en auxiliar
            columna_base='Base',                    # Columna con nombres base en auxiliar
            umbral_similitud=80,                    # Mínimo 80% de similitud
            metodo_similitud='token_sort_ratio',    # Tolerante a orden de palabras
            generar_reporte=True                    # Generar reporte de calidad
        )

        # Mostrar resumen
        print("\n" + "="*60)
        print("RESUMEN DE NORMALIZACIÓN")
        print("="*60)

        print(f"\nTotal de registros procesados: {len(df_normalizado):,}")
        print(f"Descripciones únicas originales: {df_normalizado['Descripcion'].nunique():,}")
        print(f"Descripciones únicas normalizadas: {df_normalizado['Descripcion_Normalizada'].nunique():,}")

        print("\nDistribución por tipo de match:")
        print(df_normalizado['Metodo_Match'].value_counts())

        print(f"\nSimilitud promedio: {df_normalizado['Similitud_Match'].mean():.1f}%")

        # Mostrar top 10 productos
        print("\n" + "="*60)
        print("TOP 10 PRODUCTOS MÁS FRECUENTES (NORMALIZADOS)")
        print("="*60)

        top_productos = df_normalizado.groupby('Descripcion_Normalizada').agg({
            'Cantidad': 'sum',
            'Subtotal': 'sum'
        }).sort_values('Cantidad', ascending=False).head(10)

        for idx, (producto, row) in enumerate(top_productos.iterrows(), 1):
            print(f"{idx:2d}. {producto:50s} - Cant: {row['Cantidad']:8,.0f} - Total: ${row['Subtotal']:12,.2f}")

        print(f"\n✅ Resultados guardados en: {ARCHIVO_SALIDA}")

    except Exception as e:
        print(f"\n❌ Error durante la normalización: {e}")
        import traceback
        traceback.print_exc()
