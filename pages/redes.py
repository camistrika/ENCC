import dash
from dash import html, dcc, register_page, Input, Output, callback
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import seaborn as sns

from src.data import load_data, apply_filters
from src.metrics import kpi_representado_pct, kpi_perfiles_unicos, pct_by_valor, kpi_style, kpi_tooltip

dash.register_page(__name__, path="/redes", name="Redes")

df_all = load_data()

BG = "rgba(0,0,0,0)"
GRID = "rgba(120,130,160,0.12)"


def get_mako_scale(n=9):
    colors = sns.color_palette("mako", n)
    return [f"rgb({int(r*255)},{int(g*255)},{int(b*255)})" for r, g, b in colors]


MAKO = get_mako_scale(9)


def mako_skip_wide(n):
    dense = get_mako_scale(64)
    return [dense[min(12 + i * 13, len(dense) - 1)] for i in range(n)]


def mako_skip(n, start=18, skip=4):
    dense = get_mako_scale(64)
    max_skip = max(1, (len(dense) - 1 - start) // max(n - 1, 1))
    sk = min(skip, max_skip)
    return [dense[min(start + i * sk, len(dense) - 1)] for i in range(n)]


def get_redes_consumers(df_f):
    return df_f[
        (df_f["actividad"] == "Redes sociales") &
        (df_f["dimension"] == "Consume") &
        (df_f["valor"] == "Sí")
    ]["personaid"].unique()


def get_dim(df_f, personaids, dimension):
    return df_f[
        (df_f["actividad"] == "Redes sociales") &
        (df_f["dimension"] == dimension) &
        (df_f["personaid"].isin(personaids))
    ]


# FIGURAS
def fig_redes_plataformas(df_f, personaids):
    sub = get_dim(df_f, personaids, "Plataforma")
    if sub.empty:
        return go.Figure()
    g = pct_by_valor(sub).sort_values(
        "pct", ascending=True).reset_index(drop=True)
    n = len(g)
    max_val = float(g["pct"].max())
    g["left"] = (max_val - g["pct"]) / 2
    dense = get_mako_scale(64)
    start = 18
    max_skip = max(1, (len(dense) - 1 - start) // max(n - 1, 1))
    skip = min(4, max_skip)
    colors = [dense[min(start + i * skip, len(dense) - 1)]
              for i in range(n)][::-1]
    fig = go.Figure(go.Bar(
        y=g["valor"], x=g["pct"], base=g["left"],
        orientation="h",
        marker=dict(color=colors),
        text=[f"{v:.1f}" if v >= 3 else "" for v in g["pct"]],
        textposition="inside",
        insidetextanchor="middle",
        hovertemplate="%{customdata:.2f}%<extra></extra>",
        customdata=g["pct"],
    ))
    fig.update_layout(
        showlegend=False,
        margin=dict(l=75, r=15, t=5, b=5),
        paper_bgcolor=BG, plot_bgcolor=BG,
        xaxis=dict(visible=False, range=[0, max_val * 1.25]),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=11)),
        font=dict(color="rgba(15,21,56,0.9)", size=11),
    )
    return fig


