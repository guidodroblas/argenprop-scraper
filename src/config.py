# config.py
BARRIOS_CABA = [
    "agronomia","almagro","balvanera","barracas","belgrano","boedo","caballito",
    "chacarita","coghlan","colegiales","constitucion","flores","floresta","la-boca",
    "linieres","mataderos","monserrat","monte-castro","nunez","palermo","parque-avellaneda",
    "parque-chacabuco","parque-chas","parque-patricios","paternal","pompeya",
    "puerto-madero","recoleta","retiro","saavedra","san-cristobal","san-nicolas",
    "san-telmo","velez-sarsfield","versalles","villa-crespo","villa-devoto",
    "villa-general-mitre","villa-luro","villa-ortuzar","villa-pueyrredon","villa-real",
    "villa-riachuelo","villa-santa-rita","villa-soldati","villa-urquiza"
]

# URL por barrio (alquiler - departamentos)
def url_barrio(barrio_slug: str) -> str:
    return f"https://www.argenprop.com/departamento-alquiler-barrio-{barrio_slug}"

# Parámetros de scraping
MAX_PROPS_TOTAL = 1500        # límite total de propiedades para CABA
MAX_PROPS_POR_BARRIO = 80      # por barrio, para balancear
N_DRIVERS = 4                   # paralelismo (pool de drivers)
HEADLESS = True
