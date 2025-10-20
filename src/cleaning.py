# cleaning.py
import pandas as pd
import numpy as np
pd.options.display.float_format = '{:,.0f}'.format

import unicodedata
import re

def clean_data(df, cotizacion_usd=1350):  # ajustá el tipo de cambio aquí
    df = df.copy()

    # Normalizar columnas esperadas
    for col in ["Dormitorios","Baños","Ambientes","Cocheras","Toilettes","Sup. cubierta","Antiguedad"]:
        if col not in df.columns: df[col] = None

    # Numéricas desde texto (e.g. "2 dormitorios" -> 2)
    num_cols = ["Dormitorios","Baños","Ambientes","Cocheras","Toilettes","Sup. cubierta","Antiguedad"]
    for c in num_cols:
        df[c] = df[c].astype(str).str.extract(r"(\d+)").astype(float)

    # Barrio: extraer el barrio si viene con "en Barrio X"
    df["Barrio"] = df["Barrio"].astype(str).str.split("en").str[-1].str.strip().replace("None", np.nan)

    # Expensas
    df["expensas"] = df["expensas"].astype(str).str.extract(r"(\d+)").astype(float) * 1000
    df["expensas"] = df["expensas"].fillna(0)

    # Precio y moneda
    df["precio"] = df["precio"].astype(str).str.replace(".", "", regex=False)
    df["Moneda"] = df["precio"].str.extract(r"^\s*(\D+)\s*\d")
    df["precio"] = df["precio"].str.extract(r"(\d+)").astype(float)
    df["Moneda"] = df["Moneda"].astype(str).str.strip()
    df.loc[df["Moneda"].str.contains("USD", case=False, na=False), "precio"] *= cotizacion_usd

    # Cambiar año 2025
    df["Antiguedad"] = pd.to_numeric(df["Antiguedad"], errors="coerce")
    df.loc[df["Antiguedad"].isin([2025, 2025.0]), "Antiguedad"] = 1.0


    # Totales
    df["Total"] = (df["precio"].fillna(0) + df["expensas"].fillna(0)).round(0)

    def _strip_accents(s: str) -> str:
        return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))

    # Canonical (con acentos correctos)
    MAIN_BARRIOS_CANONICAL = {
        "agronomia":"Agronomía","almagro":"Almagro","balvanera":"Balvanera","barracas":"Barracas",
        "belgrano":"Belgrano","boedo":"Boedo","caballito":"Caballito","chacarita":"Chacarita",
        "coghlan":"Coghlan","colegiales":"Colegiales","constitucion":"Constitución","flores":"Flores",
        "floresta":"Floresta","la boca":"La Boca","liniers":"Liniers","mataderos":"Mataderos",
        "monserrat":"Monserrat","montserrat":"Monserrat","monte castro":"Monte Castro",
        "nunez":"Núñez","nuñez":"Núñez","palermo":"Palermo","parque avellaneda":"Parque Avellaneda",
        "parque chacabuco":"Parque Chacabuco","parque chas":"Parque Chas","parque patricios":"Parque Patricios",
        "paternal":"La Paternal","pompeya":"Nueva Pompeya","puerto madero":"Puerto Madero",
        "recoleta":"Recoleta","retiro":"Retiro","saavedra":"Saavedra","san cristobal":"San Cristóbal",
        "san nicolas":"San Nicolás","san telmo":"San Telmo","velez sarsfield":"Vélez Sarsfield",
        "versalles":"Versalles","villa crespo":"Villa Crespo","villa devoto":"Villa Devoto",
        "villa general mitre":"Villa General Mitre","villa luro":"Villa Luro","villa ortuzar":"Villa Ortúzar",
        "villa ortúzar":"Villa Ortúzar","villa pueyrredon":"Villa Pueyrredón","villa pueyrredón":"Villa Pueyrredón",
        "villa real":"Villa Real","villa riachuelo":"Villa Riachuelo","villa santa rita":"Villa Santa Rita",
        "villa soldati":"Villa Soldati","villa urquiza":"Villa Urquiza"
    }

    # Subzonas → barrio principal (normalizado sin acentos y en minúsculas)
    SUBAREA_TO_BARRIO = {
        # Belgrano
        "belgrano r":"belgrano","belgrano c":"belgrano","belgrano chico":"belgrano","barrancas de belgrano":"belgrano",
        # Palermo
        "palermo chico":"palermo","palermo soho":"palermo","palermo hollywood":"palermo","palermo nuevo":"palermo",
        "palermo botanico":"palermo","palermo botánico":"palermo","palermo viejo":"palermo",
        # Caballito
        "caballito norte":"caballito","caballito sur":"caballito","parque rivadavia":"caballito",
        # Núñez / San Nicolás variantes
        "nunez":"nunez","nuñez":"nunez","san nicolás":"san nicolas","san nicolas microcentro":"san nicolas",
        # Otras subzonas comunes
        "parque lezama":"san telmo","abasto":"balvanera","once":"balvanera",
        "las cañitas":"palermo","barrio parque":"palermo",
    }

    def _canonicalize(barrio_raw: str) -> str:
        """Devuelve el barrio principal canónico (con acentos) a partir de una cadena cruda."""
        if not barrio_raw or pd.isna(barrio_raw):
            return np.nan

        s = str(barrio_raw).strip()
        # Partes tipo "Subzona, Barrio" o "Barrio, Capital Federal"
        parts = [p.strip() for p in s.split(",") if p.strip()]
        # Normalizamos a ascii-lower para matchear
        parts_norm = [_strip_accents(p).lower() for p in parts]

        # Si la última parte es un barrio válido, usamos esa
        if parts_norm:
            tail = parts_norm[-1]
            if tail in MAIN_BARRIOS_CANONICAL:
                return MAIN_BARRIOS_CANONICAL[tail]
            # Si termina en "Capital Federal"/"CABA", usamos la primera parte (subzona → barrio)
            if tail in {"capital federal","caba","ciudad autonoma de buenos aires","ciudad autónoma de buenos aires"}:
                head = parts_norm[0]
                # ¿Subzona conocida?
                if head in SUBAREA_TO_BARRIO:
                    barrio_norm = SUBAREA_TO_BARRIO[head]
                    return MAIN_BARRIOS_CANONICAL.get(barrio_norm, barrio_raw)
                # Si la subzona ya es un barrio exacto
                if head in MAIN_BARRIOS_CANONICAL:
                    return MAIN_BARRIOS_CANONICAL[head]
                # Heurística: si contiene el nombre de un barrio dentro
                for key in MAIN_BARRIOS_CANONICAL:
                    if re.search(rf"\b{re.escape(key)}\b", head):
                        return MAIN_BARRIOS_CANONICAL[key]
                # Si no, devolvemos capitalizado de la primera parte
                return parts[0].title()

            # Si la última parte no es capital federal, puede ser “Subzona, Caballito”
            # intentamos mapear subzona→barrio
            if tail in SUBAREA_TO_BARRIO:
                barrio_norm = SUBAREA_TO_BARRIO[tail]
                return MAIN_BARRIOS_CANONICAL.get(barrio_norm, parts[-1].title())

        # Sin coma: puede ser "Belgrano R" o "Caballito Norte"
        only = parts_norm[0] if parts_norm else _strip_accents(s).lower()
        if only in MAIN_BARRIOS_CANONICAL:
            return MAIN_BARRIOS_CANONICAL[only]
        if only in SUBAREA_TO_BARRIO:
            barrio_norm = SUBAREA_TO_BARRIO[only]
            return MAIN_BARRIOS_CANONICAL.get(barrio_norm, s.title())

        # Heurística final: buscar un barrio dentro del texto
        for key in MAIN_BARRIOS_CANONICAL:
            if re.search(rf"\b{re.escape(key)}\b", only):
                return MAIN_BARRIOS_CANONICAL[key]

        return s.title()

    # ---- Crear columna unificada sin tocar 'Barrio' original
    df["Barrio_simplificado"] = df["Barrio"].apply(_canonicalize)

    # Quitar filas muy vacías / sin precio
    df = df[df["Total"] > 0].reset_index(drop=True)
    return df

    
