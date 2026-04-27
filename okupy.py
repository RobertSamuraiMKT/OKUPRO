import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.units import cm

st.set_page_config(page_title="OKUPRO v6.0", layout="wide", page_icon="🏠")

# ─── CSS personalizado ───────────────────────────────────────────────────────
st.markdown("""
<style>
.semaforo-verde  { background:#d4edda; color:#155724; padding:4px 10px; border-radius:6px; font-weight:600; font-size:13px; }
.semaforo-naranja{ background:#fff3cd; color:#856404; padding:4px 10px; border-radius:6px; font-weight:600; font-size:13px; }
.semaforo-rojo   { background:#f8d7da; color:#721c24; padding:4px 10px; border-radius:6px; font-weight:600; font-size:13px; }
.semaforo-gris   { background:#e2e3e5; color:#383d41; padding:4px 10px; border-radius:6px; font-weight:600; font-size:13px; }
.metric-card { background:#f8f9fa; border-radius:10px; padding:16px; text-align:center; border:1px solid #dee2e6; }
.metric-label { font-size:13px; color:#6c757d; margin-bottom:4px; }
.metric-value { font-size:26px; font-weight:700; color:#212529; }
</style>
""", unsafe_allow_html=True)

st.title("🏠 OKUPRO v6.0")
st.subheader("Analizador de carteras inmobiliarias · Pisos ocupados, bancarios, SAREB")

# ─── 1. PRECIOS DE MERCADO BASE ───────────────────────────────────────────────
PRECIOS_BASE = {
    "Barcelona": {"venta": 5000, "alquiler": 18.0},
    "Hospitalet de Llobregat": {"venta": 2800, "alquiler": 17.0},
    "Badalona": {"venta": 2400, "alquiler": 15.0},
    "Sabadell": {"venta": 2200, "alquiler": 12.0},
    "Mollet del Vallès": {"venta": 2100, "alquiler": 11.5},
    "Terrassa": {"venta": 2100, "alquiler": 11.5},
    "Mataró": {"venta": 2400, "alquiler": 13.0},
    "Santa Coloma de Gramenet": {"venta": 2300, "alquiler": 13.5},
    "Rubí": {"venta": 2300, "alquiler": 12.0},
    "Cornellà de Llobregat": {"venta": 2600, "alquiler": 14.0},
    "Sant Boi de Llobregat": {"venta": 2400, "alquiler": 13.0},
    "Castelldefels": {"venta": 3000, "alquiler": 16.0},
    "Granollers": {"venta": 2400, "alquiler": 12.0},
    "Berga": {"venta": 1300, "alquiler": 8.0},
    "Pineda de Mar": {"venta": 2000, "alquiler": 11.0},
    "Manresa": {"venta": 1400, "alquiler": 9.0},
    "Ripollet": {"venta": 2100, "alquiler": 12.0},
    "Olesa de Bonesvalls": {"venta": 1800, "alquiler": 10.0},
    "Olèrdola": {"venta": 1700, "alquiler": 9.5},
    "Manlleu": {"venta": 1200, "alquiler": 8.0},
}

# ─── 2. MAPA CP → BARRIO ──────────────────────────────────────────────────────
CP_BARRIOS = {
    "08001": "EL RAVAL", "08002": "GÒTIC", "08003": "LA BARCELONETA",
    "08004": "SANTS-MONTJUÏC", "08005": "SANT MARTÍ", "08006": "GRÀCIA",
    "08007": "L'AMPLE", "08008": "LES CORTS", "08009": "LA DRETA DE L'EIXAMPLE",
    "08010": "LA SAGRERA", "08011": "SANT ANTONI", "08012": "VALLVIDRERA",
    "08013": "CLOT", "08014": "HOSTAFRANCS", "08015": "LA BORDETA",
    "08016": "NOU BARRIS", "08017": "SARRIÀ", "08018": "EL POBLENOU",
    "08019": "EL BESÒS", "08020": "SANT ANDREU", "08021": "LES CORTS",
    "08022": "LA TEIXONERA", "08023": "VALLVIDRERA", "08024": "EL CARMEL",
    "08025": "LA SAGRADA FAMÍLIA", "08026": "EL GUINARDÓ", "08027": "SANT ANDREU",
    "08028": "SANTS", "08029": "LES CORTS", "08030": "SANT ANDREU",
    "08031": "SANT ANDREU", "08032": "NOU BARRIS", "08033": "NOU BARRIS",
    "08034": "LES CORTS", "08035": "HORTA", "08036": "L'AMPLE",
    "08037": "LA DRETA DE L'EIXAMPLE", "08038": "SANTS", "08039": "SANTS",
    "08040": "SANT MARTÍ", "08041": "SANT MARTÍ", "08042": "SANT MARTÍ",
    "08901": "CENTRE", "08902": "SANFELIU", "08903": "COLLBLANC",
    "08904": "LA TORRASSA", "08905": "LA FLORIDA", "08906": "PUBILLA CASAS",
    "08907": "BELLVITGE", "08908": "GRAN VIA",
    "08911": "CENTRE", "08912": "LA SALUT", "08913": "LLEFIÀ",
    "08914": "SANT ROC", "08915": "SANT CRIST", "08916": "MORA",
    "08917": "SANT ADRIÀ", "08918": "LA SALUT - ALFONSO XII",
    "08921": "CENTRE", "08922": "EL RAVAL", "08923": "SANTA ROSA", "08924": "SANT JORDI",
    "08191": "CENTRE", "08192": "CAN BOSCH",
    "08221": "CENTRE", "08222": "CAN BOSCH", "08223": "LA PAU",
    "08224": "CA N'ANGEL", "08225": "MONTPELLIER", "08226": "SANT PERE",
    "08201": "CENTRE", "08202": "CREU DE BARBERÀ", "08203": "CAN RULL",
    "08204": "GRÀCIA", "08205": "EL VAPOR", "08206": "LA SALUT",
    "08207": "SOL I PADRIS", "08208": "CAN FEU",
}

