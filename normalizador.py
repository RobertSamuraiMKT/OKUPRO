import unicodedata
import re
import pandas as pd

# ─── Mapeo de sinónimos por categoría ──────────────────────────────
SINONIMOS = {
    "municipio": [
        "municipio", "poblacion", "población", "ciudad", "localidad",
        "city", "town", "municipality", "ayuntamiento"
    ],
    "direccion": [
        "direccion", "dirección", "domicilio", "calle", "address",
        "street", "via", "avenida", "plaza", "camino"
    ],
    "precio": [
        "pvp", "precio", "importe", "valor", "euros", "price",
        "amount", "value", "coste", "venta", "tasación", "tasacion"
    ],
    "superficie": [
        "superficie", "metros", "m2", "construidos", "construida",
        "area", "sqm", "size", "surface", "metros2"
    ],
    "cp": [
        "postal", "cp", "codigopostal", "códigopostal",
        "zip", "zipcode", "codigo postal", "código postal"
    ],
    "id": [
        "id", "expediente", "prinex", "inmueble", "identificador",
        "referencia", "ref", "identificacion"
    ],
    "ccaa": [
        "ccaa", "comunidad", "autonomia", "autonomía", "region",
        "provincia", "comunidad autonoma"
    ],
    "tipo": [
        "tipo", "categoria", "categoría", "clase", "tipologia",
        "type", "category", "clasificacion"
    ],
    "ob_deuda": [
        "ob", "deuda", "saldo", "outstanding", "balance",
        "principal", "importe deuda", "deuda pendiente"
    ],
    "id_inmueble_completo": [
        "id inmueble completo", "id_inmueble_completo",
        "cd inmueble", "referencia inmueble"
    ],
    "okupado_fase_sae": [
        "okupado", "ocupado", "fase sae", "estado ocupación",
        "situacion ocupacion", "occupied", "sae phase"
    ]
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
    "BARCELONA": "BARCELONA",
    "BADALONA": "BADALONA",
    "SABADELL": "SABADELL",
    "TERRASSA": "TERRASSA",
    "SANTA COLOMA DE GRAMENET": "SANTA COLOMA DE GRAMENET",
    "RUBÍ": "RUBI",
    "RUBI": "RUBI",
    "CORNELLÀ": "CORNELLA DE LLOBREGAT",
    "CORNELLA DE LLOBREGAT": "CORNELLA DE LLOBREGAT",
    "SANT BOI": "SANT BOI DE LLOBREGAT",
    "SANT BOI DE LLOBREGAT": "SANT BOI DE LLOBREGAT",
    "GRANOLLERS": "GRANOLLERS",
    "MANRESA": "MANRESA",
    "MOLLET DEL VALLÈS": "MOLLET DEL VALLES",
    "MOLLET DEL VALLES": "MOLLET DEL VALLES",
    "TORDERA": "TORDERA",
    "BLANES": "BLANES",
    "SALT": "SALT",
    "GIRONA": "GIRONA",
    "FIGUERES": "FIGUERES",
    "OLOT": "OLOT",
    "VIDRERES": "VIDRERES",
    "PALAMÓS": "PALAMOS",
    "PALAMOS": "PALAMOS",
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
    """Unifica los tipos de inmueble en categorías estándar"""
    if not isinstance(valor, str):
        return "PISO"
    valor = valor.upper().strip()
    if "PISO" in valor or "VIVIENDA" in valor or "FLAT" in valor or "APART" in valor or "DUPLEX" in valor:
        return "PISO"
    elif "CASA" in valor or "CHALET" in valor or "HOUSE" in valor or "VILLA" in valor or "UNIFAM" in valor:
        return "CASA"
    elif "LOCAL" in valor or "COMERCIAL" in valor or "SHOP" in valor:
        return "LOCAL"
    elif "GARAJE" in valor or "PARKING" in valor or "GARAGE" in valor:
        return "GARAJE"
    elif "NAVE" in valor or "INDUSTRIAL" in valor or "WAREHOUSE" in valor:
        return "NAVE"
    elif "SUELO" in valor or "SOLAR" in valor or "TERRENO" in valor:
        return "SUELO"
    else:
        return "OTRO"

def encontrar_columna_inteligente(df, posibles, buscar_en=None):
    """
    Busca una columna en el DataFrame usando múltiples estrategias.
    - posibles: lista de categorías a buscar (ej. ["municipio"])
    - buscar_en: si se pasa, solo busca en esa lista de columnas
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
  "Añadido motor de normalización de columnas"
