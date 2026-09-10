import unicodedata
import re
import pandas as pd

# ─── Sinónimos SOLO para las columnas que importan ──────────────
SINONIMOS = {
    "municipio": [
        "municipio", "poblacion", "población", "ciudad", "localidad",
        "city", "town", "municipality", "POBLACION"
    ],
    "direccion": [
        "direccion", "dirección", "domicilio", "calle", "address",
        "street", "descripcion_ur", "descripcion ur", "DIRECCION"
    ],
    "precio": [
        "pvp", "PVP", "Pvp",
        "precio", "PRECIO", "precio venta",
        "importe", "valor", "euros", "price", "coste", "venta"
    ],
    "superficie": [
        "superficie", "metros", "m2", "construidos", "construida",
        "area", "sqm", "size", "surface",
        "superficie_construida", "SUPERFICIE_CONSTRUIDA",
        "sup construida", "m²"
    ],
    "cp": [
        "postal", "cp", "codigo postal", "código postal",
        "cod_postal", "COD_POSTAL", "zip", "zipcode"
    ],
    "id": [
        "id inmueble completo", "id_inmueble_completo",
        "id inmueble", "Id inmueble completo", "ID INMUEBLE COMPLETO",
        "id de producto", "Id de Producto", "id producto",
        "expediente", "referencia"
    ],
    "ccaa": [
        "ccaa", "comunidad", "autonomia", "autonomía",
        "provincia", "PROVINCIA", "comunidad autonoma",
        "comunidad autónoma", "region"
    ],
    "okupado_fase_sae": [
        "okupado - fase sae", "OKUPADO - FASE SAE",
        "okupado", "ocupado", "fase sae",
        "estado ocupación", "situacion ocupacion",
        "situación judicial", "tipo ocupante"
    ],
    "vulnerabilidad": [
        "vulnerabilidad", "VULNERABILIDAD", "vulnerable",
        "porpob_bbvv_11", "riesgo zona"
    ],
}

# ─── Mapeo de municipios (variantes → normalizado) ──────────────────
MUNICIPIOS_MAP = {
    "LHOSPITALET": "L'HOSPITALET DE LLOBREGAT",
    "HOSPITALET": "L'HOSPITALET DE LLOBREGAT",
    "HOSPITALET DE LLOBREGAT": "L'HOSPITALET DE LLOBREGAT",
    "MATARÓ": "MATARO",
    "MATARO": "MATARO",
    "VILANOVA I LA GELTRÚ": "VILANOVA I LA GELTRU",
    "VILANOVA I LA GELTRU": "VILANOVA I LA GELTRU",
    "CORNELLÀ": "CORNELLA DE LLOBREGAT",
    "CORNELLA DE LLOBREGAT": "CORNELLA DE LLOBREGAT",
    "SANT BOI": "SANT BOI DE LLOBREGAT",
    "SANT BOI DE LLOBREGAT": "SANT BOI DE LLOBREGAT",
    "SANT ADRIÀ DE BESÒS": "SANT ADRIA DE BESOS",
    "SANT ADRIA DE BESOS": "SANT ADRIA DE BESOS",
    "SANT VICENÇ DELS HORTS": "SANT VICENS DELS HORTS",
    "SANT VICENS DELS HORTS": "SANT VICENS DELS HORTS",
    "ESPARREGUERA": "ESPARRAGUERA",
    "ESPARRAGUERA": "ESPARRAGUERA",
    "MASNOU": "MASNOU EL",
    "MASNOU EL": "MASNOU EL",
    "PREMIÀ DE MAR": "PREMIÀ DE MAR",
    "L'HOSPITALET DE LLOBREGAT": "L'HOSPITALET DE LLOBREGAT",
    "HOSPITALET DE LLOBREGAT": "L'HOSPITALET DE LLOBREGAT",
    "LOS REALEJOS": "REALEJOS",
    "REALEJOS": "REALEJOS",
}

# ─── Funciones auxiliares ────────────────────────────────────────────

def normalizar_texto(texto):
    """Elimina acentos, convierte a minúsculas y limpia espacios"""
    if not isinstance(texto, str):
        return ""
    texto = texto.lower().strip()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    texto = re.sub(r'[^a-z0-9 ]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def normalizar_municipio(valor):
    """Normaliza el nombre de un municipio"""
    if not isinstance(valor, str):
        return valor
    valor = valor.strip().upper()
    valor_norm = normalizar_texto(valor)
    for clave, mapeado in MUNICIPIOS_MAP.items():
        if normalizar_texto(clave) in valor_norm or valor_norm in normalizar_texto(clave):
            return mapeado
    return valor

def normalizar_tipo_inmueble(valor):
    """Unifica los tipos de inmueble"""
    if not isinstance(valor, str):
        return "PISO"
    valor = valor.upper().strip()
    if any(x in valor for x in ["PISO", "VIVIENDA", "FLAT", "APART", "DUPLEX", "APTO"]):
        return "PISO"
    elif any(x in valor for x in ["CASA", "CHALET", "HOUSE", "VILLA", "UNIFAM", "ADOSADO"]):
        return "CASA"
    elif any(x in valor for x in ["LOCAL", "COMERCIAL", "SHOP"]):
        return "LOCAL"
    elif any(x in valor for x in ["GARAJE", "PARKING", "GARAGE", "PLAZA"]):
        return "GARAJE"
    elif any(x in valor for x in ["NAVE", "INDUSTRIAL", "WAREHOUSE"]):
        return "NAVE"
    elif any(x in valor for x in ["SUELO", "SOLAR", "TERRENO", "RUSTICA"]):
        return "SUELO"
    return "OTRO"

def encontrar_columna_inteligente(df, posibles, buscar_en=None):
    """
    Busca una columna en el DataFrame usando múltiples estrategias.
    """
    columnas = buscar_en if buscar_en else df.columns
    for col in columnas:
        col_norm = normalizar_texto(col)
        for categoria in posibles:
            sinonimos = SINONIMOS.get(categoria, [])
            for sinonimo in sinonimos:
                sinonimo_norm = normalizar_texto(sinonimo)
                if sinonimo_norm in col_norm or col_norm in sinonimo_norm:
                    return col
    return None