BARRIOS_RIESGO_ALTO = [
    "FLORIDA", "LA SALUT", "ALFONSO XII", "CIUTAT VELLA", "RAVAL",
    "EL BESÒS", "LA MINA", "SANT ROC", "LLEFIÀ", "COLLBLANC",
    "PUBILLA CASAS", "LA TORRASSA", "CAN RULL", "CAN BOSCH", "NOU BARRIS",
    "BELLVITGE", "SANFELIU",
]

# Coste estimado de desahucio por zona de riesgo (€ y meses)
COSTE_DESAHUCIO = {
    "BAJA":   {"coste": 3000,  "meses": 8},
    "MEDIA":  {"coste": 6000,  "meses": 14},
    "ALTA":   {"coste": 10000, "meses": 22},
    "REVISAR":{"coste": 6000,  "meses": 14},
}

# ─── 3. HELPERS ───────────────────────────────────────────────────────────────
def encontrar_columna(df, posibles):
    for col in df.columns:
        for nombre in posibles:
            if nombre.lower() in col.lower().strip():
                return col
    return None

def calcular_descuento(precio):
    if precio < 70000:   return 0.25
    elif precio < 150000: return 0.225
    elif precio < 200000: return 0.20
    else:                return 0.19

def calcular_precio_ofertado(precio):
    return precio * (1 - calcular_descuento(precio))

def obtener_tipo_inmueble(superficie):
    return "PISO" if superficie < 150 else "CASA"

def obtener_precios_mercado(poblacion, tipo, superficie, precios_usuario=None):
    fuente = precios_usuario if precios_usuario else PRECIOS_BASE
    base = fuente.get(poblacion, {"venta": 2000, "alquiler": 12.0})
    if tipo == "PISO":
        return {"venta": base["venta"], "alquiler": base["alquiler"]}
    else:
        fv = 0.5 if superficie > 500 else 0.6 if superficie > 300 else 0.7
        fa = 0.6 if superficie > 500 else 0.7 if superficie > 300 else 0.8
        return {"venta": base["venta"] * fv, "alquiler": base["alquiler"] * fa}

def extraer_barrio(direccion, codigo_postal):
    cp = str(codigo_postal).strip()
    if cp in CP_BARRIOS:
        return CP_BARRIOS[cp], "CÓDIGO POSTAL"
    if isinstance(direccion, str):
        du = direccion.upper()
        for b in BARRIOS_RIESGO_ALTO:
            if b in du:
                return b, "DIRECCIÓN"
    return "default", "DEFAULT"

@st.cache_data
def cargar_vulnerabilidad(ruta="1_0_BD_Municipios_1991_2001_2006_2011.xlsx"):
    try:
        df = pd.read_excel(ruta, sheet_name="BD")
        df.columns = df.columns.str.strip()
        vuln = {}
        for _, row in df.iterrows():
            mun = str(row.get("MUNICIPIO", "")).upper().strip()
            if not mun or mun == "NAN":
                continue
            v = row.get("PORPOB_BBVV_11", 0)
            vuln[mun] = float(v) if not pd.isna(v) else 0.0
        return vuln
    except:
        return {}

