# proveedores/quilmes.py
# -*- coding: utf-8 -*-

PATTERNS = [
    r"(?i)\bQUILMES\b",
    r"(?i)CERVECER[ÍI]A\s+Y\s+MALTER[ÍI]A\s+QUILMES",
    "QUIL",
    "ERES",
    "FC"
]

PROMPT = """
Actúa como un procesador de datos experto especializado en facturas de "CERVECERIA Y MALTERIA QUILMES".
Tu objetivo es generar una tabla exacta al formato solicitado, infiriendo datos de empaque desde la descripción.

Reglas de Normalización:
1. Formato numérico: 10.000,00 (Separador de miles punto, decimal coma).
2. Fechas: dd-mmm (ej. 28-oct).
3. Si un valor es 0, déjalo como 0,00.

PASO 1: Datos Globales y Coeficientes
Extrae del Pie de Factura:
- TOTAL_NETO_FACTURA: Valor numérico bajo "SUBTOTAL" en el pie (ej. 927903,20).
- TOTAL_PERC_IB: Valor numérico bajo "PERC.IN.BR." o "CABA RG987/12".
- TOTAL_PERC_IVA: Valor numérico bajo "PERC.IVA".

Calcula Coeficientes de Prorrateo:
- COEF_IIBB = TOTAL_PERC_IB / TOTAL_NETO_FACTURA
- COEF_PERC_IVA = TOTAL_PERC_IVA / TOTAL_NETO_FACTURA

PASO 2: Procesamiento Línea por Línea
Para cada fila de artículos, extrae y calcula los siguientes campos:

A. Extracción Directa (Columnas de la factura):
- Num de FC: Extraer del encabezado (ej. 9407-06280841).
- Producto: Columna "DESCRIPCION".
- Bultos: Columna "BULTOS".
- Px Lista: Columna "PRECIO UNI".
- Desc Global ($): Columna "DESCUENTO".
- Neto: Columna "SUBTOTAL".
- Imp Int: Columna "IMP.INTERNO".
- % Imp Int: Columna "%II".
- IVA $: Columna "IMP. IVA".

B. Lógica de Unidades (Ps y Q):
- Ps (Pack Size): Analiza el texto de "Producto".
  - Busca patrones como "x12", "12x", "X6", "6X". El número junto a la X es el Ps.
  - Si dice "4X6", multiplica 4*6 = 24.
  - Si no hay patrón, asume 1.
- Q (Total Unidades) = Bultos * Ps.

C. Cálculos de Estructura de Costos:
- Familia: Extraer la primera palabra del producto (ej. "PEPSI", "QUILMES", "ECO").
- Total (Bruto) = Bultos * Px Lista.
- Desc Uni = (Total - Neto) / Bultos.
- Desc % = (Total - Neto) / Total.
- Neto + Imp = Neto + Imp Int.
- IIBB $ (Prorrateo) = Neto * COEF_IIBB.
- Perc IVA $ (Prorrateo) = Neto * COEF_PERC_IVA.
- Final = Neto + Imp Int + IVA $ + IIBB $ + Perc IVA $.
- Pack Final = Final / Bultos.
- Unit = Pack Final / Ps.

SALIDA FINAL
Devolver un JSON con la estructura:
{
  "invoice_number": "<número de factura del encabezado>",
  "invoice_total": <total de la factura>,
  "items": [<lista de objetos con los campos de cada producto>]
}

Cada objeto en "items" debe tener las claves EXACTAS:
["Fecha","Num_de_FC","Producto","Familia","Bultos","Ps","Q","Px_Lista","Desc_Uni","Total","Desc_Global","Desc_Porc","Neto","Imp_Int","Porc_II","Neto_Imp","IVA","IIBB","Perc_IVA","Final","Pack_Final","Unit"]

IMPORTANTE:
- Todos los valores numéricos deben usar punto como separador decimal (ej. 10000.50)
- Los porcentajes deben ser decimales (ej. 0.15 para 15%)
- Si un valor no se puede calcular o no existe, usar null
- NO añadir texto fuera del JSON
- Devolver ÚNICAMENTE el JSON (sin fences de código)
"""
