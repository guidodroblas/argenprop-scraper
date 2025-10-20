import os
import pandas as pd
from scraper import run_scraper_caba
from cleaning import clean_data
from features import add_features
from analysis_interactive import plot_interactive
from ml_model import train_model
from insights_advanced import run_advanced_insights

DATA_DIR = r"C:\Users\drobl\OneDrive\Escritorio\Guido\argenprop_scraper\output\data"
PLOTS_DIR = r"C:\Users\drobl\OneDrive\Escritorio\Guido\argenprop_scraper\output\plots"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

print("🏙️ Análisis de mercado inmobiliario CABA")
print("¿Qué querés hacer?")
print("1️⃣  Scrappear nuevamente Argenprop")
print("2️⃣  Usar el último CSV guardado\n")

choice = input("Elegí una opción (1 o 2): ").strip()

if choice == "1":
    print("🕸️ Scrapeando CABA (esto puede tardar unos minutos)...")
    df_raw = run_scraper_caba()
    print("🧹 Limpiando datos...")
    df = clean_data(df_raw)
    print("🧪 Generando features...")
    df = add_features(df)
    df.to_csv(os.path.join(DATA_DIR, "caba_base_completa.csv"), index=False, encoding="utf-8-sig")
else:
    file_path = os.path.join(DATA_DIR, "caba_base_completa.csv")
    if not os.path.exists(file_path):
        print("⚠️ No se encontró un CSV previo. Se realizará scraping.")
        df_raw = run_scraper_caba()
        df = clean_data(df_raw)
        df = add_features(df)
        df.to_csv(file_path, index=False, encoding="utf-8-sig")
    else:
        print(f"📂 Cargando datos desde {file_path} ...")
        df = pd.read_csv(file_path)

print("📊 Generando visualizaciones interactivas y eliminando outliers...")
df_clean = plot_interactive(df, out_dir=PLOTS_DIR)
df_clean.to_csv(os.path.join(DATA_DIR, "caba_limpio_sin_outliers.csv"), index=False, encoding="utf-8-sig")

print("🤖 Entrenando modelo de predicción...")
train_model(df_clean, out_dir=PLOTS_DIR)

print("🔍 Generando insights avanzados...")
run_advanced_insights(df_clean, out_dir=PLOTS_DIR)

print("\n✅ Proyecto completado. Resultados guardados en /output/data y /output/plots")

