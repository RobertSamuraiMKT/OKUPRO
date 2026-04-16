import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import numpy as np
import re

st.set_page_config(page_title="OKUPRO - Analizador de Oportunidades", layout="wide")
st.title("🏠 OKUPRO")
st.subheader("Analizador de carteras inmobiliarias (ocupados, bancarios, SAREB)")

# ------------------------------------------------------------
# 1. PRECIOS DE MERCADO BASE POR MUNICIPIO (€/m² venta y alquiler)
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# 2. FUNCIÓN PARA ENCONTRAR COLUMNAS FLEXIBLES
# ------------------------------------------------------------
def encontrar_columna(df, posibles_nombres):
    """Busca una columna en el DataFrame que coincida con alguno de los posibles nombres"""
    for col in df.columns:
        col_lower = col.lower().strip()
        for nombre in posibles_nombres:
            if nombre.lower() in col_lower:
                return col
    return None

# ------------------------------------------------------------
# 3. DESCUENTO POR RANGO DE PRECIO
# ------------------------------------------------------------
def calcular_descuento(precio_original):
    if precio_original < 70000:
        descuento = 0.25      # 25%
    elif precio_original < 150000:
        descuento = 0.225     # 22.5%
    elif precio_original < 200000:
        descuento = 0.20      # 20%
    else:
        descuento = 0.19      # 19%
    return descuento

def calcular_precio_ofertado(precio_original):
    return precio_original * (1 - calcular_descuento(precio_original))

# ------------------------------------------------------------
# 4. MAPA DE CÓDIGOS POSTALES A BARRIOS
# ------------------------------------------------------------
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
    "08227": "SANT LLORENÇ", "08228": "LES ARENES",
    "08201": "CENTRE", "08202": "CREU DE BARBERÀ", "08203": "CAN RULL",
    "08204": "GRÀCIA", "08205": "EL VAPOR", "08206": "LA SALUT",
    "08207": "SOL I PADRIS", "08208": "CAN FEU",
}

BARRIOS_RIESGO_ALTO = [
    "FLORIDA", "LA SALUT", "ALFONSO XII", "CIUTAT VELLA", "RAVAL",
    "EL BESÒS", "LA MINA", "SANT ROC", "LLEFIÀ", "COLLBLANC",
    "PUBILLA CASAS", "LA TORRASSA", "CAN RULL", "CAN BOSCH"
]

def extraer_barrio_avanzado(direccion, codigo_postal):
    barrio = "default"
    origen = "DEFAULT"
    
    if codigo_postal and str(codigo_postal) in CP_BARRIOS:
        barrio = CP_BARRIOS[str(codigo_postal)]
        origen = "CÓDIGO POSTAL"
        return barrio, origen
    
    if isinstance(direccion, str):
        direccion_upper = direccion.upper()
        for b in BARRIOS_RIESGO_ALTO:
            if b in direccion_upper:
                return b, "DIRECCIÓN"
    
    return barrio, origen

# ------------------------------------------------------------
# 5. CARGA DE VULNERABILIDAD REAL
# ------------------------------------------------------------
@st.cache_data
def cargar_vulnerabilidad_real(ruta_excel="1_0_BD_Municipios_1991_2001_2006_2011.xlsx"):
    try:
        df = pd.read_excel(ruta_excel, sheet_name="BD")
        df.columns = df.columns.str.strip()
        vulnerabilidad = {}
        for _, row in df.iterrows():
            municipio = str(row.get("MUNICIPIO", "")).upper().strip()
            if not municipio or municipio == "NAN":
                continue
            porc_vuln = row.get("PORPOB_BBVV_11", 0)
            if pd.isna(porc_vuln):
                porc_vuln = 0
            vulnerabilidad[municipio] = porc_vuln
        return vulnerabilidad
    except Exception as e:
        st.warning(f"⚠️ No se pudo cargar vulnerabilidad: {e}")
        return {}

