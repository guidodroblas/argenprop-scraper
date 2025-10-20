import os, numpy as np, pandas as pd
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import folium
from branca.colormap import linear
import unicodedata, re


def _remove_outliers(df):
    use = df.copy()
    feats = ["Dormitorios","Baños","Ambientes","Cocheras","Toilettes","m2","precio_m2","expensas_ratio","amb_m2"]
    X = use[feats].fillna(0)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    iso = IsolationForest(contamination=0.08, random_state=42)
    y = iso.fit_predict(Xs)
    clean = use[y == 1].copy()
    return clean


def plot_interactive(df, out_dir="output/plots"):
    os.makedirs(out_dir, exist_ok=True)
    clean = _remove_outliers(df)

    # 🔹 Aseguramos que la columna de barrios simplificados exista
    if "Barrio_simplificado" not in clean.columns:
        clean["Barrio_simplificado"] = clean["Barrio"].fillna("Sin barrio").str.strip().str.title()

    # 🔹 Normalizamos valores nulos y eliminamos sin barrio
    clean["Barrio_simplificado"] = clean["Barrio_simplificado"].replace("", np.nan)
    clean = clean.dropna(subset=["Barrio_simplificado"])

    # Histograma interactivo Total
    fig1 = px.histogram(clean, x="Total", title="Distribución de precio total (CABA, sin outliers)")
    fig1.update_layout(
        yaxis_title="Cantidad",
        xaxis_title="ARS",
        dragmode="zoom",
        xaxis=dict(tickformat=".0f")
    )
    fig1.write_html(os.path.join(out_dir, "hist_total_interactivo.html"))

    # Boxplot por barrio simplificado
    fig2 = px.box(clean, x="Barrio_simplificado", y="Total", title="Precio total por barrio (sin outliers)")
    fig2.update_layout(
        xaxis_title="Barrio",
        yaxis_title="ARS",
        xaxis_tickangle=-45,
        yaxis=dict(tickformat=".0f")
    )
    fig2.write_html(os.path.join(out_dir, "box_barrio_interactivo.html"))

    # Scatter m2 vs Total
    hover_cols = [c for c in ["Link","m2","precio_m2","Estado","expensas_ratio","Barrio"] if c in clean.columns]
    fig3 = px.scatter(
        clean, x="m2", y="Total", color="Barrio_simplificado",
        hover_data=hover_cols,
        title="m² vs Total (hover: link y detalles)"
    )
    fig3.update_layout(yaxis=dict(tickformat=".0f"))
    fig3.write_html(os.path.join(out_dir, "scatter_m2_total.html"))

    # 🗺️ Mapa Folium por barrio (con color según precio promedio)
    print("🗺️ Generando mapa por barrio (color por precio promedio)...")

    barrio_coords = {
        # Norte
        "Palermo": [-34.578, -58.425],
        "Palermo Chico": [-34.583, -58.400],
        "Palermo Hollywood": [-34.584, -58.438],
        "Palermo Soho": [-34.588, -58.428],
        "Las Cañitas": [-34.573, -58.433],
        "Recoleta": [-34.595, -58.393],
        "Barrio Norte": [-34.593, -58.404],
        "Belgrano": [-34.563, -58.459],
        "Belgrano R": [-34.565, -58.468],
        "Colegiales": [-34.576, -58.446],
        "Nuñez": [-34.544, -58.468],
        "Saavedra": [-34.548, -58.489],
        "Villa Urquiza": [-34.573, -58.487],
        "Villa Devoto": [-34.601, -58.515],
        "Villa del Parque": [-34.607, -58.486],
        "Villa Pueyrredón": [-34.584, -58.507],
        "Coghlan": [-34.567, -58.475],
        "Agronomía": [-34.593, -58.487],
        "Parque Chas": [-34.588, -58.476],
        "Villa Ortúzar": [-34.588, -58.468],
        "Villa Crespo": [-34.604, -58.435],
        "Chacarita": [-34.592, -58.454],
        "La Paternal": [-34.598, -58.469],
        "Versalles": [-34.634, -58.512],

        # Centro
        "Caballito": [-34.616, -58.440],
        "Caballito Norte": [-34.610, -58.436],
        "Almagro": [-34.610, -58.420],
        "Balvanera": [-34.610, -58.402],
        "San Cristóbal": [-34.620, -58.405],
        "Boedo": [-34.630, -58.415],
        "Parque Centenario": [-34.605, -58.433],
        "Parque Patricios": [-34.634, -58.400],
        "San Nicolás": [-34.604, -58.379],
        "Monserrat": [-34.613, -58.380],
        "Congreso": [-34.610, -58.390],
        "Constitución": [-34.619, -58.379],
        "San Telmo": [-34.621, -58.373],
        "Retiro": [-34.595, -58.373],
        "Puerto Madero": [-34.608, -58.362],
        "Barracas": [-34.647, -58.379],

        # Sur
        "Parque Avellaneda": [-34.667, -58.474],
        "Parque Chacabuco": [-34.634, -58.440],
        "Parque Lezama": [-34.624, -58.377],
        "Parque Rivadavia": [-34.613, -58.435],
        "Parque Las Heras": [-34.587, -58.406],
        "Flores": [-34.635, -58.465],
        "Floresta": [-34.635, -58.485],
        "Vélez Sarsfield": [-34.634, -58.488],
        "Villa General Mitre": [-34.610, -58.468],
        "Villa Luro": [-34.635, -58.500],
        "Mataderos": [-34.652, -58.505],
        "Liniers": [-34.642, -58.522],
        "Nueva Pompeya": [-34.652, -58.411],
        "Villa Soldati": [-34.667, -58.453],
        "Villa Lugano": [-34.675, -58.478],
        "Villa Riachuelo": [-34.685, -58.470],
        "La Boca": [-34.634, -58.363],
}

    def normalizar_barrio(b):
        if not isinstance(b, str):
            return None
        b = ''.join(c for c in unicodedata.normalize('NFKD', b) if not unicodedata.combining(c))
        b = re.sub(r'\s+', ' ', b.strip().title())
        return b

    df["Barrio_simplificado"] = df["Barrio_simplificado"].apply(normalizar_barrio)
    resumen = (
        clean.groupby("Barrio_simplificado")
        .agg({"Total": "mean", "precio_m2": "mean", "m2": "mean", "Link": "first"})
        .reset_index()
    )

    resumen = resumen.dropna(subset=["Barrio_simplificado", "Total"])
    min_val, max_val = resumen["Total"].min(), resumen["Total"].max()

    # Escala de color continua
    colormap = linear.YlOrRd_09.scale(min_val, max_val)
    colormap.caption = "Promedio de alquiler (ARS)"

    m = folium.Map(location=[-34.6037, -58.3816], zoom_start=11, tiles="cartodb positron")

    for _, r in resumen.iterrows():
        barrio = r["Barrio_simplificado"]
        if not barrio or barrio not in barrio_coords:
            continue

        lat, lon = barrio_coords[barrio]
        total = r["Total"]
        pm2 = r["precio_m2"]
        color = colormap(total)

        pm2_text = "-" if pd.isna(pm2) else f"{pm2:,.0f}"
        popup = (
            f"<b>{barrio}</b><br>"
            f"💰 Promedio total: ${total:,.0f}<br>"
            f"📏 Promedio m²: {pm2_text}<br>"
            f"<a href='{r['Link']}' target='_blank'>Ver aviso</a>"
        )


        folium.CircleMarker(
            [lat, lon],
            radius=10,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=popup,
            tooltip=f"{barrio} - ${total:,.0f}",
        ).add_to(m)

    colormap.add_to(m)
    m.save(os.path.join(out_dir, "mapa_caba.html"))

    print("✅ Mapa por barrio guardado en /output/plots/mapa_caba.html")
    print("✅ Interactivos generados en /output/plots")

    return clean
