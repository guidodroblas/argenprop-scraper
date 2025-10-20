# features.py
import pandas as pd
import numpy as np

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # m²: si no hay Sup. cubierta, dejamos NaN
    out["m2"] = out["Sup. cubierta"].replace(0, np.nan)

    # Precio por m² (si se puede)
    out["precio_m2"] = (out["Total"] / out["m2"]).replace([np.inf, -np.inf], np.nan)

    # Ratio expensas/total
    out["expensas_ratio"] = np.where(out["Total"]>0, out["expensas"]/out["Total"], np.nan)

    # Ambientes por m² (densidad)
    out["amb_m2"] = np.where(out["m2"]>0, out["Ambientes"]/out["m2"], np.nan)

    # Antigüedad binned
    bins = [-1, 0, 5, 10, 20, 40, 80, 200]
    labels = ["0","1-5","6-10","11-20","21-40","41-80","+80"]
    out["Antig_binned"] = pd.cut(out["Antiguedad"].fillna(-1), bins=bins, labels=labels)

    # Log-precio (para análisis/ML)
    out["log_total"] = np.log1p(out["Total"])
    return out