def obtener_riesgo_real(municipio, direccion, codigo_postal, vulnerabilidad_dict):
    municipio_upper = municipio.upper().strip()
    barrio, origen_barrio = extraer_barrio_avanzado(direccion, codigo_postal)
    porc_vuln = vulnerabilidad_dict.get(municipio_upper, None)
    
    if porc_vuln is None:
        porc_vuln = 10.0
        origen = f"⚠️ POR DEFECTO (barrio: {barrio})"
        penalizacion = 0
        recomendacion = "⚠️ REVISAR MANUALMENTE - Municipio sin datos oficiales"
        nivel = "REVISAR"
    else:
        origen = f"REAL (MITMA) - barrio: {barrio}"
        if barrio.upper() in BARRIOS_RIESGO_ALTO:
            nivel = "ALTA"
            penalizacion = -0.5
            recomendacion = f"⚠️ BARRIO VULNERABLE DETECTADO ({barrio}) - Solo expertos"
        elif porc_vuln > 20:
            nivel = "ALTA"
            penalizacion = -0.5
            recomendacion = f"⚠️ {porc_vuln:.1f}% población vulnerable - Solo expertos"
        elif porc_vuln > 10:
            nivel = "MEDIA"
            penalizacion = -0.25
            recomendacion = f"⚠️ {porc_vuln:.1f}% población vulnerable - Evaluar con precaución"
        else:
            nivel = "BAJA"
            penalizacion = 0
            recomendacion = f"✅ Zona consolidada ({porc_vuln:.1f}% vulnerable)"
    
    return nivel, penalizacion, recomendacion, porc_vuln, origen, barrio, origen_barrio

# ------------------------------------------------------------
# 6. FUNCIONES DE ANÁLISIS
# ------------------------------------------------------------
def obtener_tipo_inmueble(superficie):
    return "PISO" if superficie < 150 else "CASA"

def obtener_precios_mercado(poblacion, tipo, superficie):
    base = PRECIOS_BASE.get(poblacion, {"venta": 2000, "alquiler": 12.0})
    if tipo == "PISO":
        factor_venta = 1.0
        factor_alquiler = 1.0
    else:
        if superficie > 500:
            factor_venta = 0.5
            factor_alquiler = 0.6
        elif superficie > 300:
            factor_venta = 0.6
            factor_alquiler = 0.7
        else:
            factor_venta = 0.7
            factor_alquiler = 0.8
    return {
        "venta": base["venta"] * factor_venta,
        "alquiler": base["alquiler"] * factor_alquiler
    }

