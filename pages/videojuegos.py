import dash
from dash import html, dcc, register_page, Input, Output, callback
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import seaborn as sns

from src.data import load_data, apply_filters
from src.metrics import kpi_representado_pct, kpi_perfiles_unicos, pct_by_valor, kpi_style, kpi_tooltip

dash.register_page(__name__, path="/videojuegos", name="Videojuegos")

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



def get_vj_consumers(df_f):
    return df_f[
        (df_f["actividad"] == "Videojuegos") &
        (df_f["dimension"] == "Consume") &
        (df_f["valor"] == "Sí")
    ]["personaid"].unique()


def get_dim(df_f, personaids, dimension):
    return df_f[
        (df_f["actividad"] == "Videojuegos") &
        (df_f["dimension"] == dimension) &
        (df_f["personaid"].isin(personaids))
    ]


# ==========================================================
# FIGURAS
# ==========================================================


def fig_vj_dispositivo(df_f, personaids):
    sub = get_dim(df_f, personaids, "Dispositivo")
    if sub.empty:
        return go.Figure()
    g = pct_by_valor(sub)
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
        legend_title_text="Dispositivo",
        font=dict(color="rgba(15,21,56,0.9)", size=11),
    )
    return fig


def fig_vj_frecuencia(df_f, personaids):
    sub = get_dim(df_f, personaids, "Frecuencia")
    if sub.empty:
        return go.Figure()
    g = pct_by_valor(sub)
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


def fig_vj_genero(df_f, personaids):
    sub = get_dim(df_f, personaids, "Genero")
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
        textposition="inside", insidetextanchor="middle",
        customdata=g["pct"],
        hovertemplate="%{y}<br>%{customdata:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        showlegend=False,
        margin=dict(l=90, r=20, t=10, b=10),
        paper_bgcolor=BG, plot_bgcolor=BG,
        xaxis=dict(visible=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=11)),
        font=dict(color="rgba(15,21,56,0.9)", size=11),
    )
    return fig


def fig_vj_dispositivo_frec(df_f, personaids):
    disp = get_dim(df_f, personaids, "Dispositivo")[
        ["personaid", "valor", "peso"]].rename(columns={"valor": "dispositivo"})
    frec = get_dim(df_f, personaids, "Frecuencia")[
        ["personaid", "valor"]].rename(columns={"valor": "frecuencia"})
    if disp.empty or frec.empty:
        return go.Figure()
    df = disp.merge(frec, on="personaid")
    g = df.groupby(["dispositivo", "frecuencia"], as_index=False)["peso"].sum()
    g["pct"] = g["peso"] / g["peso"].sum() * 100
    orden_frec = ["Diario", "Semanal", "Mensual", "Anual"]
    orden_disp = ["Celular", "Consola",
                  "Computadora de escritorio", "Notebook", "Tablet"]
    mat = g.pivot(index="dispositivo", columns="frecuencia", values="pct")
    mat = mat.reindex(index=orden_disp, columns=orden_frec).fillna(0.0)
    dense = get_mako_scale(64)
    mako_slice = list(
        reversed(dense[int(len(dense)*0.25):int(len(dense)*0.95)]))
    fig = px.imshow(mat.values, x=orden_frec, y=orden_disp,
                    text_auto=".1f", color_continuous_scale=mako_slice,
                    aspect="auto", zmin=0, zmax=mat.values.max())
    fig.update_traces(texttemplate="%{z:.1f}", textfont=dict(size=11),
                      hovertemplate="%{y} × %{x}<br>%{z:.2f}%<extra></extra>")
    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG,
        margin=dict(l=2, r=2, t=2, b=2),
        coloraxis_showscale=False,
        font=dict(color="rgba(15,21,56,0.9)", size=11),
    )
    fig.update_xaxes(constrain="domain", automargin=True, showgrid=False)
    fig.update_yaxes(showgrid=False)
    return fig

# ==========================================================
# LAYOUT
# ==========================================================


layout = html.Div(className="content-area", children=[
    html.Div(className="kpis-row",
             style={"paddingTop": "4px", "paddingLeft": "8px",
                    "paddingRight": "8px", "paddingBottom": "0px"},
             children=[
                 html.Div([html.Div("Porcentaje representado", className="kpi-label"),
                           html.Div(id="vj-kpi-pct", className="kpi-value")],
                          className="kpi-box", id="vj-kpi-pct-box"),
                 html.Div([html.Div("Muestra de espectador", className="kpi-label"),
                           html.Div(id="vj-kpi-n", className="kpi-value")],
                          className="kpi-box", id="vj-kpi-n-box"),
                 html.Div([html.Div("Perfiles únicos", className="kpi-label"),
                           html.Div(id="vj-kpi-perfiles", className="kpi-value")],
                          className="kpi-box", id="vj-kpi-perfiles-box"),
             ]),
    html.Div(className="charts-grid", children=[
        html.Div(className="card-pro", children=[
            html.Div("Dispositivo de juego (%)", className="card-head"),
            dcc.Graph(id="vj-g-dispositivo", style={"height": "100%"})]),
        html.Div(className="card-pro", children=[
            html.Div("Frecuencia de juego (%)", className="card-head"),
            dcc.Graph(id="vj-g-frecuencia", style={"height": "100%"})]),
        html.Div(className="card-pro", children=[
            html.Div("Género de videojuego (%)", className="card-head"),
            dcc.Graph(id="vj-g-genero", style={"height": "100%"})]),
        html.Div(className="card-pro", children=[
            html.Div("Dispositivo según frecuencia de juego (%)", className="card-head"),
            dcc.Graph(id="vj-g-disp-frec", style={"height": "100%"})]),
    ]),
])

# ==========================================================
# CALLBACKS
# ==========================================================


@callback(
    Output("vj-kpi-pct",          "children"),
    Output("vj-kpi-pct",          "style"),
    Output("vj-kpi-pct",          "title"),
    Output("vj-kpi-pct-box",      "title"),
    Output("vj-kpi-n",            "children"),
    Output("vj-kpi-n",            "style"),
    Output("vj-kpi-n",            "title"),
    Output("vj-kpi-n-box",        "title"),
    Output("vj-kpi-perfiles",     "children"),
    Output("vj-kpi-perfiles",     "style"),
    Output("vj-kpi-perfiles",     "title"),
    Output("vj-kpi-perfiles-box", "title"),
    Input("f-region", "value"), Input("f-genero", "value"),
    Input("f-nse", "value"),    Input("f-edad",   "value"),
)
def update_vj_kpi(region, genero, nse, edad):
    df_f = apply_filters(df_all, region, genero, nse, edad)
    personaids = get_vj_consumers(df_f)
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
    Output("vj-g-dispositivo", "figure"),
    Output("vj-g-frecuencia",  "figure"),
    Output("vj-g-genero",      "figure"),
    Output("vj-g-disp-frec",   "figure"),
    Input("f-region", "value"), Input("f-genero", "value"),
    Input("f-nse", "value"),    Input("f-edad",   "value"),
)
def update_vj(region, genero, nse, edad):
    df_f = apply_filters(df_all, region, genero, nse, edad)
    personaids = get_vj_consumers(df_f)
    return (
        fig_vj_dispositivo(df_f, personaids),
        fig_vj_frecuencia(df_f, personaids),
        fig_vj_genero(df_f, personaids),
        fig_vj_dispositivo_frec(df_f, personaids),
    )