def obtener_riesgo(municipio, direccion, codigo_postal, vuln_dict):
    mun_up = municipio.upper().strip()
    barrio, origen_barrio = extraer_barrio(direccion, codigo_postal)
    porc = vuln_dict.get(mun_up, None)

    if porc is None:
        return "REVISAR", -0.25, "⚠️ Sin datos oficiales — revisar manualmente", 10.0, "DEFAULT", barrio, origen_barrio

    if barrio.upper() in BARRIOS_RIESGO_ALTO:
        return "ALTA", -0.5, f"🔴 Barrio vulnerable detectado: {barrio}", porc, "MITMA", barrio, origen_barrio
    elif porc > 20:
        return "ALTA", -0.5, f"🔴 {porc:.1f}% población vulnerable — Solo para expertos", porc, "MITMA", barrio, origen_barrio
    elif porc > 10:
        return "MEDIA", -0.25, f"🟡 {porc:.1f}% población vulnerable — Evaluar con precaución", porc, "MITMA", barrio, origen_barrio
    else:
        return "BAJA", 0, f"🟢 Zona consolidada ({porc:.1f}% vulnerable)", porc, "MITMA", barrio, origen_barrio

def semaforo_html(nivel):
    colores = {
        "BAJA":    ("semaforo-verde",   "🟢 BAJA"),
        "MEDIA":   ("semaforo-naranja", "🟡 MEDIA"),
        "ALTA":    ("semaforo-rojo",    "🔴 ALTA"),
        "REVISAR": ("semaforo-gris",    "⚪ REVISAR"),
    }
    cls, texto = colores.get(nivel, ("semaforo-gris", nivel))
    return f'<span class="{cls}">{texto}</span>'

# ─── 4. SCORING MULTIDIMENSIONAL ──────────────────────────────────────────────
def calcular_score(roi_flip, rent_alquiler, precio_oferta, precio_mercado, nivel_riesgo,
                   w_roi, w_alq, w_mercado, w_riesgo):
    """Scoring 0-100 con pesos configurables"""
    # Normalización simple por percentil dentro de rangos razonables
    score_roi    = min(100, max(0, roi_flip / 0.5))          # 50% ROI = 100 pts
    score_alq    = min(100, max(0, rent_alquiler / 0.15))    # 15% rent bruta = 100 pts
    score_mercado = min(100, max(0, (1 - precio_oferta / max(precio_mercado, 1)) * 200))
    riesgo_pts   = {"BAJA": 100, "MEDIA": 50, "ALTA": 0, "REVISAR": 40}.get(nivel_riesgo, 40)

    total = (score_roi * w_roi + score_alq * w_alq +
             score_mercado * w_mercado + riesgo_pts * w_riesgo)
    return round(min(100, max(0, total)), 1)

# ─── 5. CASHFLOW ──────────────────────────────────────────────────────────────
def calcular_cashflow(precio_oferta, alquiler_mensual, vacancia_pct,
                      ibi_anual, comunidad_mensual, seguro_anual,
                      reforma_total, coste_desahucio, nivel_riesgo):
    ingresos_anuales = alquiler_mensual * 12 * (1 - vacancia_pct / 100)
    gastos_anuales = ibi_anual + comunidad_mensual * 12 + seguro_anual
    coste_des = COSTE_DESAHUCIO.get(nivel_riesgo, COSTE_DESAHUCIO["MEDIA"])["coste"] if coste_desahucio else 0
    inversion_total = precio_oferta + reforma_total + coste_des
    cashflow_neto_anual = ingresos_anuales - gastos_anuales
    rentabilidad_neta = (cashflow_neto_anual / inversion_total * 100) if inversion_total > 0 else 0
    payback = (inversion_total / cashflow_neto_anual) if cashflow_neto_anual > 0 else 999
    return {
        "ingresos_anuales": round(ingresos_anuales, 0),
        "gastos_anuales": round(gastos_anuales, 0),
        "cashflow_neto_anual": round(cashflow_neto_anual, 0),
        "cashflow_mensual": round(cashflow_neto_anual / 12, 0),
        "rentabilidad_neta": round(rentabilidad_neta, 2),
        "payback_anios": round(payback, 1),
        "inversion_total": round(inversion_total, 0),
        "coste_desahucio": coste_des,
    }

# ─── 6. PROCESADO EXCEL ───────────────────────────────────────────────────────
def validar_datos(df):
    alertas = []
    # Duplicados
    if df.duplicated().sum() > 0:
        alertas.append(f"⚠️ **{df.duplicated().sum()} filas duplicadas exactas** detectadas")

    col_precio = encontrar_columna(df, ["pvp", "precio", "importe", "valor", "euros"])
    col_sup = encontrar_columna(df, ["superficie", "metros", "m2", "construidos"])

    if col_precio:
        precios = pd.to_numeric(df[col_precio], errors="coerce").dropna()
        if len(precios) > 5:
            mean, std = precios.mean(), precios.std()
            outliers = ((precios - mean).abs() > 3 * std).sum()
            if outliers > 0:
                alertas.append(f"⚠️ **{outliers} inmuebles con precio fuera de rango** (>3σ) — posibles errores")
        ceros_precio = (pd.to_numeric(df[col_precio], errors="coerce") <= 0).sum()
        if ceros_precio > 0:
            alertas.append(f"⚠️ **{ceros_precio} filas con precio 0 o negativo** — serán ignoradas")

    if col_sup:
        ceros_sup = (pd.to_numeric(df[col_sup], errors="coerce") <= 0).sum()
        if ceros_sup > 0:
            alertas.append(f"⚠️ **{ceros_sup} filas con superficie 0** — serán ignoradas")

    col_mun = encontrar_columna(df, ["municipio", "poblacion", "población", "ciudad", "localidad"])
    if col_mun:
        nulos_mun = df[col_mun].isna().sum() + (df[col_mun].astype(str) == "nan").sum()
        if nulos_mun > 0:
            alertas.append(f"⚠️ **{nulos_mun} filas sin municipio** — serán ignoradas")

    return alertas

