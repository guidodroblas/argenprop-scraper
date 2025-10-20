# insights_advanced.py
import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from ml_model import train_model  # reutilizamos el modelo ya entrenado
import shap
import folium
from branca.colormap import linear

def run_advanced_insights(df, out_dir="output/plots"):
    os.makedirs(out_dir, exist_ok=True)
    print("🔬 Generando análisis avanzados...")

    # 1️⃣ Precio promedio por m² según barrio
    price_m2 = df.groupby("Barrio_simplificado")["precio_m2"].mean().sort_values(ascending=False).reset_index()
    fig1 = px.bar(price_m2, x="Barrio_simplificado", y="precio_m2",
                  title="💰 Precio promedio por m² según barrio", color="precio_m2",
                  color_continuous_scale="YlOrRd")
    fig1.update_layout(xaxis_tickangle=-45, yaxis_title="Precio promedio (ARS/m²)")
    fig1.write_html(os.path.join(out_dir, "precio_m2_por_barrio.html"))

    # 2️⃣ Distribución del tamaño (m²) por barrio
    fig2 = px.box(df, x="Barrio_simplificado", y="m2",
                  title="📏 Distribución del tamaño (m²) por barrio")
    fig2.update_layout(xaxis_tickangle=-45)
    fig2.write_html(os.path.join(out_dir, "distribucion_m2_barrio.html"))
#
#   # 3️⃣ Mapa de calor (precios)
#    pivot = df.pivot_table(values="precio_m2", index="Barrio_simplificado", aggfunc="mean").sort_values("precio_m2", ascending=False)
#    fig3 = go.Figure(data=go.Heatmap(
#        z=pivot["precio_m2"].values,
#        x=pivot.index,
#        y=["Precio m²"],
#        colorscale="YlOrRd"
#    ))
#    fig3.update_layout(title="🌡️ Mapa de calor de precios por barrio", xaxis_tickangle=-45)
#    fig3.write_html(os.path.join(out_dir, "heatmap_precios.html"))

    # 4️⃣ Densidad de publicación por barrio
    dens = df["Barrio_simplificado"].value_counts().reset_index()
    dens.columns = ["Barrio", "Publicaciones"]
    fig4 = px.bar(dens, x="Barrio", y="Publicaciones", title="🏢 Densidad de publicaciones por barrio")
    fig4.update_layout(xaxis_tickangle=-45)
    fig4.write_html(os.path.join(out_dir, "densidad_publicaciones.html"))

    # 5️⃣ Precio vs antigüedad
    fig5 = px.scatter(df, x="Antiguedad", y="precio_m2", color="Barrio_simplificado",
                      title="🏗️ Precio promedio vs antigüedad del edificio",
                      trendline="ols")
    fig5.update_layout(yaxis_title="Precio por m² (ARS)")
    fig5.write_html(os.path.join(out_dir, "precio_vs_antiguedad.html"))

    # 6️⃣ Elasticidad precio–m²
    df_log = df.dropna(subset=["m2", "Total"])
    X = np.log(df_log[["m2"]])
    y = np.log(df_log["Total"])
    reg = LinearRegression().fit(X, y)
    elasticity = reg.coef_[0]
    fig6 = px.scatter(df_log, x=np.log(df_log["m2"]), y=np.log(df_log["Total"]),
                      title=f"📈 Elasticidad precio–m² (coef ≈ {elasticity:.2f})",
                      trendline="ols")
    fig6.update_layout(xaxis_title="log(m²)", yaxis_title="log(precio total)")
    fig6.write_html(os.path.join(out_dir, "elasticidad_preciom2.html"))

        # 7️⃣ Feature Importance explicada (SHAP)
    features = ["Dormitorios","Baños","Ambientes","Cocheras","Toilettes","m2","precio_m2","expensas_ratio","amb_m2"]

    df_model = df[features + ["Total"]].dropna()
    if len(df_model) < 5:
        print("⚠️ Muy pocos datos completos para calcular SHAP. Usando columnas básicas...")
        features = ["m2", "precio_m2", "expensas_ratio"]
        df_model = df[features + ["Total"]].dropna()

    if len(df_model) == 0:
        print("❌ No hay suficientes datos para calcular la importancia de variables (SHAP). Se omite esta sección.")
    else:
        X = df_model[features]
        y = df_model["Total"]
        model = LinearRegression().fit(X, y)

        try:
            explainer = shap.Explainer(model, X)
            shap_values = explainer(X)
            shap_mean = np.abs(shap_values.values).mean(axis=0)
            fig = px.bar(x=shap_mean, y=features,
                        orientation="h", title="🧠 Importancia promedio (SHAP)")
            fig.update_layout(xaxis_title="Magnitud media de impacto")
            fig.write_html(os.path.join(out_dir, "feature_importance_shap.html"))
        except Exception as e:
            print(f"⚠️ No se pudo generar gráfico SHAP: {e}")


    # 8️⃣ Segmentación de barrios (KMeans)
    seg = df.groupby("Barrio_simplificado")[["precio_m2","expensas_ratio","m2"]].mean().dropna()
    scaler = StandardScaler()
    X_seg = scaler.fit_transform(seg)
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10).fit(X_seg)
    seg["cluster"] = kmeans.labels_

    # Mapa con colores por cluster
    barrio_coords = {
        "Palermo": [-34.578, -58.425], "Recoleta": [-34.595, -58.393],
        "Belgrano": [-34.563, -58.459], "Caballito": [-34.616, -58.440],
        "Almagro": [-34.610, -58.420], "Villa Urquiza": [-34.573, -58.487],
        "Flores": [-34.635, -58.465], "Balvanera": [-34.610, -58.402],
        "Boedo": [-34.630, -58.415], "San Telmo": [-34.621, -58.373],
    }
    m = folium.Map(location=[-34.6037, -58.3816], zoom_start=11, tiles="cartodb positron")
    colors = ["#1f77b4","#2ca02c","#ff7f0e","#d62728"]
    for b, row in seg.iterrows():
        if b in barrio_coords:
            lat, lon = barrio_coords[b]
            cluster = row["cluster"]
            popup = f"<b>{b}</b><br>Cluster {cluster}<br>Precio m²: ${row['precio_m2']:,.0f}"
            folium.CircleMarker([lat, lon], radius=10, color=colors[int(cluster)],
                                fill=True, fill_opacity=0.8, popup=popup).add_to(m)
    m.save(os.path.join(out_dir, "segmentacion_barrios.html"))

    # 9️⃣ Outliers notables (según precio por m²)
    q1, q3 = df["precio_m2"].quantile([0.25, 0.75])
    iqr = q3 - q1
    upper = q3 + 1.5 * iqr
    outliers = df[df["precio_m2"] > upper][["Link","Barrio_simplificado","precio_m2","m2","Total"]].sort_values("precio_m2", ascending=False)
    outliers.head(20).to_csv(os.path.join(out_dir, "outliers_notables.csv"), index=False, encoding="utf-8-sig")

    print("✅ Insights avanzados generados correctamente.")
