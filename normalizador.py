import unicodedata
import re
import pandas as pd

# ─── Mapeo de sinónimos por categoría (VERSIÓN AMPLIADA) ──────────────
SINONIMOS = {
    "municipio": [
        "municipio", "poblacion", "población", "ciudad", "localidad",
        "city", "town", "municipality", "ayuntamiento",
        "poblacion", "poblation", "town"
    ],
    "direccion": [
        "direccion", "dirección", "domicilio", "calle", "address",
        "street", "via", "avenida", "plaza", "camino",
        "dirección completa", "direccion completa", "dir", "calle",
        "direccion", "dirección", "ubicacion", "ubicación"
    ],
    "precio": [
        "pvp", "precio", "importe", "valor", "euros", "price",
        "amount", "value", "coste", "venta", "tasación", "tasacion",
        "precio de referencia", "€ pvp", "precio", "euros",
        "precio venta", "valor tasacion", "importe total demandado",
        "tipo para subasta", "precio referencia", "precio cierre"
    ],
    "superficie": [
        "superficie", "metros", "m2", "construidos", "construida",
        "area", "sqm", "size", "surface", "metros2",
        "superficie_construida", "superficie construida",
        "superficie construida m²", "sup construida", "s m²",
        "m²", "m2 construidos"
    ],
    "cp": [
        "postal", "cp", "codigopostal", "códigopostal",
        "zip", "zipcode", "codigo postal", "código postal",
        "cp", "codigo postal", "zip code", "postal code"
    ],
    "id": [
        "id", "expediente", "prinex", "inmueble", "identificador",
        "referencia", "ref", "identificacion",
        "id inmueble completo", "id producto", "property id",
        "property idh", "idh", "id de producto"
    ],
    "ccaa": [
        "ccaa", "comunidad", "autonomia", "autonomía", "region",
        "provincia", "comunidad autonoma", "comunidad autónoma",
        "comunidad", "autonomia", "autonomía"
    ],
    "tipo": [
        "tipo", "categoria", "categoría", "clase", "tipologia",
        "type", "category", "clasificacion",
        "tipo inmueble", "tipología", "property type"
    ],
    "ob_deuda": [
        "ob", "deuda", "saldo", "outstanding", "balance",
        "principal", "importe deuda", "deuda pendiente"
    ],
    "id_inmueble_completo": [
        "id inmueble completo", "id_inmueble_completo",
        "cd inmueble", "referencia inmueble",
        "id inmueble", "inmueble id"
    ],
    "okupado_fase_sae": [
        "okupado", "ocupado", "fase sae", "estado ocupación",
        "situacion ocupacion", "occupied", "sae phase",
        "okupado - fase sae", "estado producto",
        "situación ocupación", "tipo ocupante",
        "situación judicial", "situacion judicial",
        "tf_sae.ds_juzgados", "tf_sae ds juzgados"
    ],
    "provincia": [
        "provincia", "province", "provincia",
        "comunidad autónoma", "comunidad"
    ],
    "poblacion": [
        "poblacion", "población", "municipio", "ciudad", "town",
        "city", "poblation", "localidad"
    ],
    "referencia_catastral": [
        "referencia catastral", "ref_catastral", "catastral",
        "cadastral reference", "ref catastral", "cd referencia"
    ],
    "dormitorios": [
        "dormitorios", "habitaciones", "rooms", "bedrooms",
        "nº dormitorios", "numero dormitorios",
        "nº habitaciones", "número habitaciones",
        "num dormitorios", "num habitaciones"
    ],
    "banos": [
        "baños", "banos", "bathrooms", "baths",
        "nº baños", "numero baños", "num baños"
    ],
    "fecha_subasta": [
        "fecha subasta", "subasta fecha", "fecha de subasta",
        "auction date", "fecha cesion de remate", "fecha cesión"
    ],
    "tipo_subasta": [
        "tipo para subasta", "tipo subasta", "tipo de subasta",
        "auction type", "legal type"
    ],
    "estado_producto": [
        "estado producto", "estado", "status",
        "estado del producto", "situacion", "situación"
    ],
    "vulnerabilidad": [
        "vulnerabilidad", "vulnerable", "vulnerabilidad",
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
    "LLORET DE MAR": "LLORET DE MAR",
    "REUS": "REUS",
    "TARRAGONA": "TARRAGONA",
    "VALLS": "VALLS",
    "VENDRELL": "VENDRELL EL",
    "VENDRELL EL": "VENDRELL EL",
    "CALAFELL": "CALAFELL",
    "CUBELLES": "CUBELLES",
    "GELIDA": "GELIDA",
    "OLESA DE MONTSERRAT": "OLESA DE MONTSERRAT",
    "SANT FELIU DE LLOBREGAT": "SANT FELIU DE LLOBREGAT",
    "SANT BOI DE LLOBREGAT": "SANT BOI DE LLOBREGAT",
    "SANT ADRIA DE BESOS": "SANT ADRIA DE BESOS",
    "SANT ADRIÀ DE BESÒS": "SANT ADRIA DE BESOS",
    "SANT PERE DE RIBES": "SANT PERE DE RIBES",
    "SANT VICENÇ DELS HORTS": "SANT VICENS DELS HORTS",
    "SANT VICENS DELS HORTS": "SANT VICENS DELS HORTS",
    "ESPARRAGUERA": "ESPARRAGUERA",
    "ESPARREGUERA": "ESPARRAGUERA",
    "RIPOLLET": "RIPOLLET",
    "MONTGAT": "MONTGAT",
    "MASNOU": "MASNOU EL",
    "MASNOU EL": "MASNOU EL",
    "PREMIÀ DE MAR": "PREMIÀ DE MAR",
    "PREMIÀ DE MAR": "PREMIÀ DE MAR",
    "PALAFRUGELL": "PALAFRUGELL",
    "L'HOSPITALET DE LLOBREGAT": "L'HOSPITALET DE LLOBREGAT",
    "HOSPITALET DE LLOBREGAT": "L'HOSPITALET DE LLOBREGAT",
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
    if "PISO" in valor or "VIVIENDA" in valor or "FLAT" in valor or "APART" in valor or "DUPLEX" in valor or "PISO" in valor or "APARTAMENTO" in valor or "APTO" in valor:
        return "PISO"
    elif "CASA" in valor or "CHALET" in valor or "HOUSE" in valor or "VILLA" in valor or "UNIFAM" in valor or "ADOSADO" in valor:
        return "CASA"
    elif "LOCAL" in valor or "COMERCIAL" in valor or "SHOP" in valor or "COMERCIAL" in valor:
        return "LOCAL"
    elif "GARAJE" in valor or "PARKING" in valor or "GARAGE" in valor or "PLAZA" in valor:
        return "GARAJE"
    elif "NAVE" in valor or "INDUSTRIAL" in valor or "WAREHOUSE" in valor:
        return "NAVE"
    elif "SUELO" in valor or "SOLAR" in valor or "TERRENO" in valor or "SUELO" in valor or "RUSTICA" in valor:
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