def procesar_excel(df, tipo_filtro, precios_usuario, vuln_dict,
                   vacancia_pct, reforma_m2, incluir_desahucio, ibi_anual, comunidad_mensual, seguro_anual,
                   w_roi, w_alq, w_mercado, w_riesgo):

    col_id   = encontrar_columna(df, ["id", "prinex", "expediente", "inmueble"])
    col_mun  = encontrar_columna(df, ["municipio", "poblacion", "población", "ciudad", "localidad"])
    col_dir  = encontrar_columna(df, ["direccion", "domicilio", "calle", "address"])
    col_cp   = encontrar_columna(df, ["postal", "cp", "codigo postal", "código postal"])
    col_sup  = encontrar_columna(df, ["superficie", "metros", "m2", "construidos"])
    col_pre  = encontrar_columna(df, ["pvp", "precio", "importe", "valor", "euros"])

    if not col_mun:
        st.error(f"❌ No se encontró columna de municipio. Columnas disponibles: {', '.join(df.columns)}")
        return pd.DataFrame()
    if not col_pre:
        st.error("❌ No se encontró columna de precio.")
        return pd.DataFrame()

    resultados = []
    for _, row in df.iterrows():
        try:
            municipio     = str(row.get(col_mun, "")).strip()
            precio_orig   = float(row.get(col_pre, 0)) if pd.notna(row.get(col_pre)) else 0
            superficie    = float(row.get(col_sup, 0)) if col_sup and pd.notna(row.get(col_sup)) else 0
            direccion     = str(row.get(col_dir, "")) if col_dir else ""
            cp            = str(row.get(col_cp, "")).strip() if col_cp else ""
            id_inmueble   = str(row.get(col_id, "")) if col_id else ""

            if superficie <= 0 or precio_orig <= 0 or not municipio or municipio == "nan":
                continue

            tipo = obtener_tipo_inmueble(superficie)
            if tipo_filtro == "Solo pisos" and tipo != "PISO":
                continue
            if tipo_filtro == "Solo casas" and tipo != "CASA":
                continue

            precio_oferta = calcular_precio_ofertado(precio_orig)
            descuento_pct = round(calcular_descuento(precio_orig) * 100, 1)

            mercado = obtener_precios_mercado(municipio, tipo, superficie, precios_usuario)
            precio_mercado_total = superficie * mercado["venta"]
            alquiler_mensual_bruto = superficie * mercado["alquiler"]
            roi_flip = (precio_mercado_total - precio_oferta) / precio_oferta if precio_oferta > 0 else 0
            rent_bruta = (alquiler_mensual_bruto * 12) / precio_oferta if precio_oferta > 0 else 0

            nivel_riesgo, penaliz, recomendacion, porc_vuln, origen_riesgo, barrio, origen_barrio = obtener_riesgo(
                municipio, direccion, cp, vuln_dict
            )

            reforma_total = superficie * reforma_m2
            cf = calcular_cashflow(
                precio_oferta, alquiler_mensual_bruto, vacancia_pct,
                ibi_anual, comunidad_mensual, seguro_anual,
                reforma_total, incluir_desahucio, nivel_riesgo
            )

            score = calcular_score(
                roi_flip, rent_bruta, precio_oferta, precio_mercado_total,
                nivel_riesgo, w_roi, w_alq, w_mercado, w_riesgo
            )

            meses_desahucio = COSTE_DESAHUCIO.get(nivel_riesgo, {}).get("meses", 14) if incluir_desahucio else 0

            dir_corta = (direccion[:45] + "...") if len(str(direccion)) > 45 else direccion

            resultados.append({
                "ID": id_inmueble,
                "Municipio": municipio,
                "Dirección": dir_corta,
                "Barrio": barrio,
                "Tipo": tipo,
                "Superficie (m²)": superficie,
                "Precio original (€)": precio_orig,
                "Descuento %": descuento_pct,
                "Precio oferta (€)": round(precio_oferta, 0),
                "Precio mercado (€)": round(precio_mercado_total, 0),
                "ROI Flip (%)": round(roi_flip * 100, 1),
                "Rent. bruta (%)": round(rent_bruta * 100, 1),
                "Cashflow mensual (€)": cf["cashflow_mensual"],
                "Rent. neta (%)": cf["rentabilidad_neta"],
                "Payback (años)": cf["payback_anios"],
                "Inversión total (€)": cf["inversion_total"],
                "Riesgo zona": nivel_riesgo,
                "% Vulnerable": round(porc_vuln, 1),
                "Semáforo": nivel_riesgo,
                "Recomendación": recomendacion,
                "Meses desahucio est.": meses_desahucio,
                "Score OKUPRO": score,
                # Guardamos datos extra para PDF
                "_alquiler_bruto_mensual": round(alquiler_mensual_bruto, 0),
                "_gastos_anuales": cf["gastos_anuales"],
                "_ingresos_anuales": cf["ingresos_anuales"],
                "_coste_desahucio": cf["coste_desahucio"],
                "_reforma_total": round(reforma_total, 0),
            })
        except:
            continue

    df_res = pd.DataFrame(resultados)
    if len(df_res) > 0:
        df_res = df_res.sort_values("Score OKUPRO", ascending=False).reset_index(drop=True)
    return df_res