def procesar_excel(df, tipo_filtro):
    # Buscar columnas flexiblemente
    col_id = encontrar_columna(df, ["id", "prinex", "expediente", "inmueble"])
    col_municipio = encontrar_columna(df, ["municipio", "poblacion", "ciudad", "localidad"])
    col_direccion = encontrar_columna(df, ["direccion", "domicilio", "calle", "address"])
    col_cp = encontrar_columna(df, ["postal", "cp", "codigo postal"])
    col_superficie = encontrar_columna(df, ["superficie", "metros", "m2", "construidos"])
    col_precio = encontrar_columna(df, ["pvp", "precio", "importe", "valor", "euros"])
    
    # Verificar que encontramos lo mínimo necesario
    if not col_municipio:
        st.error("❌ No se encontró una columna de municipio/población. Las columnas disponibles son: " + ", ".join(df.columns))
        return pd.DataFrame()
    
    if not col_precio:
        st.error("❌ No se encontró una columna de precio (PVP, precio, importe...).")
        return pd.DataFrame()
    
    if not col_superficie:
        st.warning("⚠️ No se encontró columna de superficie. Algunos inmuebles podrían no procesarse.")
    
    vulnerabilidad_dict = cargar_vulnerabilidad_real()
    
    resultados = []
    for idx, row in df.iterrows():
        try:
            # Obtener valores usando las columnas encontradas
            municipio = str(row.get(col_municipio, ""))
            precio_original = float(row.get(col_precio, 0)) if row.get(col_precio) else 0
            
            # Superficie (si no existe, intentar extraer de dirección o poner 0)
            superficie = 0
            if col_superficie:
                try:
                    superficie = float(row.get(col_superficie, 0))
                except:
                    superficie = 0
            
            direccion = str(row.get(col_direccion, "")) if col_direccion else ""
            codigo_postal = str(row.get(col_cp, "")) if col_cp else ""
            id_inmueble = str(row.get(col_id, "")) if col_id else ""
            
            if superficie <= 0 or precio_original <= 0 or not municipio:
                continue
            
            tipo = obtener_tipo_inmueble(superficie)
            if tipo_filtro == "Solo pisos" and tipo != "PISO":
                continue
            if tipo_filtro == "Solo casas" and tipo != "CASA":
                continue
            
            precio_ofertado = calcular_precio_ofertado(precio_original)
            descuento_aplicado = calcular_descuento(precio_original)
            
            mercado = obtener_precios_mercado(municipio, tipo, superficie)
            precio_venta_estimado = superficie * mercado["venta"]
            roi_flip = (precio_venta_estimado - precio_ofertado) / precio_ofertado * 100 if precio_ofertado > 0 else 0
            alquiler_mensual = superficie * mercado["alquiler"]
            rentabilidad_alquiler = (alquiler_mensual * 12) / precio_ofertado * 100 if precio_ofertado > 0 else 0
            
            nivel_riesgo, penalizacion, recomendacion, porc_vuln, origen_riesgo, barrio, origen_barrio = obtener_riesgo_real(
                municipio, direccion, codigo_postal, vulnerabilidad_dict
            )
            
            score_base = (roi_flip / 20) + (rentabilidad_alquiler / 10)
            ranking_ajustado = max(0, min(5, score_base + penalizacion))
            
            resultados.append({
                "ID": id_inmueble,
                "Municipio": municipio,
                "Dirección": direccion[:50] + "..." if len(str(direccion)) > 50 else direccion,
                "Barrio": barrio,
                "Origen barrio": origen_barrio,
                "Tipo": tipo,
                "Superficie (m²)": superficie,
                "Precio original (€)": precio_original,
                "Descuento %": round(descuento_aplicado * 100, 1),
                "Precio oferta (€)": round(precio_ofertado, 2),
                "ROI Flip (%)": round(roi_flip, 1),
                "Rentabilidad alquiler (%)": round(rentabilidad_alquiler, 1),
                "Riesgo zona": nivel_riesgo,
                "% Vulnerable": porc_vuln,
                "Origen riesgo": origen_riesgo,
                "Recomendación": recomendacion,
                "Ranking OKUPRO": round(ranking_ajustado, 1)
            })
        except Exception as e:
            continue
            
    df_resultado = pd.DataFrame(resultados)
    if len(df_resultado) > 0:
        df_resultado = df_resultado.sort_values("Ranking OKUPRO", ascending=False)
    return df_resultado

# ------------------------------------------------------------
# 7. INTERFAZ STREAMLIT
# ------------------------------------------------------------
st.sidebar.header("⚙️ Configuración")

tipo_filtro = st.sidebar.radio(
    "Tipo de inmueble:",
    ["Todos", "Solo pisos", "Solo casas"],
)

top_n = st.sidebar.slider("Número de resultados a mostrar", 10, 100, 25, step=5)
mostrar_solo_riesgo_bajo = st.sidebar.checkbox("Mostrar solo riesgo BAJO", value=False)
mostrar_solo_revisar = st.sidebar.checkbox("Mostrar solo los que requieren revisión manual", value=False)

archivo = st.file_uploader("📂 Sube tu archivo Excel", type=["xlsx", "xls"])