def fig_redes_frec_consumo(df_f, personaids):
    sub = get_dim(df_f, personaids, "Frecuencia_consumo")
    if sub.empty:
        return go.Figure()
    g = pct_by_valor(sub)
    # "Nunca" excluido — usuarios de redes que nunca las consumen no es relevante
    orden = ["Diario", "Semanal", "Mensual", "Anual"]
    g["orden"] = g["valor"].map({v: i for i, v in enumerate(orden)})
    g = g.dropna(subset=["orden"]).sort_values("orden")
    fig = go.Figure(go.Pie(
        labels=g["valor"], values=g["pct"], hole=0.55,
        marker=dict(colors=mako_skip_wide(len(g))), sort=False,
        textinfo="none", texttemplate="%{value:.1f}",
        textfont=dict(size=11),
        hovertemplate="%{label}<br>%{value:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG,
        margin=dict(l=5, r=5, t=5, b=5),
        legend_title_text="Frecuencia",
        font=dict(color="rgba(15,21,56,0.9)", size=11),
    )
    return fig


def fig_redes_frec_video(df_f, personaids):
    sub = get_dim(df_f, personaids, "Frecuencia_video")
    if sub.empty:
        return go.Figure()
    g = pct_by_valor(sub)
    orden = ["Diario", "Semanal", "Mensual", "Anual", "Nunca"]
    g["orden"] = g["valor"].map({v: i for i, v in enumerate(orden)})
    g = g.dropna(subset=["orden"]).sort_values("orden")
    fig = go.Figure(go.Pie(
        labels=g["valor"], values=g["pct"], hole=0.55,
        marker=dict(colors=mako_skip_wide(len(g))), sort=False,
        textinfo="none", texttemplate="%{value:.1f}",
        textfont=dict(size=11),
        hovertemplate="%{label}<br>%{value:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG,
        margin=dict(l=5, r=5, t=5, b=5),
        legend_title_text="Frecuencia",
        font=dict(color="rgba(15,21,56,0.9)", size=11),
    )
    return fig


def fig_redes_plataformas_x_frec(df_f, personaids):
    plat = get_dim(df_f, personaids, "Plataforma")[["personaid", "valor", "peso"]]
    frec = get_dim(df_f, personaids, "Frecuencia_consumo")[
        ["personaid", "valor"]
    ].rename(columns={"valor": "frecuencia"})

    if plat.empty or frec.empty:
        return go.Figure()

    plat = plat.drop_duplicates(["personaid", "valor"])

    orden_frec = ["Diario", "Semanal", "Mensual", "Anual"]
    frec = frec[frec["frecuencia"].isin(orden_frec)].drop_duplicates(["personaid", "frecuencia"])

    if frec.empty:
        return go.Figure()

    cant = plat.groupby("personaid").agg(
        n_plat=("valor", "count"),
        peso=("peso", "max")
    ).reset_index()

    def bucket(n):
        if n == 1:
            return "1"
        if n == 2:
            return "2"
        if n <= 4:
            return "3 a 4"
        return "5 o más"

    merged = cant.merge(frec, on="personaid", how="inner")
    if merged.empty:
        return go.Figure()

    merged = merged.copy()
    merged["bucket"] = merged["n_plat"].apply(bucket)
    buckets = ["1", "2", "3 a 4", "5 o más"]
    rows = []
    for f in orden_frec:
        sub_f = merged[merged["frecuencia"] == f]
        total = sub_f.drop_duplicates("personaid")["peso"].sum()

        for b in buckets:
            sub_b = sub_f[sub_f["bucket"] == b]
            w = sub_b.drop_duplicates("personaid")["peso"].sum()
            pct = w / total * 100 if total else 0

            rows.append({
                "frecuencia": f,
                "bucket": b,
                "pct": pct
            })
    g = pd.DataFrame(rows)
    dense = get_mako_scale(64)
    colors = {
        "1": dense[14],
        "2": dense[26],
        "3 a 4": dense[40],
        "5 o más": dense[54]
    }
    fig = go.Figure()
    for b in buckets:
        sub = g[g["bucket"] == b]
        fig.add_trace(go.Bar(
            name=b,
            x=sub["frecuencia"],
            y=sub["pct"],
            marker=dict(color=colors[b]),
            customdata=np.array([[b]] * len(sub)),
            hovertemplate=(
                "Frecuencia: %{x}<br>"
                "Cantidad de plataformas: %{customdata[0]}<br>"
                "Porcentaje: %{y:.1f}%<extra></extra>"
            ),
        ))
    fig.update_layout(
        barmode="stack",
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        margin=dict(l=10, r=10, t=20, b=10),
        legend_title_text="Cantidad de plataformas",
        yaxis=dict(
            title="Porcentaje",
            ticksuffix="%",
            showgrid=True,
            gridcolor=GRID,
            zeroline=False,
            range=[0, 100]
        ),
        xaxis=dict(title=None),
    )
    return fig


# LAYOUT
layout = html.Div(className="content-area", children=[
    html.Div(className="kpis-row",
             style={"paddingTop": "4px", "paddingLeft": "8px",
                    "paddingRight": "8px", "paddingBottom": "0px"},
             children=[
                 html.Div([html.Div("Porcentaje representado", className="kpi-label"),
                           html.Div(id="redes-kpi-pct", className="kpi-value")],
                          className="kpi-box", id="redes-kpi-pct-box"),
                 html.Div([html.Div("Muestra de usuarios", className="kpi-label"),
                           html.Div(id="redes-kpi-n", className="kpi-value")],
                          className="kpi-box", id="redes-kpi-n-box"),
                 html.Div([html.Div("Perfiles únicos", className="kpi-label"),
                           html.Div(id="redes-kpi-perfiles", className="kpi-value")],
                          className="kpi-box", id="redes-kpi-perfiles-box"),
             ]),
    html.Div(className="charts-grid", children=[
        html.Div(className="card-pro", children=[
            html.Div("Plataformas utilizadas (%)", className="card-head"),
            dcc.Graph(id="redes-g-plataformas", style={"height": "100%"})]),
        html.Div(className="card-pro", children=[
            html.Div("Frecuencia de consumo (%)", className="card-head"),
            dcc.Graph(id="redes-g-frec-consumo", style={"height": "100%"})]),
        html.Div(className="card-pro", children=[
            html.Div("Frecuencia de consumo de videos (%)",
                     className="card-head"),
            dcc.Graph(id="redes-g-frec-video", style={"height": "100%"})]),
        html.Div(className="card-pro", children=[
            html.Div("Plataformas usadas por frecuencia (%)", className="card-head"),
            dcc.Graph(id="redes-g-consumo-vs-video", style={"height": "100%"})]),
    ]),
])


# CALLBACKS
@callback(
    Output("redes-kpi-pct",          "children"),
    Output("redes-kpi-pct",          "style"),
    Output("redes-kpi-pct",          "title"),
    Output("redes-kpi-pct-box",      "title"),
    Output("redes-kpi-n",            "children"),
    Output("redes-kpi-n",            "style"),
    Output("redes-kpi-n",            "title"),
    Output("redes-kpi-n-box",        "title"),
    Output("redes-kpi-perfiles",     "children"),
    Output("redes-kpi-perfiles",     "style"),
    Output("redes-kpi-perfiles",     "title"),
    Output("redes-kpi-perfiles-box", "title"),
    Input("f-region", "value"), Input("f-genero", "value"),
    Input("f-nse", "value"),    Input("f-edad",   "value"),
)
def update_redes_kpis(region, genero, nse, edad):
    df_f = apply_filters(df_all, region, genero, nse, edad)
    personaids = get_redes_consumers(df_f)
    n = len(personaids)
    df_c = df_f[df_f["personaid"].isin(personaids)]
    pct = kpi_representado_pct(df_all, df_c)
    perfiles = kpi_perfiles_unicos(df_c)
    st = kpi_style(n)
    tt = kpi_tooltip(n)
    return (
        f"{pct:.1f}%",   st, tt, tt,
        f"{n:,}",        st, tt, tt,
        f"{perfiles:,}", st, tt, tt,
    )


@callback(
    Output("redes-g-plataformas",      "figure"),
    Output("redes-g-frec-consumo",     "figure"),
    Output("redes-g-frec-video",       "figure"),
    Output("redes-g-consumo-vs-video", "figure"),
    Input("f-region", "value"), Input("f-genero", "value"),
    Input("f-nse", "value"),    Input("f-edad",   "value"),
)
def update_redes(region, genero, nse, edad):
    df_f = apply_filters(df_all, region, genero, nse, edad)
    personaids = get_redes_consumers(df_f)
    return (
        fig_redes_plataformas(df_f, personaids),
        fig_redes_frec_consumo(df_f, personaids),
        fig_redes_frec_video(df_f, personaids),
        fig_redes_plataformas_x_frec(df_f, personaids),
    )