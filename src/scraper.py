# scraper.py
import time, itertools, math
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from config import url_barrio, BARRIOS_CABA, MAX_PROPS_TOTAL, MAX_PROPS_POR_BARRIO, N_DRIVERS, HEADLESS

BASE_ITEM_URL = "https://www.argenprop.com"

def _init_driver():
    opts = Options()
    if HEADLESS: opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=opts)

def _get_ids_de_pagina(driver, url):
    driver.get(url)
    time.sleep(1.5)
    soup = bs(driver.page_source, "html.parser")
    holder = soup.find(id="ga-dimension-list")
    if not holder: return []
    return holder.get("data-ids-avisos-mostrados","").split(",")

def _get_paginas(driver):
    soup = bs(driver.page_source, "html.parser")
    pag = soup.find("ul", class_="pagination pagination--links")
    if not pag: return 1
    lis = pag.find_all("li")
    try: return int(lis[-2].text)
    except: return 1

def _scrape_ids_barrio(barrio):
    driver = _init_driver()
    ids = []
    try:
        url1 = url_barrio(barrio)
        driver.get(url1)
        time.sleep(1.5)
        total_pages = _get_paginas(driver)
        for p in range(1, total_pages+1):
            if len(ids) >= MAX_PROPS_POR_BARRIO: break
            urlp = url1 if p==1 else f"{url1}-pagina-{p}"
            ids += _get_ids_de_pagina(driver, urlp)
    finally:
        driver.quit()
    # Limitar y limpiar
    ids = [i for i in ids if i]
    return ids[:MAX_PROPS_POR_BARRIO]

def _scrape_detalle(pid):
    driver = _init_driver()
    try:
        # Tip: muchas fichas comparten la misma raíz /{filtros}--{id}
        # Usamos una ruta neutra de deptos en CABA para abrir por id:
        url = f"{BASE_ITEM_URL}/departamento-alquiler--{pid}"
        driver.get(url)
        time.sleep(1.2)
        soup = bs(driver.page_source, "html.parser")
        main = soup.find(class_="property-main")
        if not main:
            return None
        feats = main.find(class_="property-main-features")
        precio = main.find("p", class_="titlebar__price")
        expensa = main.find("p", class_="titlebar__expenses")
        barrio = main.find("h2", class_="titlebar__title")

        data = {
            "Link": driver.current_url,
            "precio": precio.text if precio else None,
            "expensas": expensa.text if expensa else None,
            "Barrio": barrio.text if barrio else None,
        }
        if feats:
            for e in feats.find_all(recursive=False):
                titulo = e.get("title")
                v = e.find("p", class_="strong")
                if titulo and v: data[titulo] = v.text.strip()
        return data
    except Exception:
        return None
    finally:
        driver.quit()

def run_scraper_caba():
    # 1) IDs por barrio (paralelo)
    ids_total = []
    with ThreadPoolExecutor(max_workers=N_DRIVERS) as ex:
        futures = {ex.submit(_scrape_ids_barrio, b): b for b in BARRIOS_CABA}
        for f in as_completed(futures):
            ids_total.extend(f.result() or [])
            if len(ids_total) >= MAX_PROPS_TOTAL:
                break
    ids_total = list(dict.fromkeys(ids_total))[:MAX_PROPS_TOTAL]  # únicos y tope
    print(f"🔎 IDs recolectados CABA: {len(ids_total)}")

    # 2) Detalles por ID (paralelo)
    rows = []
    with ThreadPoolExecutor(max_workers=N_DRIVERS) as ex:
        futures = {ex.submit(_scrape_detalle, pid): pid for pid in ids_total}
        for i, f in enumerate(as_completed(futures), 1):
            r = f.result()
            if r: rows.append(r)
            if i % 50 == 0: print(f"Scrapeados {i}/{len(ids_total)} detalles...")

    df = pd.DataFrame(rows)
    print(f"🏁 Publicaciones con detalle: {len(df)}")
    return df
