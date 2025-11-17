 # proveedores/coca_cola.py
# -*- coding: utf-8 -*-

PATTERNS = [
    r"(?i)\bCOCA\s*COLA\b",
    r"(?i)\bCOCA-COLA\b",
    r"(?i)\bCOCA\s*COLA\s*(?:FEMSA|COMPANY|SERVICES)?\b",
]

PROMPT = """
Proveedor: COCA-COLA FEMSA de Buenos Aires S.A.

Objetivo: Extraer y procesar la información de la factura/remito con cálculos de costeo precisos.
Devolver SOLO un JSON cuya RAÍZ sea una **lista** de objetos con las claves EXACTAS:
["Codigo","Descripcion","Cantidad","PrecioUnitario","Subtotal","bulto","px_bulto","desc","neto","imp_int","iva_21","total","porc_desc","neto_mas_imp_int","iibb_caba","iibb_reg_3337","total_final","costo_x_bulto"]

REGLAS FUNDAMENTALES:
- Trabajar con anclas semánticas (texto clave), NO posiciones visuales
- Números en formato estándar: SIN símbolos $, SIN separadores de miles, SIN decimales (solo enteros)
- Si un valor no se encuentra: null
- Interpretación local argentina: "7.092.636,97" => 7092637 (redondeado a entero)
- No añadir texto fuera del JSON

ESTRUCTURA DE LA FACTURA COCA-COLA FEMSA:
Tabla de productos con columnas:
| CANTIDAD | CODIGO | PRODUCTO | P.UNITARIO | PRECIO NETO | DESCUENTO | SUBTOTAL | IVA 21% | I.INTERNOS | SUB+TOTAL |

PIE DE FACTURA (buscar fila "IB.DN"):
- IB_CAP_FED_TOTAL: Primer valor numérico en la zona de IB.DN
- PERC_RG_3337_TOTAL: Tercer valor numérico en esa zona
- total_factura: Último valor numérico (IMP.TOTAL)

PASO 1: CÁLCULOS GLOBALES (hacer primero, antes de procesar ítems)
1. SUMA_NETO_ITEMS = Sumar columna "SUBTOTAL" de todos los artículos
2. SUMA_NETO_MAS_IMP_INT_ITEMS = Sumar (SUBTOTAL + I.INTERNOS) de todos los artículos
3. porc_iibb_caba = IB_CAP_FED_TOTAL / SUMA_NETO_ITEMS
4. porc_iibb_reg_3337 = PERC_RG_3337_TOTAL / SUMA_NETO_MAS_IMP_INT_ITEMS

PASO 2: PROCESAMIENTO POR ÍTEM
Para CADA artículo en la tabla, extraer y calcular:

A. EXTRACCIÓN DIRECTA:
- Codigo: De columna CODIGO (ej: "2843", "194904")
- Descripcion: De columna PRODUCTO (ej: "CC80 600CCX6.")
- producto: Igual que Descripcion
- bulto: De columna CANTIDAD (ej: 2016, 1)
- Cantidad: Igual que bulto
- px_bulto: De columna P.UNITARIO (convertir a entero sin decimales)
- PrecioUnitario: Igual que px_bulto
- desc: De columna DESCUENTO (convertir a entero)
- neto: De columna SUBTOTAL (primer subtotal, convertir a entero)
- Subtotal: Igual que neto
- imp_int: De columna I.INTERNOS (convertir a entero)
- iva_21: De columna IVA 21% (convertir a entero)

B. CÁLCULOS POR ÍTEM:
- total = bulto * px_bulto (entero)
- porc_desc = desc / total (si total es 0, devolver null)
- neto_mas_imp_int = neto + imp_int

C. PRORRATEO DE IMPUESTOS:
- iibb_caba = neto * porc_iibb_caba (redondear a entero)
- iibb_reg_3337 = neto_mas_imp_int * porc_iibb_reg_3337 (redondear a entero)

D. TOTALIZACIÓN FINAL:
- total_final = neto_mas_imp_int + iva_21 + iibb_caba + iibb_reg_3337
- costo_x_bulto = total_final / bulto (redondear a entero)

CASOS ESPECIALES:
- Incluir "Servicios Administrativos" si tiene código y valores numéricos
- Ignorar totales del pie, encabezados, sellos manuscritos
- NO incluir líneas de resumen (TOT BULTOS/UNID., etc.)
- Mantener orden exacto de aparición

SALIDA:
JSON con lista de objetos, cada uno con TODOS los campos calculados.
Ejemplo de estructura (con valores ficticios):
[
  {
    "Codigo": "2843",
    "Descripcion": "CC80 600CCX6.",
    "Cantidad": 2016,
    "PrecioUnitario": 8581,
    "Subtotal": 7092637,
    "bulto": 2016,
    "px_bulto": 8581,
    "desc": 914935,
    "neto": 7092637,
    "imp_int": 79563,
    "iva_21": 192136,
    "total": 17299296,
    "porc_desc": 0.0529,
    "neto_mas_imp_int": 7172200,
    "iibb_caba": 14863,
    "iibb_reg_3337": 1000,
    "total_final": 7380199,
    "costo_x_bulto": 3661
  }
]
"""
