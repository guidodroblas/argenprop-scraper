# 🏙️ Argenprop Scraper – Análisis de alquileres en CABA

Scraper y analizador de precios de alquiler en la Ciudad de Buenos Aires, construido con **Python, Selenium, Pandas y Plotly**.

## 🚀 Funcionalidades
- Scrapea automáticamente avisos de Argenprop.
- Limpieza, normalización y enriquecimiento de datos.
- Detección de outliers e insights interactivos.
- Modelos de Machine Learning para predicción de precios.
- Visualizaciones interactivas (Plotly + Folium).

## 📊 Ejemplo de outputs
- `precio_m2_por_barrio.html`  
- `elasticidad_preciom2.html`  
- `mapa_caba.html`

## 🧩 Estructura
src/
├── scraper.py # Selenium + BeautifulSoup

├── cleaning.py # Limpieza y normalización

├── features.py # Feature engineering


├── analysis_interactive.py # Visualizaciones interactivas

├── insights_advanced.py # Insights y modelos

├── ml_model.py # Entrenamiento ML

└── main.py # Pipeline principal

## 🧠 Uso
```bash
python src/main.py
Te preguntará si querés scrapear de nuevo o usar el CSV existente.

💡 Autor

Guido Droblas
Instagram – Comidas con Guido

📍 Buenos Aires, Argentina