if archivo is not None:
    try:
        df_raw = pd.read_excel(archivo)
        st.success(f"✅ Archivo cargado: {len(df_raw)} filas")
        
        # Mostrar columnas detectadas
        with st.expander("🔍 Ver columnas detectadas"):
            col_id = encontrar_columna(df_raw, ["id", "prinex", "expediente", "inmueble"])
            col_mun = encontrar_columna(df_raw, ["municipio", "poblacion", "ciudad", "localidad"])
            col_dir = encontrar_columna(df_raw, ["direccion", "domicilio", "calle", "address"])
            col_cp = encontrar_columna(df_raw, ["postal", "cp", "codigo postal"])
            col_sup = encontrar_columna(df_raw, ["superficie", "metros", "m2", "construidos"])
            col_pre = encontrar_columna(df_raw, ["pvp", "precio", "importe", "valor", "euros"])
            st.write(f"📌 **ID:** {col_id or '❌ No encontrada'}")
            st.write(f"📌 **Municipio:** {col_mun or '❌ No encontrada'}")
            st.write(f"📌 **Dirección:** {col_dir or '❌ No encontrada'}")
            st.write(f"📌 **Código Postal:** {col_cp or '❌ No encontrada'}")
            st.write(f"📌 **Superficie:** {col_sup or '❌ No encontrada'}")
            st.write(f"📌 **Precio:** {col_pre or '❌ No encontrada'}")
        
        with st.spinner("Procesando..."):
            df_resultados = procesar_excel(df_raw, tipo_filtro)
        
        if mostrar_solo_riesgo_bajo and len(df_resultados) > 0:
            df_resultados = df_resultados[df_resultados["Riesgo zona"] == "BAJA"]
        
        if mostrar_solo_revisar and len(df_resultados) > 0:
            df_resultados = df_resultados[df_resultados["Riesgo zona"] == "REVISAR"]
        
        if len(df_resultados) > 0:
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.metric("🏠 Total analizados", len(df_resultados))
            col2.metric("📐 Pisos", len(df_resultados[df_resultados["Tipo"] == "PISO"]))
            col3.metric("🏡 Casas", len(df_resultados[df_resultados["Tipo"] == "CASA"]))
            col4.metric("💰 ROI Flip medio", f"{df_resultados['ROI Flip (%)'].mean():.1f}%")
            col5.metric("⚠️ Riesgo ALTO", len(df_resultados[df_resultados["Riesgo zona"] == "ALTA"]))
            col6.metric("🔍 Revisar manual", len(df_resultados[df_resultados["Riesgo zona"] == "REVISAR"]))
            
            st.subheader(f"🏆 TOP {top_n} Oportunidades (por Ranking OKUPRO)")
            st.dataframe(df_resultados.head(top_n))
            
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            
            axes[0,0].hist(df_resultados["ROI Flip (%)"].head(top_n), bins=15, edgecolor="black", color="skyblue")
            axes[0,0].set_xlabel("ROI Flip (%)")
            axes[0,0].set_title("Distribución de ROI Flip")
            
            top_munis = df_resultados.head(top_n)["Municipio"].value_counts().head(5)
            axes[0,1].bar(top_munis.index, top_munis.values, color="lightcoral")
            axes[0,1].set_xlabel("Municipio")
            axes[0,1].set_title("Municipios con más oportunidades")
            plt.setp(axes[0,1].xaxis.get_majorticklabels(), rotation=45)
            
            axes[1,0].scatter(df_resultados["Rentabilidad alquiler (%)"], df_resultados["Ranking OKUPRO"], alpha=0.6, c="green")
            axes[1,0].set_xlabel("Rentabilidad alquiler (%)")
            axes[1,0].set_ylabel("Ranking OKUPRO")
            axes[1,0].set_title("Relación Rentabilidad - Ranking")
            
            riesgos = df_resultados["Riesgo zona"].value_counts()
            axes[1,1].pie(riesgos, labels=riesgos.index, autopct="%1.1f%%", startangle=90, 
                         colors=["red", "orange", "green", "gray"])
            axes[1,1].set_title("Distribución de riesgo por zona")
            
            plt.tight_layout()
            st.pyplot(fig)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_resultados.to_excel(writer, index=False, sheet_name="OKUPRO_Resultados")
            st.download_button("📥 Descargar Excel completo", output.getvalue(), "okupy_resultados.xlsx")
        else:
            st.warning("⚠️ No se encontraron inmuebles con los filtros seleccionados.")
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
else:
    st.info("📂 Sube un archivo Excel para comenzar")

st.markdown("---")
st.caption("OKUPRO v5.0 - Detecta columnas automáticamente: municipio, dirección, precio, superficie...")