# ─── 7. GENERADOR DE PDF ──────────────────────────────────────────────────────
def generar_pdf_inmueble(row):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    # Título
    title_style = ParagraphStyle("title", fontSize=18, textColor=colors.HexColor("#1a1a2e"),
                                  spaceAfter=6, fontName="Helvetica-Bold")
    sub_style   = ParagraphStyle("sub", fontSize=11, textColor=colors.HexColor("#6c757d"), spaceAfter=16)
    label_style = ParagraphStyle("label", fontSize=9,  textColor=colors.HexColor("#6c757d"), fontName="Helvetica")
    value_style = ParagraphStyle("value", fontSize=12, textColor=colors.HexColor("#212529"), fontName="Helvetica-Bold")
    body_style  = ParagraphStyle("body", fontSize=10, textColor=colors.HexColor("#343a40"), leading=14)

    story.append(Paragraph("🏠 OKUPRO v6.0 — Ficha de inmueble", title_style))
    story.append(Paragraph(f"{row.get('Dirección','N/A')} · {row.get('Municipio','N/A')} · {row.get('Barrio','N/A')}", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dee2e6")))
    story.append(Spacer(1, 0.4*cm))

    # Semáforo de riesgo
    riesgo = row.get("Riesgo zona", "REVISAR")
    colores_riesgo = {"BAJA": "#28a745", "MEDIA": "#ffc107", "ALTA": "#dc3545", "REVISAR": "#6c757d"}
    color_r = colores_riesgo.get(riesgo, "#6c757d")
    riesgo_style = ParagraphStyle("riesgo", fontSize=13, textColor=colors.HexColor(color_r),
                                   fontName="Helvetica-Bold", spaceAfter=12)
    iconos = {"BAJA": "● ZONA DE RIESGO BAJO", "MEDIA": "● ZONA DE RIESGO MEDIO",
              "ALTA": "● ZONA DE RIESGO ALTO", "REVISAR": "● ZONA SIN DATOS — REVISAR"}
    story.append(Paragraph(iconos.get(riesgo, riesgo), riesgo_style))
    story.append(Paragraph(str(row.get("Recomendación", "")), body_style))
    story.append(Spacer(1, 0.4*cm))

    # Tabla métricas principales
    def fila(label, val):
        return [Paragraph(label, label_style), Paragraph(str(val), value_style)]

    score = row.get("Score OKUPRO", 0)
    data_tabla = [
        ["", ""],
        fila("Tipo de inmueble", f"{row.get('Tipo','N/A')} · {row.get('Superficie (m²)',0):.0f} m²"),
        fila("Precio original", f"€ {row.get('Precio original (€)',0):,.0f}"),
        fila("Precio oferta (con descuento)", f"€ {row.get('Precio oferta (€)',0):,.0f}  ({row.get('Descuento %',0):.1f}% dto.)"),
        fila("Precio de mercado estimado", f"€ {row.get('Precio mercado (€)',0):,.0f}"),
        fila("ROI Flip estimado", f"{row.get('ROI Flip (%)',0):.1f}%"),
        fila("Rentabilidad bruta (alquiler)", f"{row.get('Rent. bruta (%)',0):.1f}%"),
        fila("Rentabilidad neta (alquiler)", f"{row.get('Rent. neta (%)',0):.2f}%"),
        fila("Cashflow mensual neto", f"€ {row.get('Cashflow mensual (€)',0):,.0f}"),
        fila("Payback estimado", f"{row.get('Payback (años)',0):.1f} años"),
        fila("Inversión total estimada", f"€ {row.get('Inversión total (€)',0):,.0f}"),
        fila("Coste desahucio estimado", f"€ {row.get('_coste_desahucio',0):,.0f}  (~{row.get('Meses desahucio est.',0)} meses)"),
        fila("Reforma estimada", f"€ {row.get('_reforma_total',0):,.0f}"),
        fila("Score OKUPRO", f"{score:.0f} / 100"),
    ]

    tabla = Table(data_tabla, colWidths=[7*cm, 9*cm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f8f9fa")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f8f9fa")]),
        ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#dee2e6")),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(tabla)
    story.append(Spacer(1, 0.5*cm))

    # Footer
    footer_style = ParagraphStyle("footer", fontSize=8, textColor=colors.HexColor("#adb5bd"),
                                   alignment=1)
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dee2e6")))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("Documento generado por OKUPRO v6.0 · Uso exclusivamente informativo · No constituye asesoramiento financiero", footer_style))

    doc.build(story)
    buf.seek(0)
    return buf

# ─── 8. SIDEBAR ───────────────────────────────────────────────────────────────
st.sidebar.header("⚙️ Configuración")

tipo_filtro = st.sidebar.radio("Tipo de inmueble:", ["Todos", "Solo pisos", "Solo casas"])
top_n = st.sidebar.slider("Top resultados a mostrar", 10, 100, 25, step=5)

st.sidebar.markdown("---")
st.sidebar.subheader("💶 Parámetros de cashflow")
vacancia_pct       = st.sidebar.slider("Vacancia estimada (%)", 0, 25, 8)
reforma_m2         = st.sidebar.slider("Coste reforma (€/m²)", 0, 500, 80)
ibi_anual          = st.sidebar.number_input("IBI anual (€)", 0, 5000, 400)
comunidad_mensual  = st.sidebar.number_input("Comunidad mensual (€)", 0, 500, 60)
seguro_anual       = st.sidebar.number_input("Seguro anual (€)", 0, 2000, 250)
incluir_desahucio  = st.sidebar.checkbox("Incluir coste de desahucio", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ Pesos del Score OKUPRO")
st.sidebar.caption("Deben sumar 1.0")
w_roi     = st.sidebar.slider("Peso ROI Flip",         0.0, 1.0, 0.30, 0.05)
w_alq     = st.sidebar.slider("Peso Rent. alquiler",   0.0, 1.0, 0.25, 0.05)
w_mercado = st.sidebar.slider("Peso precio vs mercado",0.0, 1.0, 0.20, 0.05)
w_riesgo  = st.sidebar.slider("Peso zona de riesgo",   0.0, 1.0, 0.25, 0.05)
total_w = round(w_roi + w_alq + w_mercado + w_riesgo, 2)
if abs(total_w - 1.0) > 0.01:
    st.sidebar.warning(f"⚠️ Los pesos suman {total_w:.2f} — deberían sumar 1.0")

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Precios de mercado personalizados")
archivo_precios = st.sidebar.file_uploader("Excel con precios (opcional)", type=["xlsx","xls"],
                                            help="Columnas: Municipio, PrecioVenta (€/m²), PrecioAlquiler (€/m²)")
precios_usuario = None
if archivo_precios:
    try:
        df_precios = pd.read_excel(archivo_precios)
        precios_usuario = {}
        for _, r in df_precios.iterrows():
            mun = str(r.iloc[0]).strip()
            precios_usuario[mun] = {"venta": float(r.iloc[1]), "alquiler": float(r.iloc[2])}
        st.sidebar.success(f"✅ {len(precios_usuario)} municipios cargados")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filtros de alerta")
umbral_roi  = st.sidebar.slider("ROI Flip mínimo (%)", 0, 80, 0)
umbral_rent = st.sidebar.slider("Rent. bruta mínima (%)", 0, 20, 0)
solo_riesgo_bajo  = st.sidebar.checkbox("Solo riesgo BAJO")
solo_revisar      = st.sidebar.checkbox("Solo requieren revisión manual")

# ─── 9. CARGA PRINCIPAL ───────────────────────────────────────────────────────
archivo = st.file_uploader("📂 Sube tu archivo Excel con la cartera", type=["xlsx", "xls"])
vuln_dict = cargar_vulnerabilidad()

if archivo is not None:
    try:
        df_raw = pd.read_excel(archivo)
        st.success(f"✅ Archivo cargado: {len(df_raw)} filas")

        # Validación de calidad
        alertas = validar_datos(df_raw)
        if alertas:
            with st.expander("⚠️ Informe de calidad de datos", expanded=True):
                for a in alertas:
                    st.markdown(a)

        # Columnas detectadas
        with st.expander("🔍 Columnas detectadas"):
            cols_check = {
                "ID": ["id","prinex","expediente","inmueble"],
                "Municipio": ["municipio","poblacion","población","ciudad","localidad"],
                "Dirección": ["direccion","domicilio","calle","address"],
                "CP": ["postal","cp","codigo postal","código postal"],
                "Superficie": ["superficie","metros","m2","construidos"],
                "Precio": ["pvp","precio","importe","valor","euros"],
            }
            for nombre, posibles in cols_check.items():
                col = encontrar_columna(df_raw, posibles)
                st.write(f"**{nombre}:** {col or '❌ No encontrada'}")

        with st.spinner("⏳ Analizando cartera..."):
            df_res = procesar_excel(
                df_raw, tipo_filtro, precios_usuario, vuln_dict,
                vacancia_pct, reforma_m2, incluir_desahucio,
                ibi_anual, comunidad_mensual, seguro_anual,
                w_roi, w_alq, w_mercado, w_riesgo
            )

        if len(df_res) == 0:
            st.warning("⚠️ No se encontraron inmuebles con los filtros seleccionados.")
            st.stop()

        # Aplicar filtros de alerta
        df_filtrado = df_res.copy()
        if umbral_roi > 0:
            df_filtrado = df_filtrado[df_filtrado["ROI Flip (%)"] >= umbral_roi]
        if umbral_rent > 0:
            df_filtrado = df_filtrado[df_filtrado["Rent. bruta (%)"] >= umbral_rent]
        if solo_riesgo_bajo:
            df_filtrado = df_filtrado[df_filtrado["Riesgo zona"] == "BAJA"]
        if solo_revisar:
            df_filtrado = df_filtrado[df_filtrado["Riesgo zona"] == "REVISAR"]

        # ── MÉTRICAS ──────────────────────────────────────────────────────────
        st.subheader("📊 Resumen de la cartera")
        cols = st.columns(6)
        cols[0].metric("Total analizados", len(df_filtrado))
        cols[1].metric("🟢 Riesgo BAJO",  (df_filtrado["Riesgo zona"]=="BAJA").sum())
        cols[2].metric("🟡 Riesgo MEDIO", (df_filtrado["Riesgo zona"]=="MEDIA").sum())
        cols[3].metric("🔴 Riesgo ALTO",  (df_filtrado["Riesgo zona"]=="ALTA").sum())
        cols[4].metric("ROI Flip medio",  f"{df_filtrado['ROI Flip (%)'].mean():.1f}%")
        cols[5].metric("Score medio",     f"{df_filtrado['Score OKUPRO'].mean():.0f}/100")

        # ── SEMÁFORO VISUAL ───────────────────────────────────────────────────
        st.subheader(f"🏆 Top {min(top_n, len(df_filtrado))} Oportunidades")

        cols_mostrar = [
            "Score OKUPRO", "ID", "Municipio", "Barrio", "Tipo",
            "Superficie (m²)", "Precio oferta (€)", "Precio mercado (€)",
            "ROI Flip (%)", "Rent. bruta (%)", "Rent. neta (%)",
            "Cashflow mensual (€)", "Payback (años)", "Inversión total (€)",
            "Riesgo zona", "% Vulnerable", "Recomendación"
        ]
        df_display = df_filtrado[cols_mostrar].head(top_n).copy()

        def color_score(val):
            if val >= 70: return "background-color: #d4edda; color: #155724"
            elif val >= 40: return "background-color: #fff3cd; color: #856404"
            else: return "background-color: #f8d7da; color: #721c24"

        def color_riesgo(val):
            m = {"BAJA": "background-color:#d4edda;color:#155724",
                 "MEDIA": "background-color:#fff3cd;color:#856404",
                 "ALTA": "background-color:#f8d7da;color:#721c24",
                 "REVISAR": "background-color:#e2e3e5;color:#383d41"}
            return m.get(val, "")

        styled = (df_display.style
          .map(color_score, subset=["Score OKUPRO"])
          .map(color_riesgo, subset=["Riesgo zona"])
                  .format({
                      "Precio oferta (€)": "€ {:,.0f}",
                      "Precio mercado (€)": "€ {:,.0f}",
                      "Inversión total (€)": "€ {:,.0f}",
                      "Cashflow mensual (€)": "€ {:,.0f}",
                      "ROI Flip (%)": "{:.1f}%",
                      "Rent. bruta (%)": "{:.1f}%",
                      "Rent. neta (%)": "{:.2f}%",
                  }))
        st.dataframe(styled, use_container_width=True, height=420)

        # ── PDF POR INMUEBLE ──────────────────────────────────────────────────
        st.subheader("📄 Informe PDF por inmueble")
        ids_disponibles = df_filtrado["ID"].astype(str).tolist()
        id_sel = st.selectbox("Selecciona un inmueble por ID", ids_disponibles)
        if id_sel:
            row_sel = df_filtrado[df_filtrado["ID"].astype(str) == id_sel].iloc[0]
            col1, col2 = st.columns([2, 1])
            with col1:
                nivel = row_sel["Riesgo zona"]
                st.markdown(f"**Semáforo de zona:** {semaforo_html(nivel)}", unsafe_allow_html=True)
                st.markdown(f"**Recomendación:** {row_sel['Recomendación']}")
                st.markdown(f"**Score OKUPRO:** `{row_sel['Score OKUPRO']:.0f} / 100`")
                st.markdown(f"**Cashflow mensual:** `€ {row_sel['Cashflow mensual (€)']:,.0f}`")
                st.markdown(f"**Payback:** `{row_sel['Payback (años)']:.1f} años`")
            with col2:
                pdf_buf = generar_pdf_inmueble(row_sel)
                st.download_button(
                    "📥 Descargar PDF ficha",
                    pdf_buf,
                    file_name=f"OKUPRO_{id_sel}.pdf",
                    mime="application/pdf"
                )

        # ── GRÁFICOS PLOTLY ───────────────────────────────────────────────────
        st.subheader("📈 Análisis visual interactivo")
        tab1, tab2, tab3, tab4 = st.tabs(["ROI vs Riesgo", "Cashflow", "Municipios", "Distribución Score"])

        with tab1:
            fig1 = px.scatter(
                df_filtrado.head(top_n),
                x="ROI Flip (%)", y="Rent. neta (%)",
                color="Riesgo zona",
                color_discrete_map={"BAJA":"#28a745","MEDIA":"#ffc107","ALTA":"#dc3545","REVISAR":"#6c757d"},
                size="Superficie (m²)", hover_data=["ID","Municipio","Barrio","Score OKUPRO"],
                title="ROI Flip vs Rentabilidad neta (tamaño = superficie)",
                labels={"ROI Flip (%)": "ROI Flip (%)", "Rent. neta (%)": "Rentabilidad neta (%)"}
            )
            st.plotly_chart(fig1, use_container_width=True)

        with tab2:
            fig2 = px.bar(
                df_filtrado.head(top_n).sort_values("Cashflow mensual (€)", ascending=True),
                x="Cashflow mensual (€)", y="ID",
                orientation="h",
                color="Riesgo zona",
                color_discrete_map={"BAJA":"#28a745","MEDIA":"#ffc107","ALTA":"#dc3545","REVISAR":"#6c757d"},
                title="Cashflow mensual neto por inmueble",
                hover_data=["Municipio","Score OKUPRO","Payback (años)"]
            )
            st.plotly_chart(fig2, use_container_width=True)

        with tab3:
            muni_stats = (df_filtrado.groupby("Municipio")
                          .agg(n=("Score OKUPRO","count"),
                               score_medio=("Score OKUPRO","mean"),
                               roi_medio=("ROI Flip (%)","mean"))
                          .reset_index()
                          .sort_values("score_medio", ascending=False)
                          .head(15))
            fig3 = px.bar(muni_stats, x="Municipio", y="score_medio",
                          color="n", title="Score medio por municipio (Top 15)",
                          labels={"score_medio":"Score medio OKUPRO","n":"Nº inmuebles"},
                          color_continuous_scale="Greens")
            fig3.update_xaxes(tickangle=45)
            st.plotly_chart(fig3, use_container_width=True)

        with tab4:
            fig4 = px.histogram(df_filtrado, x="Score OKUPRO", nbins=20,
                                color_discrete_sequence=["#4a90d9"],
                                title="Distribución del Score OKUPRO")
            fig4.add_vline(x=df_filtrado["Score OKUPRO"].mean(), line_dash="dash",
                           annotation_text="Media", line_color="red")
            st.plotly_chart(fig4, use_container_width=True)

        # ── DESCARGA EXCEL ────────────────────────────────────────────────────
        st.subheader("📥 Exportar resultados")
        cols_export = [c for c in df_filtrado.columns if not c.startswith("_")]
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_filtrado[cols_export].to_excel(writer, index=False, sheet_name="OKUPRO_Resultados")
        st.download_button("📥 Descargar Excel completo", output.getvalue(), "okupro_v6_resultados.xlsx")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
else:
    st.info("📂 Sube un archivo Excel para comenzar el análisis")
    with st.expander("ℹ️ Columnas esperadas en el Excel"):
        st.markdown("""
        | Columna | Nombres aceptados |
        |---------|------------------|
        | Identificador | id, prinex, expediente, inmueble |
        | Municipio | municipio, poblacion, población, ciudad, localidad |
        | Dirección | direccion, domicilio, calle, address |
        | Código Postal | postal, cp, codigo postal, código postal |
        | Superficie | superficie, metros, m2, construidos |
        | Precio | pvp, precio, importe, valor, euros |
        """)

st.markdown("---")
st.caption("OKUPRO v6.0 · Scoring multidimensional · Cashflow real · Semáforo de zonas · PDF por inmueble")
