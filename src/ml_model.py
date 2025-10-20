# ml_model.py
import os, numpy as np, pandas as pd, plotly.express as px
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import plotly.express as px
import pandas as pd
import numpy as np
import os

def train_model(df, out_dir="output/plots"):
    os.makedirs(out_dir, exist_ok=True)

    # Variables del modelo
    feats = [
        "Dormitorios", "Baños", "Ambientes", "Cocheras", "Toilettes",
        "m2", "precio_m2", "expensas_ratio", "amb_m2", "Antig_binned", "Barrio"
    ]
    d = df[feats + ["Total"]].copy()
    d = pd.get_dummies(d, columns=["Antig_binned", "Barrio"], dummy_na=True)

    X = d.drop("Total", axis=1).fillna(0)
    y = d["Total"]

    # Entrenamiento
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=250, random_state=42, n_jobs=-1)
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)

    # Métricas
    mae = mean_absolute_error(yte, pred)
    rmse = mean_squared_error(yte, pred) ** 0.5  # ✅ compatible con todas las versiones
    print(f"🤖 RF — MAE: {mae:,.0f} | RMSE: {rmse:,.0f}")


    # 📈 Gráfico interactivo real vs predicho
    resultados = pd.DataFrame({"Real": yte, "Predicho": pred})
    fig_pred = px.scatter(
        resultados, x="Real", y="Predicho",
        title="Predicción vs Valor Real (Random Forest)",
        trendline="ols",
        opacity=0.7
    )
    fig_pred.update_layout(
        xaxis_title="Valor Real (ARS)",
        yaxis_title="Predicho (ARS)",
        xaxis=dict(tickformat=".0f"),
        yaxis=dict(tickformat=".0f")
    )
    fig_pred.write_html(os.path.join(out_dir, "pred_vs_real.html"))

    print("📈 Gráficos generados: importancia_variables.html y pred_vs_real.html")
