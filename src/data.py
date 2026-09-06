import os
import pandas as pd

DATA_PATH = os.getenv("DATA_PATH", "data/encc_looker_base.csv")


def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)

    df["peso"] = pd.to_numeric(df["peso"], errors="coerce").fillna(0.0)
    df["actividad"] = df["actividad"].astype(str)

    df["flag_consumo"] = (
        (df["dimension"] == "Consume") & (df["valor"] == "Sí")
    ).astype(int)

    for col in ["region", "genero", "nse_3", "grupos_edad"]:
        if col in df.columns:
            df[col] = df[col].fillna("Sin dato").astype(str)

    return df


def apply_filters(df: pd.DataFrame, region, genero, nse, edad) -> pd.DataFrame:
    dff = df

    if isinstance(region, list) and len(region) > 0:
        dff = dff[dff["region"].isin(region)]

    if isinstance(genero, list) and len(genero) > 0:
        dff = dff[dff["genero"].isin(genero)]

    if isinstance(nse, list) and len(nse) > 0:
        dff = dff[dff["nse_3"].isin(nse)]

    if isinstance(edad, list) and len(edad) > 0:
        dff = dff[dff["grupos_edad"].isin(edad)]

    return dff


def dropdown_options(df: pd.DataFrame, col: str):
    vals = sorted(df[col].dropna().unique().tolist())
    return [{"label": v, "value": v} for v in vals]
