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

# ─── IMPORTAR EL NUEVO MOTOR DE NORMALIZACIÓN ──────────────────────
from normalizador import (
    normalizar_texto,
    normalizar_municipio,
    normalizar_tipo_inmueble,
    encontrar_columna_inteligente
)

st.set_page_config(page_title="OKUPRO v7.1", layout="wide", page_icon="🏠")

# ─── CSS personalizado ───────────────────────────────────────────────
st.markdown("""
<style>
.semaforo-verde  { background:#d4edda; color:#155724; padding:4px 10px; border-radius:6px; font-weight:600; font-size:13px; }
.semaforo-naranja{ background:#fff3cd; color:#856404; padding:4px 10px; border-radius:6px; font-weight:600; font-size:13px; }
.semaforo-rojo   { background:#f8d7da; color:#721c24; padding:4px 10px; border-radius:6px; font-weight:600; font-size:13px; }
.semaforo-gris   { background:#e2e3e5; color:#383d41; padding:4px 10px; border-radius:6px; font-weight:600; font-size:13px; }
.metric-card  { background:#f8f9fa; border-radius:10px; padding:16px; text-align:center; border:1px solid #dee2e6; }
.metric-label { font-size:13px; color:#6c757d; margin-bottom:4px; }
.metric-value { font-size:26px; font-weight:700; color:#212529; }
.npl-badge    { background:#1a1a2e; color:#e8d5a3; padding:4px 12px; border-radius:6px; font-weight:700; font-size:13px; }
.pl-badge     { background:#17a2b8; color:white; padding:4px 12px; border-radius:6px; font-weight:700; font-size:13px; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# DATOS COMPARTIDOS
# ═══════════════════════════════════════════════════════════════════════

PRECIOS_BASE = {
    "BARCELONA": {"venta": 5000, "alquiler": 18.0},
    "L' HOSPITALET DE LLOBREGAT": {"venta": 2800, "alquiler": 17.0},
    "HOSPITALET DE LLOBREGAT": {"venta": 2800, "alquiler": 17.0},
    "BADALONA": {"venta": 2400, "alquiler": 15.0},
    "SABADELL": {"venta": 2200, "alquiler": 12.0},
    "MOLLET DEL VALLÈS": {"venta": 2100, "alquiler": 11.5},
    "TERRASSA": {"venta": 2100, "alquiler": 11.5},
    "MATARÓ": {"venta": 2400, "alquiler": 13.0},
    "MATARO": {"venta": 2400, "alquiler": 13.0},
    "SANTA COLOMA DE GRAMENET": {"venta": 2300, "alquiler": 13.5},
    "RUBÍ": {"venta": 2300, "alquiler": 12.0},
    "RUBI": {"venta": 2300, "alquiler": 12.0},
    "CORNELLÀ DE LLOBREGAT": {"venta": 2600, "alquiler": 14.0},
    "CORNELLA DE LLOBREGAT": {"venta": 2600, "alquiler": 14.0},
    "SANT BOI DE LLOBREGAT": {"venta": 2400, "alquiler": 13.0},
    "CASTELLDEFELS": {"venta": 3000, "alquiler": 16.0},
    "GRANOLLERS": {"venta": 2400, "alquiler": 12.0},
    "BERGA": {"venta": 1300, "alquiler": 8.0},
    "PINEDA DE MAR": {"venta": 2000, "alquiler": 11.0},
    "MANRESA": {"venta": 1400, "alquiler": 9.0},
    "RIPOLLET": {"venta": 2100, "alquiler": 12.0},
    "VALLS": {"venta": 1600, "alquiler": 9.0},
    "CALAFELL": {"venta": 2200, "alquiler": 11.5},
    "VILANOVA I LA GELTRÚ": {"venta": 2100, "alquiler": 11.0},
    "VILANOVA I LA GELTRU": {"venta": 2100, "alquiler": 11.0},
    "EL MORELL": {"venta": 1500, "alquiler": 9.0},
    "CORBERA DE LLOBREGAT": {"venta": 2600, "alquiler": 13.0},
    "ALACANT": {"venta": 2200, "alquiler": 11.0},
    "AVILA": {"venta": 1200, "alquiler": 7.5},
    "TORDERA": {"venta": 1600, "alquiler": 9.0},
    "BLANES": {"venta": 2000, "alquiler": 11.0},
    "SALT": {"venta": 1600, "alquiler": 9.0},
    "GIRONA": {"venta": 2200, "alquiler": 12.0},
    "FIGUERES": {"venta": 1800, "alquiler": 10.0},
    "OLOT": {"venta": 1700, "alquiler": 9.5},
    "VIDRERES": {"venta": 1600, "alquiler": 9.0},
    "PALAMOS": {"venta": 2000, "alquiler": 11.0},
    "PALAMÓS": {"venta": 2000, "alquiler": 11.0},
    "_CATALUÑA": {"venta": 2000, "alquiler": 11.0},
    "_COMUNIDAD VALENCIANA": {"venta": 1800, "alquiler": 10.0},
    "_CASTILLA Y LEÓN": {"venta": 1200, "alquiler": 7.5},
    "_MADRID": {"venta": 3500, "alquiler": 15.0},
    "_ANDALUCIA": {"venta": 1700, "alquiler": 9.5},
    "_DEFAULT": {"venta": 1800, "alquiler": 10.0},
}

CCAA_MAP = {
    "CATALUÑA": "_CATALUÑA", "CATALUNYA": "_CATALUÑA",
    "COMUNIDAD VALENCIANA": "_COMUNIDAD VALENCIANA",
    "CASTILLA Y LEÓN": "_CASTILLA Y LEÓN",
    "COMUNIDAD DE MADRID": "_MADRID",
    "ANDALUCÍA": "_ANDALUCIA", "ANDALUCIA": "_ANDALUCIA",
}

CP_BARRIOS = {
    "08001": "EL RAVAL", "08002": "GÒTIC", "08003": "LA BARCELONETA",
    "08004": "SANTS-MONTJUÏC", "08005": "SANT MARTÍ", "08006": "GRÀCIA",
    "08007": "L'AMPLE", "08008": "LES CORTS", "08009": "LA DRETA DE L'EIXAMPLE",
    "08010": "LA SAGRERA", "08011": "SANT ANTONI", "08016": "NOU BARRIS",
    "08017": "SARRIÀ", "08018": "EL POBLENOU", "08019": "EL BESÒS",
    "08020": "SANT ANDREU", "08025": "LA SAGRADA FAMÍLIA", "08028": "SANTS",
    "08901": "CENTRE", "08902": "SANFELIU", "08903": "COLLBLANC",
    "08904": "LA TORRASSA", "08905": "LA FLORIDA", "08906": "PUBILLA CASAS",
    "08907": "BELLVITGE",
    "08911": "CENTRE", "08912": "LA SALUT", "08913": "LLEFIÀ",
    "08914": "SANT ROC",
}

BARRIOS_RIESGO_ALTO = [
    "FLORIDA", "LA SALUT", "CIUDAD VELLA", "RAVAL",
    "EL BESÒS", "LA MINA", "SANT ROC", "LLEFIÀ", "COLLBLANC",
    "PUBILLA CASAS", "LA TORRASSA", "NOU BARRIS", "BELLVITGE", "SANFELIU",
]

COSTE_DESAHUCIO = {
    "BAJA":    {"coste": 3000,  "meses": 8},
    "MEDIA":   {"coste": 6000,  "meses": 14},
    "ALTA":    {"coste": 10000, "meses": 22},
    "REVISAR": {"coste": 6000,  "meses": 14},
}

# ═══════════════════════════════════════════════════════════════════════
# HELPERS COMPARTIDOS
# ═══════════════════════════════════════════════════════════════════════

def encontrar_columna(df, posibles):
    """
    Versión mejorada que usa el motor de reconocimiento inteligente.
    Mantiene compatibilidad con el código existente.
    """
    return encontrar_columna_inteligente(df, posibles)

def calcular_descuento(precio):
    if precio < 70000:    return 0.25
    elif precio < 150000: return 0.225
    elif precio < 200000: return 0.20
    else:                 return 0.19

def calcular_precio_ofertado(precio):
    return precio * (1 - calcular_descuento(precio))

def obtener_tipo_inmueble(superficie):
    return "PISO" if superficie < 150 else "CASA"

def obtener_precios_mercado(municipio, ccaa="", precios_usuario=None):
    fuente = precios_usuario if precios_usuario else PRECIOS_BASE
    mun_up = municipio.upper().strip()
    if mun_up in fuente:
        return fuente[mun_up], "municipio"
    if ccaa:
        ccaa_up = ccaa.upper().strip()
        clave_ccaa = CCAA_MAP.get(ccaa_up)
        if clave_ccaa and clave_ccaa in PRECIOS_BASE:
            return PRECIOS_BASE[clave_ccaa], "ccaa"
    return PRECIOS_BASE["_DEFAULT"], "estimado"

def extraer_barrio(direccion, codigo_postal):
    cp = str(int(float(str(codigo_postal)))).zfill(5) if str(codigo_postal).replace('.', '').isdigit() else str(codigo_postal).strip()
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
        return "REVISAR", -0.25, "⚠️ Sin datos oficiales — revisar manualmente", 10.0, barrio
    if barrio.upper() in BARRIOS_RIESGO_ALTO:
        return "ALTA", -0.5, f"🔴 Barrio vulnerable detectado: {barrio}", porc, barrio
    elif porc > 20:
        return "ALTA", -0.5, f"🔴 {porc:.1f}% población vulnerable — Solo para expertos", porc, barrio
    elif porc > 10:
        return "MEDIA", -0.25, f"🟡 {porc:.1f}% población vulnerable — Evaluar con precaución", porc, barrio
    else:
        return "BAJA", 0, f"🟢 Zona consolidada ({porc:.1f}% vulnerable)", porc, barrio

def semaforo_html(nivel):
    colores = {
        "BAJA":    ("semaforo-verde",   "🟢 BAJA"),
        "MEDIA":   ("semaforo-naranja", "🟡 MEDIA"),
        "ALTA":    ("semaforo-rojo",    "🔴 ALTA"),
        "REVISAR": ("semaforo-gris",    "⚪ REVISAR"),
    }
    cls, texto = colores.get(nivel, ("semaforo-gris", nivel))
    return f'<span class="{cls}">{texto}</span>'

def calcular_score(roi_flip, rent_alquiler, precio_oferta, precio_mercado, nivel_riesgo,
                   w_roi, w_alq, w_mercado, w_riesgo):
    score_roi     = min(100, max(0, roi_flip / 0.5))
    score_alq     = min(100, max(0, rent_alquiler / 0.15))
    score_mercado = min(100, max(0, (1 - precio_oferta / max(precio_mercado, 1)) * 200))
    riesgo_pts    = {"BAJA": 100, "MEDIA": 50, "ALTA": 0, "REVISAR": 40}.get(nivel_riesgo, 40)
    total = (score_roi * w_roi + score_alq * w_alq +
             score_mercado * w_mercado + riesgo_pts * w_riesgo)
    return round(min(100, max(0, total)), 1)

def calcular_cashflow(precio_oferta, alquiler_mensual, vacancia_pct,
                      ibi_anual, comunidad_mensual, seguro_anual,
                      reforma_total, coste_desahucio, nivel_riesgo):
    ingresos_anuales = alquiler_mensual * 12 * (1 - vacancia_pct / 100)
    gastos_anuales   = ibi_anual + comunidad_mensual * 12 + seguro_anual
    coste_des        = COSTE_DESAHUCIO.get(nivel_riesgo, COSTE_DESAHUCIO["MEDIA"])["coste"] if coste_desahucio else 0
    inversion_total  = precio_oferta + reforma_total + coste_des
    cashflow_neto_anual = ingresos_anuales - gastos_anuales
    rentabilidad_neta   = (cashflow_neto_anual / inversion_total * 100) if inversion_total > 0 else 0
    payback = (inversion_total / cashflow_neto_anual) if cashflow_neto_anual > 0 else 999
    return {
        "ingresos_anuales":    round(ingresos_anuales, 0),
        "gastos_anuales":      round(gastos_anuales, 0),
        "cashflow_neto_anual": round(cashflow_neto_anual, 0),
        "cashflow_mensual":    round(cashflow_neto_anual / 12, 0),
        "rentabilidad_neta":   round(rentabilidad_neta, 2),
        "payback_anios":       round(payback, 1),
        "inversion_total":     round(inversion_total, 0),
        "coste_desahucio":     coste_des,
    }

def validar_datos(df):
    alertas = []
    if df.duplicated().sum() > 0:
        alertas.append(f"⚠️ **{df.duplicated().sum()} filas duplicadas exactas** detectadas")
    col_precio = encontrar_columna(df, ["precio"])
    col_sup    = encontrar_columna(df, ["superficie"])
    if col_precio:
        precios = pd.to_numeric(df[col_precio], errors="coerce").dropna()
        if len(precios) > 5:
            mean, std = precios.mean(), precios.std()
            outliers  = ((precios - mean).abs() > 3 * std).sum()
            if outliers > 0:
                alertas.append(f"⚠️ **{outliers} inmuebles con precio fuera de rango** (>3σ)")
        ceros = (pd.to_numeric(df[col_precio], errors="coerce") <= 0).sum()
        if ceros > 0:
            alertas.append(f"⚠️ **{ceros} filas con precio 0 o negativo**")
    if col_sup:
        ceros_sup = (pd.to_numeric(df[col_sup], errors="coerce") <= 0).sum()
        if ceros_sup > 0:
            alertas.append(f"⚠️ **{ceros_sup} filas con superficie 0**")
    return alertas

# ═══════════════════════════════════════════════════════════════════════
# MÓDULO CARTERA (original OkuPro)
# ═══════════════════════════════════════════════════════════════════════

def procesar_cartera(df, tipo_filtro, precios_usuario, vuln_dict,
                     vacancia_pct, reforma_m2, incluir_desahucio,
                     ibi_anual, comunidad_mensual, seguro_anual,
                     w_roi, w_alq, w_mercado, w_riesgo):
    
    # ─── DETECCIÓN DE COLUMNAS CON EL NUEVO MOTOR ──────────────────
    col_id  = encontrar_columna(df, ["id", "id_inmueble_completo"])
    col_mun = encontrar_columna(df, ["municipio"])
    col_dir = encontrar_columna(df, ["direccion"])
    col_cp  = encontrar_columna(df, ["cp"])
    col_sup = encontrar_columna(df, ["superficie"])
    col_pre = encontrar_columna(df, ["precio"])
    col_okupado = encontrar_columna(df, ["okupado_fase_sae"])

    # ─── DIAGNÓSTICO ──────────────────────────────────────────────────
    st.write("🔍 Columnas detectadas en el Excel:")
    st.write(f"ID: {col_id}")
    st.write(f"Municipio: {col_mun}")
    st.write(f"Dirección: {col_dir}")
    st.write(f"CP: {col_cp}")
    st.write(f"Superficie: {col_sup}")
    st.write(f"Precio: {col_pre}")
    st.write(f"OKUPADO: {col_okupado}")
    
    # Mostrar primeras filas del Excel para depurar
    st.write("📋 Primeras filas del Excel (sin procesar):")
    st.dataframe(df.head(5))
    if not col_mun:
        st.error(f"❌ No se encontró columna de municipio. Columnas: {', '.join(df.columns)}")
        return pd.DataFrame()
    if not col_pre:
        st.error("❌ No se encontró columna de precio.")
        return pd.DataFrame()

    resultados = []
    for _, row in df.iterrows():
        try:
            # ─── EXTRACCIÓN Y NORMALIZACIÓN DE DATOS ──────────────
            municipio_raw = str(row.get(col_mun, "")).strip()
            municipio = normalizar_municipio(municipio_raw)
            
            precio_orig  = float(row.get(col_pre, 0)) if pd.notna(row.get(col_pre)) else 0
            superficie   = float(row.get(col_sup, 0)) if col_sup and pd.notna(row.get(col_sup)) else 0
            direccion    = str(row.get(col_dir, "")) if col_dir else ""
            cp           = str(row.get(col_cp, "")).strip() if col_cp else ""
            id_inmueble  = str(row.get(col_id, "")) if col_id else ""

            if superficie <= 0 or precio_orig <= 0 or not municipio or municipio == "nan":
                continue

            tipo = obtener_tipo_inmueble(superficie)
            if tipo_filtro == "Solo pisos" and tipo != "PISO":
                continue
            if tipo_filtro == "Solo casas" and tipo != "CASA":
                continue

            precio_oferta      = calcular_precio_ofertado(precio_orig)
            descuento_pct      = round(calcular_descuento(precio_orig) * 100, 1)
            mercado, _fuente   = obtener_precios_mercado(municipio, precios_usuario=precios_usuario)
            precio_mercado_total   = superficie * mercado["venta"]
            alquiler_mensual_bruto = superficie * mercado["alquiler"]
            roi_flip   = (precio_mercado_total - precio_oferta) / precio_oferta if precio_oferta > 0 else 0
            rent_bruta = (alquiler_mensual_bruto * 12) / precio_oferta if precio_oferta > 0 else 0

            nivel_riesgo, penaliz, recomendacion, porc_vuln, barrio = obtener_riesgo(
                municipio, direccion, cp, vuln_dict)

            reforma_total = superficie * reforma_m2
            cf = calcular_cashflow(precio_oferta, alquiler_mensual_bruto, vacancia_pct,
                                   ibi_anual, comunidad_mensual, seguro_anual,
                                   reforma_total, incluir_desahucio, nivel_riesgo)
            score = calcular_score(roi_flip, rent_bruta, precio_oferta, precio_mercado_total,
                                   nivel_riesgo, w_roi, w_alq, w_mercado, w_riesgo)
            meses_desahucio = COSTE_DESAHUCIO.get(nivel_riesgo, {}).get("meses", 14) if incluir_desahucio else 0
            dir_corta = (direccion[:45] + "...") if len(str(direccion)) > 45 else direccion

            resultados.append({
                "ID": id_inmueble, "Municipio": municipio, "Dirección": dir_corta, "Barrio": barrio,
                "Tipo": tipo, "Superficie (m²)": superficie,
                "Precio original (€)": precio_orig, "Descuento %": descuento_pct,
                "Precio oferta (€)": round(precio_oferta, 0),
                "Precio mercado (€)": round(precio_mercado_total, 0),
                "ROI Flip (%)": round(roi_flip * 100, 1),
                "Rent. bruta (%)": round(rent_bruta * 100, 1),
                "Cashflow mensual (€)": cf["cashflow_mensual"],
                "Rent. neta (%)": cf["rentabilidad_neta"],
                "Payback (años)": cf["payback_anios"],
                "Inversión total (€)": cf["inversion_total"],
                "Riesgo zona": nivel_riesgo, "% Vulnerable": round(porc_vuln, 1),
                "Recomendación": recomendacion,
                "Meses desahucio est.": meses_desahucio,
                "Score OKUPRO": score,
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

def generar_pdf_inmueble(row):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles  = getSampleStyleSheet()
    story   = []
    title_style = ParagraphStyle("title", fontSize=18, textColor=colors.HexColor("#1a1a2e"),
                                 spaceAfter=6, fontName="Helvetica-Bold")
    sub_style   = ParagraphStyle("sub",   fontSize=11, textColor=colors.HexColor("#6c757d"), spaceAfter=16)
    label_style = ParagraphStyle("label", fontSize=9,  textColor=colors.HexColor("#6c757d"), fontName="Helvetica")
    value_style = ParagraphStyle("value", fontSize=12, textColor=colors.HexColor("#212529"), fontName="Helvetica-Bold")
    body_style  = ParagraphStyle("body",  fontSize=10, textColor=colors.HexColor("#343a40"), leading=14)
    footer_style= ParagraphStyle("footer",fontSize=8,  textColor=colors.HexColor("#adb5bd"), alignment=1)

    story.append(Paragraph("🏠 OKUPRO v7.1 — Ficha de inmueble", title_style))
    story.append(Paragraph(f"{row.get('Dirección','N/A')} · {row.get('Municipio','N/A')} · {row.get('Barrio','N/A')}", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dee2e6")))
    story.append(Spacer(1, 0.4*cm))

    riesgo       = row.get("Riesgo zona", "REVISAR")
    colores_r    = {"BAJA":"#28a745","MEDIA":"#ffc107","ALTA":"#dc3545","REVISAR":"#6c757d"}
    riesgo_style = ParagraphStyle("riesgo", fontSize=13, textColor=colors.HexColor(colores_r.get(riesgo,"#6c757d")),
                                  fontName="Helvetica-Bold", spaceAfter=12)
    iconos = {"BAJA":"● ZONA RIESGO BAJO","MEDIA":"● ZONA RIESGO MEDIO","ALTA":"● ZONA RIESGO ALTO","REVISAR":"● ZONA SIN DATOS"}
    story.append(Paragraph(iconos.get(riesgo, riesgo), riesgo_style))
    story.append(Paragraph(str(row.get("Recomendación","")), body_style))
    story.append(Spacer(1, 0.4*cm))

    def fila(label, val):
        return [Paragraph(label, label_style), Paragraph(str(val), value_style)]

    data_tabla = [
        ["", ""],
        fila("Tipo de inmueble",         f"{row.get('Tipo','N/A')} · {row.get('Superficie (m²)',0):.0f} m²"),
        fila("Precio original",          f"€ {row.get('Precio original (€)',0):,.0f}"),
        fila("Precio oferta (descuento)",f"€ {row.get('Precio oferta (€)',0):,.0f} ({row.get('Descuento %',0):.1f}% dto.)"),
        fila("Precio de mercado estimado",f"€ {row.get('Precio mercado (€)',0):,.0f}"),
        fila("ROI Flip estimado",        f"{row.get('ROI Flip (%)',0):.1f}%"),
        fila("Rentabilidad bruta",       f"{row.get('Rent. bruta (%)',0):.1f}%"),
        fila("Rentabilidad neta",        f"{row.get('Rent. neta (%)',0):.2f}%"),
        fila("Cashflow mensual neto",    f"€ {row.get('Cashflow mensual (€)',0):,.0f}"),
        fila("Payback estimado",         f"{row.get('Payback (años)',0):.1f} años"),
        fila("Inversión total estimada", f"€ {row.get('Inversión total (€)',0):,.0f}"),
        fila("Coste desahucio estimado", f"€ {row.get('_coste_desahucio',0):,.0f} (~{row.get('Meses desahucio est.',0)} meses)"),
        fila("Reforma estimada",         f"€ {row.get('_reforma_total',0):,.0f}"),
        fila("Score OKUPRO",             f"{row.get('Score OKUPRO',0):.0f} / 100"),
    ]
    tabla = Table(data_tabla, colWidths=[7*cm, 9*cm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f8f9fa")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f8f9fa")]),
        ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#dee2e6")),
        ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(tabla)
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dee2e6")))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("OKUPRO v7.1 · Uso exclusivamente informativo · No constituye asesoramiento financiero", footer_style))
    doc.build(story)
    buf.seek(0)
    return buf


# ═══════════════════════════════════════════════════════════════════════
# MÓDULO NPL
# ═══════════════════════════════════════════════════════════════════════

def detectar_columna_deuda(df):
    """
    Busca la columna de deuda usando el motor inteligente
    """
    col = encontrar_columna_inteligente(df, ["ob_deuda"])
    if col:
        return col, False
    
    for col in df.columns:
        if col.lower().strip() == "ob":
            return col, False
    
    cols_deuda = []
    for col in df.columns:
        col_norm = normalizar_texto(col)
        if "deuda" in col_norm or "saldo" in col_norm or "ob" in col_norm:
            if "tasacion" not in col_norm and "tasación" not in col_norm:
                cols_deuda.append(col)
    
    if len(cols_deuda) == 1:
        return cols_deuda[0], False
    elif len(cols_deuda) > 1:
        return cols_deuda, True
    else:
        return None, False


def clasificar_ltv(ltv):
    if ltv <= 0.5:
        return "EXCELENTE", "🟢 LTV ≤ 50% — Margen amplio para el inversor"
    elif ltv <= 0.7:
        return "BUENA", "🟡 LTV 50–70% — Oportunidad razonable"
    elif ltv <= 0.9:
        return "AJUSTADA", "🟠 LTV 70–90% — Margen estrecho, evaluar bien"
    elif ltv <= 1.0:
        return "NEUTRAL", "⚪ LTV 90–100% — Deuda = valor mercado"
    else:
        return "NEGATIVA", "🔴 LTV > 100% — Deuda supera el valor de mercado"


def color_ltv(nivel):
    mapa = {
        "EXCELENTE": "background-color:#d4edda;color:#155724",
        "BUENA": "background-color:#fff3cd;color:#856404",
        "AJUSTADA": "background-color:#ffeeba;color:#856404",
        "NEUTRAL": "background-color:#e2e3e5;color:#383d41",
        "NEGATIVA": "background-color:#f8d7da;color:#721c24",
    }
    return mapa.get(nivel, "")


def procesar_npl(df, col_deuda, precios_usuario, vuln_dict, descuento_compra_pct):
    col_id = encontrar_columna(df, ["id", "id_inmueble_completo"])
    col_ref = encontrar_columna(df, ["id_inmueble_completo"])
    col_dir = encontrar_columna(df, ["direccion"])
    col_cp = encontrar_columna(df, ["cp"])
    col_mun = encontrar_columna(df, ["municipio"])
    col_ccaa = encontrar_columna(df, ["ccaa"])
    col_tipo = encontrar_columna(df, ["tipo"])
    col_pl_npl = encontrar_columna(df, ["pl_npl"])

    if not col_mun:
        st.error(f"❌ No se encontró columna de municipio. Columnas: {', '.join(df.columns)}")
        return pd.DataFrame()

    resultados = []
    for _, row in df.iterrows():
        try:
            ob_deuda = float(row.get(col_deuda, 0)) if pd.notna(row.get(col_deuda)) else 0
            if ob_deuda <= 0:
                continue

            municipio_raw = str(row.get(col_mun, "")).strip() if col_mun else ""
            municipio = normalizar_municipio(municipio_raw)
            ccaa = str(row.get(col_ccaa, "")).strip() if col_ccaa else ""
            direccion = str(row.get(col_dir, "")) if col_dir else ""
            cp = str(row.get(col_cp, "")).strip() if col_cp else ""
            id_inmueble = str(row.get(col_id, "")) if col_id else ""
            ref_cat = str(row.get(col_ref, "")) if col_ref else ""
            tipo_raw = str(row.get(col_tipo, "")).strip().upper() if col_tipo else ""
            pl_npl = str(row.get(col_pl_npl, "NPL")).strip().upper() if col_pl_npl else "NPL"

            if not municipio or municipio == "nan":
                continue

            if "VIVIENDA" in tipo_raw or "PISO" in tipo_raw or "VIVENDA" in tipo_raw:
                tipo_label = "VIVIENDA"
            elif "CASA" in tipo_raw or "UNIFAM" in tipo_raw or "UNIF" in tipo_raw:
                tipo_label = "CASA"
            else:
                tipo_label = tipo_raw if tipo_raw else "VIVIENDA"

            mercado, fuente_precio = obtener_precios_mercado(municipio, ccaa, precios_usuario)
            m2_estimado = 80 if tipo_label == "VIVIENDA" else 150
            precio_mercado_est = m2_estimado * mercado["venta"]

            ltv = ob_deuda / precio_mercado_est if precio_mercado_est > 0 else 999
            margen_bruto = precio_mercado_est - ob_deuda
            precio_compra_recomendado = ob_deuda * (1 - descuento_compra_pct / 100)
            margen_sobre_compra = precio_mercado_est - precio_compra_recomendado
            roi_sobre_compra = (margen_sobre_compra / precio_compra_recomendado * 100) if precio_compra_recomendado > 0 else 0

            nivel_ltv, desc_ltv = clasificar_ltv(ltv)
            nivel_riesgo, _, recomendacion_zona, porc_vuln, barrio = obtener_riesgo(
                municipio, direccion, cp, vuln_dict)

            dir_corta = (direccion[:50] + "...") if len(str(direccion)) > 50 else direccion

            resultados.append({
                "PL/NPL": pl_npl,
                "ID": id_inmueble,
                "Ref. Catastral": ref_cat,
                "Municipio": municipio,
                "CCAA": ccaa,
                "Dirección": dir_corta,
                "Tipo": tipo_label,
                "OB / Deuda (€)": round(ob_deuda, 2),
                "Valor Mercado Est. (€)": round(precio_mercado_est, 0),
                "Fuente precio": fuente_precio,
                "LTV (%)": round(ltv * 100, 1),
                "Nivel LTV": nivel_ltv,
                "Margen bruto (€)": round(margen_bruto, 0),
                "Precio compra rec. (€)": round(precio_compra_recomendado, 0),
                "Margen s/compra (€)": round(margen_sobre_compra, 0),
                "ROI s/compra (%)": round(roi_sobre_compra, 1),
                "Riesgo zona": nivel_riesgo,
                "% Vulnerable": round(porc_vuln, 1),
                "Barrio": barrio,
                "Descripción LTV": desc_ltv,
                "Recomendación zona": recomendacion_zona,
                "_m2_estimado": m2_estimado,
                "_precio_m2_zona": mercado["venta"],
            })
        except Exception:
            continue

    df_res = pd.DataFrame(resultados)
    if len(df_res) > 0:
        df_res = df_res.sort_values(["Nivel LTV", "ROI s/compra (%)"],
                                    ascending=[True, False]).reset_index(drop=True)
    return df_res


def generar_pdf_npl(row):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle("title", fontSize=16, textColor=colors.HexColor("#1a1a2e"),
                                 spaceAfter=6, fontName="Helvetica-Bold")
    sub_style = ParagraphStyle("sub", fontSize=10, textColor=colors.HexColor("#6c757d"), spaceAfter=14)
    label_style = ParagraphStyle("label", fontSize=9, textColor=colors.HexColor("#6c757d"), fontName="Helvetica")
    value_style = ParagraphStyle("value", fontSize=11, textColor=colors.HexColor("#212529"), fontName="Helvetica-Bold")
    body_style = ParagraphStyle("body", fontSize=9, textColor=colors.HexColor("#343a40"), leading=13)
    footer_style = ParagraphStyle("footer", fontSize=7, textColor=colors.HexColor("#adb5bd"), alignment=1)

    story.append(Paragraph("📋 OKUPRO v7.1 — Ficha NPL / Crédito Hipotecario", title_style))
    story.append(Paragraph(f"ID: {row.get('ID','N/A')}  ·  {row.get('Dirección','N/A')}  ·  {row.get('Municipio','N/A')}", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dee2e6")))
    story.append(Spacer(1, 0.3*cm))

    pl_npl = row.get("PL/NPL", "NPL")
    badge_color = "#1a1a2e" if pl_npl == "NPL" else "#17a2b8"
    badge_style = ParagraphStyle("badge", fontSize=11, textColor=colors.HexColor(badge_color),
                                 fontName="Helvetica-Bold", spaceAfter=8)
    story.append(Paragraph(f"Tipo de crédito: {pl_npl}", badge_style))

    nivel_ltv = row.get("Nivel LTV", "NEUTRAL")
    ltv_colors = {"EXCELENTE": "#28a745", "BUENA": "#ffc107", "AJUSTADA": "#fd7e14",
                  "NEUTRAL": "#6c757d", "NEGATIVA": "#dc3545"}
    ltv_style = ParagraphStyle("ltv", fontSize=12, textColor=colors.HexColor(ltv_colors.get(nivel_ltv, "#6c757d")),
                               fontName="Helvetica-Bold", spaceAfter=6)
    story.append(Paragraph(f"Clasificación LTV: {nivel_ltv}", ltv_style))
    story.append(Paragraph(str(row.get("Descripción LTV", "")), body_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"Zona: {row.get('Recomendación zona', '')}", body_style))
    story.append(Spacer(1, 0.4*cm))

    def fila(label, val):
        return [Paragraph(label, label_style), Paragraph(str(val), value_style)]

    data_tabla = [
        ["", ""],
        fila("Ref. Catastral", row.get("Ref. Catastral", "N/A")),
        fila("Tipo de inmueble", row.get("Tipo", "N/A")),
        fila("OB / Deuda pendiente", f"€ {row.get('OB / Deuda (€)', 0):,.2f}"),
        fila("Valor mercado estimado", f"€ {row.get('Valor Mercado Est. (€)', 0):,.0f}  ({row.get('Fuente precio', 'est.')})"),
        fila("LTV (Deuda / Mercado)", f"{row.get('LTV (%)', 0):.1f}%"),
        fila("Margen bruto (Mercado - OB)", f"€ {row.get('Margen bruto (€)', 0):,.0f}"),
        fila("Precio compra recomendado", f"€ {row.get('Precio compra rec. (€)', 0):,.0f}"),
        fila("Margen s/ precio compra", f"€ {row.get('Margen s/compra (€)', 0):,.0f}"),
        fila("ROI estimado s/ compra", f"{row.get('ROI s/compra (%)', 0):.1f}%"),
        fila("Riesgo zona", row.get("Riesgo zona", "N/A")),
        fila("% Vulnerable MITMA", f"{row.get('% Vulnerable', 0):.1f}%"),
        fila("m² estimados", f"{row.get('_m2_estimado', 80)} m²  ·  €/m² zona: {row.get('_precio_m2_zona', 0):,.0f}"),
    ]

    tabla = Table(data_tabla, colWidths=[7*cm, 9*cm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8f9fa")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dee2e6")),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(tabla)
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        "⚠️ AVISO: El valor de mercado es una estimación basada en precio €/m² de la zona. "
        "No sustituye a una tasación oficial. El LTV y los márgenes son orientativos para el inversor.",
        ParagraphStyle("aviso", fontSize=8, textColor=colors.HexColor("#856404"),
                       backColor=colors.HexColor("#fff3cd"), borderPadding=6, leading=12)
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dee2e6")))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "OKUPRO v7.1 · Módulo NPL · Uso exclusivamente informativo · No constituye asesoramiento financiero ni legal",
        footer_style))
    doc.build(story)
    buf.seek(0)
    return buf


# ═══════════════════════════════════════════════════════════════════════
# UI PRINCIPAL — PESTAÑAS
# ═══════════════════════════════════════════════════════════════════════

st.title("🏠 OKUPRO v7.1")
st.subheader("Analizador de carteras inmobiliarias · Pisos ocupados · NPLs hipotecarios")

tab_cartera, tab_npl = st.tabs(["🏠 Cartera OkuPro", "📋 Análisis NPL"])

vuln_dict = cargar_vulnerabilidad()

# ──────────────────────────────────────────────────────────────────────
# TAB 1 — CARTERA OKUPRO (original)
# ──────────────────────────────────────────────────────────────────────
with tab_cartera:
    with st.sidebar:
        st.header("⚙️ Configuración — Cartera")
        tipo_filtro = st.radio("Tipo de inmueble:", ["Todos", "Solo pisos", "Solo casas"])
        top_n = st.slider("Top resultados", 10, 100, 25, step=5)
        st.markdown("---")
        st.subheader("💶 Cashflow")
        vacancia_pct = st.slider("Vacancia (%)", 0, 25, 8)
        reforma_m2 = st.slider("Reforma (€/m²)", 0, 500, 80)
        ibi_anual = st.number_input("IBI anual (€)", 0, 5000, 400)
        comunidad_mensual = st.number_input("Comunidad mensual (€)", 0, 500, 60)
        seguro_anual = st.number_input("Seguro anual (€)", 0, 2000, 250)
        incluir_desahucio = st.checkbox("Incluir coste desahucio", value=True)
        st.markdown("---")
        st.subheader("⚖️ Pesos Score")
        w_roi = st.slider("Peso ROI Flip", 0.0, 1.0, 0.30, 0.05)
        w_alq = st.slider("Peso Rent. alquiler", 0.0, 1.0, 0.25, 0.05)
        w_mercado = st.slider("Peso precio/mercado", 0.0, 1.0, 0.20, 0.05)
        w_riesgo = st.slider("Peso riesgo zona", 0.0, 1.0, 0.25, 0.05)
        total_w = round(w_roi + w_alq + w_mercado + w_riesgo, 2)
        if abs(total_w - 1.0) > 0.01:
            st.warning(f"⚠️ Pesos suman {total_w:.2f} — deben sumar 1.0")
        st.markdown("---")
        st.subheader("📊 Precios personalizados")
        archivo_precios = st.file_uploader("Excel precios (opcional)", type=["xlsx", "xls"],
                                           help="Columnas: Municipio, PrecioVenta (€/m²), PrecioAlquiler (€/m²)",
                                           key="precios_cartera")
        precios_usuario = None
        if archivo_precios:
            try:
                df_precios = pd.read_excel(archivo_precios)
                precios_usuario = {}
                for _, r in df_precios.iterrows():
                    mun = str(r.iloc[0]).strip().upper()
                    precios_usuario[mun] = {"venta": float(r.iloc[1]), "alquiler": float(r.iloc[2])}
                st.success(f"✅ {len(precios_usuario)} municipios cargados")
            except Exception as e:
                st.error(f"Error: {e}")
        st.markdown("---")
        st.subheader("🔍 Filtros de alerta")
        umbral_roi = st.slider("ROI Flip mínimo (%)", 0, 80, 0)
        umbral_rent = st.slider("Rent. bruta mínima (%)", 0, 20, 0)
        solo_riesgo_bajo = st.checkbox("Solo riesgo BAJO")
        solo_revisar = st.checkbox("Solo requieren revisión")

    archivo = st.file_uploader("📂 Sube tu Excel de cartera (pisos ocupados / bancarios / SAREB)",
                               type=["xlsx", "xls"], key="cartera_file")

    if archivo is not None:
        try:
            df_raw = pd.read_excel(archivo)
            st.success(f"✅ Archivo cargado: {len(df_raw)} filas")
            alertas = validar_datos(df_raw)
            if alertas:
                with st.expander("⚠️ Calidad de datos", expanded=True):
                    for a in alertas:
                        st.markdown(a)

            with st.spinner("⏳ Analizando cartera..."):
                df_res = procesar_cartera(df_raw, tipo_filtro, precios_usuario, vuln_dict,
                                          vacancia_pct, reforma_m2, incluir_desahucio,
                                          ibi_anual, comunidad_mensual, seguro_anual,
                                          w_roi, w_alq, w_mercado, w_riesgo)
            if len(df_res) == 0:
                st.warning("⚠️ No se encontraron inmuebles con los filtros seleccionados.")
                st.stop()

            df_filtrado = df_res.copy()
            if umbral_roi > 0:
                df_filtrado = df_filtrado[df_filtrado["ROI Flip (%)"] >= umbral_roi]
            if umbral_rent > 0:
                df_filtrado = df_filtrado[df_filtrado["Rent. bruta (%)"] >= umbral_rent]
            if solo_riesgo_bajo:
                df_filtrado = df_filtrado[df_filtrado["Riesgo zona"] == "BAJA"]
            if solo_revisar:
                df_filtrado = df_filtrado[df_filtrado["Riesgo zona"] == "REVISAR"]

            st.subheader("📊 Resumen de la cartera")
            cols = st.columns(6)
            cols[0].metric("Total analizados", len(df_filtrado))
            cols[1].metric("🟢 Riesgo BAJO", (df_filtrado["Riesgo zona"] == "BAJA").sum())
            cols[2].metric("🟡 Riesgo MEDIO", (df_filtrado["Riesgo zona"] == "MEDIA").sum())
            cols[3].metric("🔴 Riesgo ALTO", (df_filtrado["Riesgo zona"] == "ALTA").sum())
            cols[4].metric("ROI Flip medio", f"{df_filtrado['ROI Flip (%)'].mean():.1f}%")
            cols[5].metric("Score medio", f"{df_filtrado['Score OKUPRO'].mean():.0f}/100")

            st.subheader(f"🏆 Top {min(top_n, len(df_filtrado))} Oportunidades")
            cols_mostrar = ["Score OKUPRO", "ID", "Municipio", "Barrio", "Tipo", "Superficie (m²)",
                            "Precio oferta (€)", "Precio mercado (€)", "ROI Flip (%)", "Rent. bruta (%)",
                            "Rent. neta (%)", "Cashflow mensual (€)", "Payback (años)", "Riesgo zona", "Recomendación"]
            df_display = df_filtrado[[c for c in cols_mostrar if c in df_filtrado.columns]].head(top_n).copy()

            def color_score(val):
                if val >= 70:
                    return "background-color:#d4edda;color:#155724"
                elif val >= 40:
                    return "background-color:#fff3cd;color:#856404"
                else:
                    return "background-color:#f8d7da;color:#721c24"

            def color_riesgo(val):
                return {"BAJA": "background-color:#d4edda;color:#155724", "MEDIA": "background-color:#fff3cd;color:#856404",
                        "ALTA": "background-color:#f8d7da;color:#721c24", "REVISAR": "background-color:#e2e3e5;color:#383d41"}.get(val, "")

            styled = (df_display.style
                      .map(color_score, subset=["Score OKUPRO"])
                      .map(color_riesgo, subset=["Riesgo zona"])
                      .format({"Precio oferta (€)": "€ {:,.0f}", "Precio mercado (€)": "€ {:,.0f}",
                               "Cashflow mensual (€)": "€ {:,.0f}", "ROI Flip (%)": "{:.1f}%",
                               "Rent. bruta (%)": "{:.1f}%", "Rent. neta (%)": "{:.2f}%"}))
            st.dataframe(styled, use_container_width=True, height=420)

            st.subheader("📄 Informe PDF por inmueble")
            id_sel = st.selectbox("Selecciona inmueble por ID", df_filtrado["ID"].astype(str).tolist())
            if id_sel:
                row_sel = df_filtrado[df_filtrado["ID"].astype(str) == id_sel].iloc[0]
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(f"**Riesgo zona:** {semaforo_html(row_sel['Riesgo zona'])}", unsafe_allow_html=True)
                    st.markdown(f"**Recomendación:** {row_sel['Recomendación']}")
                    st.markdown(f"**Score OKUPRO:** `{row_sel['Score OKUPRO']:.0f}/100`")
                with c2:
                    pdf_buf = generar_pdf_inmueble(row_sel)
                    st.download_button("📥 Descargar PDF", pdf_buf, f"OKUPRO_{id_sel}.pdf", "application/pdf")

            st.subheader("📈 Análisis visual")
            tab1, tab2, tab3, tab4 = st.tabs(["ROI vs Riesgo", "Cashflow", "Municipios", "Score"])
            with tab1:
                fig = px.scatter(df_filtrado.head(top_n), x="ROI Flip (%)", y="Rent. neta (%)",
                                 color="Riesgo zona",
                                 color_discrete_map={"BAJA": "#28a745", "MEDIA": "#ffc107", "ALTA": "#dc3545",
                                                     "REVISAR": "#6c757d"},
                                 size="Superficie (m²)", hover_data=["ID", "Municipio", "Score OKUPRO"],
                                 title="ROI Flip vs Rentabilidad neta")
                st.plotly_chart(fig, use_container_width=True)
            with tab2:
                fig2 = px.bar(df_filtrado.head(top_n).sort_values("Cashflow mensual (€)", ascending=True),
                              x="Cashflow mensual (€)", y="ID", orientation="h", color="Riesgo zona",
                              color_discrete_map={"BAJA": "#28a745", "MEDIA": "#ffc107", "ALTA": "#dc3545",
                                                  "REVISAR": "#6c757d"},
                              title="Cashflow mensual neto por inmueble")
                st.plotly_chart(fig2, use_container_width=True)
            with tab3:
                muni = (df_filtrado.groupby("Municipio")
                        .agg(n=("Score OKUPRO", "count"), score_medio=("Score OKUPRO", "mean"))
                        .reset_index().sort_values("score_medio", ascending=False).head(15))
                fig3 = px.bar(muni, x="Municipio", y="score_medio", color="n", title="Score medio por municipio")
                fig3.update_xaxes(tickangle=45)
                st.plotly_chart(fig3, use_container_width=True)
            with tab4:
                fig4 = px.histogram(df_filtrado, x="Score OKUPRO", nbins=20,
                                    color_discrete_sequence=["#4a90d9"], title="Distribución Score OKUPRO")
                fig4.add_vline(x=df_filtrado["Score OKUPRO"].mean(), line_dash="dash",
                               annotation_text="Media", line_color="red")
                st.plotly_chart(fig4, use_container_width=True)

            cols_export = [c for c in df_filtrado.columns if not c.startswith("_")]
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_filtrado[cols_export].to_excel(writer, index=False, sheet_name="OKUPRO_Resultados")
            st.download_button("📥 Descargar Excel completo", output.getvalue(), "okupro_v7_cartera.xlsx")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.info("📂 Sube un archivo Excel de cartera para comenzar")

# ──────────────────────────────────────────────────────────────────────
# TAB 2 — MÓDULO NPL
# ──────────────────────────────────────────────────────────────────────
with tab_npl:
    st.markdown("### 📋 Análisis de cartera NPL — Créditos hipotecarios")
    st.markdown("""
    Sube el Excel del fondo con los créditos NPL/PL. El programa detectará automáticamente 
    la columna de deuda (`OB` o `Deuda`) y calculará el **valor de mercado estimado**, el **LTV** 
    y el **margen para el inversor** para cada inmueble.
    """)

    col_cfg1, col_cfg2 = st.columns([1, 1])
    with col_cfg1:
        descuento_compra_pct = st.slider(
            "📉 Descuento sobre OB al comprar el crédito (%)",
            min_value=0, max_value=80, value=30,
            help="El inversor normalmente compra la deuda con descuento sobre el nominal OB. Ajusta según la oferta del fondo.")
    with col_cfg2:
        st.markdown("**¿Qué es el LTV?**")
        st.markdown("""
        - 🟢 **≤ 50%** → Excelente margen para el inversor  
        - 🟡 **50–70%** → Oportunidad razonable  
        - 🟠 **70–90%** → Margen estrecho  
        - ⚪ **90–100%** → Deuda ≈ valor mercado  
        - 🔴 **> 100%** → Deuda supera el mercado  
        """)

    st.markdown("---")

    archivo_npl = st.file_uploader(
        "📂 Sube el Excel NPL del fondo",
        type=["xlsx", "xls"],
        key="npl_file",
        help="Columnas esperadas: OB o Deuda, Referencia Catastral, Municipio, Dirección, CP, Tipo Inmueble"
    )

    if archivo_npl is not None:
        try:
            df_npl_raw = pd.read_excel(archivo_npl)
            st.success(f"✅ Archivo cargado: {len(df_npl_raw)} filas · {len(df_npl_raw.columns)} columnas")

            with st.expander("🔍 Columnas detectadas en el archivo"):
                st.write(list(df_npl_raw.columns))

            col_deuda_result, es_ambiguo = detectar_columna_deuda(df_npl_raw)

            if es_ambiguo:
                st.warning("⚠️ Se han encontrado varias columnas que podrían ser la deuda. Selecciona cuál es:")
                col_deuda_sel = st.selectbox(
                    "¿Cuál es la columna de deuda (OB)?",
                    options=col_deuda_result,
                    help="Selecciona la columna que contiene el importe de la deuda pendiente del propietario con el fondo. NO es el precio de tasación."
                )
                col_deuda = col_deuda_sel
            elif col_deuda_result is None:
                st.warning("⚠️ No se detectó automáticamente la columna de deuda. Selecciónala manualmente:")
                cols_num = [c for c in df_npl_raw.columns
                            if pd.to_numeric(df_npl_raw[c], errors="coerce").notna().sum() > len(df_npl_raw) * 0.5]
                col_deuda = st.selectbox(
                    "Columna de deuda pendiente (OB):",
                    options=cols_num if cols_num else list(df_npl_raw.columns),
                    help="Es el importe que el propietario debe al fondo. No es la tasación ni el precio de venta."
                )
            else:
                col_deuda = col_deuda_result
                st.success(f"✅ Columna de deuda detectada automáticamente: **`{col_deuda}`**")

            if col_deuda:
                vals_muestra = pd.to_numeric(df_npl_raw[col_deuda], errors="coerce").dropna()
                c1, c2, c3 = st.columns(3)
                c1.metric("Media OB/Deuda", f"€ {vals_muestra.mean():,.0f}")
                c2.metric("Mínimo", f"€ {vals_muestra.min():,.0f}")
                c3.metric("Máximo", f"€ {vals_muestra.max():,.0f}")

            st.markdown("---")

            with st.expander("📊 Cargar precios de mercado personalizados (opcional)"):
                st.markdown("Si tienes datos más precisos de €/m² por municipio, súbelos aquí. Formato: **Municipio | PrecioVenta(€/m²) | PrecioAlquiler(€/m²)**")
                archivo_precios_npl = st.file_uploader("Excel precios municipios", type=["xlsx", "xls"], key="precios_npl")
                precios_usuario_npl = None
                if archivo_precios_npl:
                    try:
                        df_p = pd.read_excel(archivo_precios_npl)
                        precios_usuario_npl = {}
                        for _, r in df_p.iterrows():
                            mun = str(r.iloc[0]).strip().upper()
                            precios_usuario_npl[mun] = {"venta": float(r.iloc[1]), "alquiler": float(r.iloc[2])}
                        st.success(f"✅ {len(precios_usuario_npl)} municipios cargados")
                    except Exception as e:
                        st.error(f"Error: {e}")

            if st.button("🚀 Analizar cartera NPL", type="primary"):
                with st.spinner("⏳ Procesando créditos NPL..."):
                    df_npl_res = procesar_npl(df_npl_raw, col_deuda,
                                              precios_usuario_npl if 'precios_usuario_npl' in locals() else None,
                                              vuln_dict, descuento_compra_pct)

                if len(df_npl_res) == 0:
                    st.warning("⚠️ No se pudieron procesar inmuebles. Revisa las columnas.")
                else:
                    st.session_state["df_npl_resultado"] = df_npl_res

            if "df_npl_resultado" in st.session_state:
                df_npl_res = st.session_state["df_npl_resultado"]

                st.subheader("📊 Resumen de la cartera NPL")
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                c1.metric("Total créditos", len(df_npl_res))
                c2.metric("🟢 LTV Excelente", (df_npl_res["Nivel LTV"] == "EXCELENTE").sum())
                c3.metric("🟡 LTV Buena", (df_npl_res["Nivel LTV"] == "BUENA").sum())
                c4.metric("🟠 LTV Ajustada", (df_npl_res["Nivel LTV"] == "AJUSTADA").sum())
                c5.metric("🔴 LTV Negativa", (df_npl_res["Nivel LTV"] == "NEGATIVA").sum())
                c6.metric("ROI medio s/compra", f"{df_npl_res['ROI s/compra (%)'].mean():.1f}%")

                c7, c8, c9 = st.columns(3)
                total_ob = df_npl_res["OB / Deuda (€)"].sum()
                total_mercado = df_npl_res["Valor Mercado Est. (€)"].sum()
                margen_total = total_mercado - total_ob
                c7.metric("Total OB cartera", f"€ {total_ob:,.0f}")
                c8.metric("Valor mercado total", f"€ {total_mercado:,.0f}")
                c9.metric("Margen bruto total", f"€ {margen_total:,.0f}")

                st.subheader("🔍 Filtros NPL")
                cf1, cf2, cf3, cf4 = st.columns(4)
                filtro_ltv = cf1.multiselect("Nivel LTV", ["EXCELENTE", "BUENA", "AJUSTADA", "NEUTRAL", "NEGATIVA"],
                                             default=["EXCELENTE", "BUENA", "AJUSTADA", "NEUTRAL", "NEGATIVA"])
                filtro_riesgo = cf2.multiselect("Riesgo zona", ["BAJA", "MEDIA", "ALTA", "REVISAR"],
                                                default=["BAJA", "MEDIA", "ALTA", "REVISAR"])
                filtro_tipo = cf3.multiselect("Tipo inmueble", df_npl_res["Tipo"].unique().tolist(),
                                              default=df_npl_res["Tipo"].unique().tolist())
                filtro_pl = cf4.multiselect("PL/NPL", df_npl_res["PL/NPL"].unique().tolist(),
                                            default=df_npl_res["PL/NPL"].unique().tolist())

                df_show = df_npl_res[
                    df_npl_res["Nivel LTV"].isin(filtro_ltv) &
                    df_npl_res["Riesgo zona"].isin(filtro_riesgo) &
                    df_npl_res["Tipo"].isin(filtro_tipo) &
                    df_npl_res["PL/NPL"].isin(filtro_pl)
                ].copy()

                st.markdown(f"**Mostrando {len(df_show)} créditos** de {len(df_npl_res)} totales")

                cols_tabla = ["PL/NPL", "ID", "Ref. Catastral", "Municipio", "CCAA", "Tipo",
                              "OB / Deuda (€)", "Valor Mercado Est. (€)", "LTV (%)",
                              "Nivel LTV", "Margen bruto (€)", "Precio compra rec. (€)",
                              "Margen s/compra (€)", "ROI s/compra (%)", "Riesgo zona", "Descripción LTV"]
                df_tabla = df_show[[c for c in cols_tabla if c in df_show.columns]].copy()

                def color_nivel_ltv(val):
                    return color_ltv(val)

                def color_riesgo_npl(val):
                    return {"BAJA": "background-color:#d4edda;color:#155724", "MEDIA": "background-color:#fff3cd;color:#856404",
                            "ALTA": "background-color:#f8d7da;color:#721c24", "REVISAR": "background-color:#e2e3e5;color:#383d41"}.get(val, "")

                styled_npl = (df_tabla.style
                              .map(color_nivel_ltv, subset=["Nivel LTV"])
                              .map(color_riesgo_npl, subset=["Riesgo zona"])
                              .format({
                                  "OB / Deuda (€)": "€ {:,.0f}",
                                  "Valor Mercado Est. (€)": "€ {:,.0f}",
                                  "Margen bruto (€)": "€ {:,.0f}",
                                  "Precio compra rec. (€)": "€ {:,.0f}",
                                  "Margen s/compra (€)": "€ {:,.0f}",
                                  "LTV (%)": "{:.1f}%",
                                  "ROI s/compra (%)": "{:.1f}%",
                              }))
                st.dataframe(styled_npl, use_container_width=True, height=450)

                st.subheader("📄 Ficha PDF por crédito NPL")
                ids_npl = df_show["ID"].astype(str).tolist()
                id_npl_sel = st.selectbox("Selecciona crédito por ID", ids_npl, key="npl_id_sel")
                if id_npl_sel:
                    row_npl = df_show[df_show["ID"].astype(str) == id_npl_sel].iloc[0]
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"**LTV:** `{row_npl['LTV (%)']:.1f}%`  ·  **Nivel:** `{row_npl['Nivel LTV']}`")
                        st.markdown(f"**OB/Deuda:** `€ {row_npl['OB / Deuda (€)']:,.0f}`")
                        st.markdown(f"**Valor mercado est.:** `€ {row_npl['Valor Mercado Est. (€)']:,.0f}`")
                        st.markdown(f"**Margen bruto:** `€ {row_npl['Margen bruto (€)']:,.0f}`")
                        st.markdown(f"**ROI s/compra:** `{row_npl['ROI s/compra (%)']:.1f}%`")
                        st.markdown(f"**Riesgo zona:** {semaforo_html(row_npl['Riesgo zona'])}", unsafe_allow_html=True)
                    with c2:
                        pdf_npl = generar_pdf_npl(row_npl)
                        st.download_button("📥 Descargar PDF ficha NPL", pdf_npl,
                                           f"NPL_{id_npl_sel}.pdf", "application/pdf")

                st.subheader("📈 Análisis visual NPL")
                nt1, nt2, nt3, nt4 = st.tabs(["LTV Distribution", "OB vs Mercado", "Por municipio", "ROI vs LTV"])

                with nt1:
                    ltv_counts = df_show["Nivel LTV"].value_counts().reset_index()
                    ltv_counts.columns = ["Nivel", "Cantidad"]
                    orden = ["EXCELENTE", "BUENA", "AJUSTADA", "NEUTRAL", "NEGATIVA"]
                    ltv_counts["Nivel"] = pd.Categorical(ltv_counts["Nivel"], categories=orden, ordered=True)
                    ltv_counts = ltv_counts.sort_values("Nivel")
                    fig_ltv = px.bar(ltv_counts, x="Nivel", y="Cantidad",
                                     color="Nivel",
                                     color_discrete_map={"EXCELENTE": "#28a745", "BUENA": "#ffc107",
                                                         "AJUSTADA": "#fd7e14", "NEUTRAL": "#6c757d", "NEGATIVA": "#dc3545"},
                                     title="Distribución por nivel de LTV")
                    st.plotly_chart(fig_ltv, use_container_width=True)

                with nt2:
                    fig_ob = px.scatter(df_show, x="OB / Deuda (€)", y="Valor Mercado Est. (€)",
                                        color="Nivel LTV",
                                        color_discrete_map={"EXCELENTE": "#28a745", "BUENA": "#ffc107",
                                                            "AJUSTADA": "#fd7e14", "NEUTRAL": "#6c757d", "NEGATIVA": "#dc3545"},
                                        hover_data=["ID", "Municipio", "LTV (%)"],
                                        title="OB (Deuda) vs Valor de Mercado estimado")
                    max_val = max(df_show["OB / Deuda (€)"].max(), df_show["Valor Mercado Est. (€)"].max())
                    fig_ob.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val],
                                                mode="lines", line=dict(dash="dash", color="gray"),
                                                name="OB = Mercado (LTV 100%)"))
                    st.plotly_chart(fig_ob, use_container_width=True)

                with nt3:
                    muni_npl = (df_show.groupby("Municipio")
                                .agg(n=("ID", "count"),
                                     ob_total=("OB / Deuda (€)", "sum"),
                                     ltv_medio=("LTV (%)", "mean"))
                                .reset_index().sort_values("ob_total", ascending=False).head(15))
                    fig_muni = px.bar(muni_npl, x="Municipio", y="ob_total",
                                      color="ltv_medio", color_continuous_scale="RdYlGn_r",
                                      hover_data=["n", "ltv_medio"],
                                      title="OB total por municipio (color = LTV medio)")
                    fig_muni.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_muni, use_container_width=True)

                with nt4:
                    fig_roi = px.scatter(df_show, x="LTV (%)", y="ROI s/compra (%)",
                                         color="Riesgo zona",
                                         color_discrete_map={"BAJA": "#28a745", "MEDIA": "#ffc107",
                                                             "ALTA": "#dc3545", "REVISAR": "#6c757d"},
                                         hover_data=["ID", "Municipio", "Nivel LTV"],
                                         title="ROI sobre compra vs LTV — por riesgo de zona")
                    fig_roi.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="ROI = 0")
                    st.plotly_chart(fig_roi, use_container_width=True)

                st.subheader("📥 Exportar resultados NPL")
                cols_export_npl = [c for c in df_show.columns if not c.startswith("_")]
                out_npl = BytesIO()
                with pd.ExcelWriter(out_npl, engine="openpyxl") as writer:
                    df_show[cols_export_npl].to_excel(writer, index=False, sheet_name="NPL_Resultados")
                st.download_button("📥 Descargar Excel NPL", out_npl.getvalue(), "okupro_v7_npl.xlsx")

                st.info("""
                ℹ️ **Nota sobre el valor de mercado estimado:** Se calcula usando el precio €/m² medio de la zona 
                y una superficie estándar (80m² vivienda / 150m² casa) cuando no hay datos de superficie en el archivo. 
                Para mayor precisión, usa un Excel de precios personalizados o integra la API del Catastro.
                """)

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.info("📂 Sube el Excel NPL del fondo para comenzar el análisis")
        with st.expander("ℹ️ Columnas esperadas en el Excel NPL"):
            st.markdown("""
| Columna | Nombres reconocidos | Notas |
|---------|---------------------|-------|
| **Deuda (OB)** | `OB`, `Deuda`, `Saldo`, `Outstanding`, `Balance` | ⚠️ **No es la tasación** |
| Referencia catastral | `CD Referencia Catastral`, `Referencia Catastral` | Para identificar el inmueble |
| Municipio | `Municipio`, `Poblacion`, `Ciudad` | Obligatorio |
| Dirección | `Dirección Completa Inmueble`, `Direccion`, `Calle` | Para riesgo de zona |
| Código Postal | `Código Postal`, `CP` | Para riesgo de barrio |
| Tipo inmueble | `Tipo Inmueble`, `Tipo` | VIVIENDA / CASA |
| PL/NPL | `PL NPL`, `Tipo cartera` | Distingue performing de non-performing |
            """)

st.markdown("---")
st.caption("OKUPRO v7.1 · Cartera OkuPro + Módulo NPL · Scoring multidimensional · LTV & Margen inversor · PDF por inmueble")
"Añadido módulo NPL completo y UI"
