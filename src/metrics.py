import pandas as pd


def kpi_representado_pct(df_all: pd.DataFrame, df_f: pd.DataFrame) -> float:
    total = df_all.groupby("personaid", as_index=False)[
        "peso"].max()["peso"].sum()
    part = df_f.groupby("personaid", as_index=False)[
        "peso"].max()["peso"].sum()
    return 0.0 if total == 0 else (part / total) * 100


def n_personas(df_f: pd.DataFrame) -> int:
    return int(df_f["personaid"].nunique())


def kpi_perfiles_unicos(df_f: pd.DataFrame) -> int:
    """
    Cantidad de perfiles sociodemográficos únicos presentes en el subconjunto filtrado.
    Perfil = combinación única de (region, genero, nse3, grupo_edad).
    No incluye actividades.
    """
    if df_f.empty:
        return 0

    cols = ["region", "genero", "nse_3", "grupos_edad"]

    # si alguna columna no existe, evitamos que explote
    missing = [c for c in cols if c not in df_f.columns]
    if missing:
        return 0

    return int(
        df_f[cols]
        .drop_duplicates()
        .shape[0]
    )


def kpi_style(n: int) -> dict:
    if n <= 25:
        return {"color": "#c0392b", "fontWeight": "900"}
    return {"color": "#1a5fa8", "fontWeight": "900"}


def kpi_tooltip(n: int) -> str:
    if n <= 25:
        return "Pocos casos, los resultados deben tomarse con cautela"
    return "La muestra es suficiente para obtener resultados confiables"


def pct_by_valor(sub: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula el porcentaje de cada valor dentro de un subset de dimensión.

    """
    if sub.empty:
        return pd.DataFrame(columns=["valor", "peso", "pct"])

    sub = sub.drop_duplicates(["personaid", "valor"])
    g = sub.groupby("valor", as_index=False)["peso"].sum()
    total = sub.groupby("personaid")["peso"].max().sum()
    g["pct"] = (g["peso"] / total * 100) if total > 0 else 0.0
    return g.sort_values("pct", ascending=False).reset_index(drop=True)