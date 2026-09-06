import seaborn as sns
import dash
from dash import html, dcc, register_page, Input, Output, callback
from src.data import load_data, apply_filters
from src.metrics import kpi_representado_pct, kpi_perfiles_unicos, pct_by_valor, kpi_style, kpi_tooltip
import pandas as pd
import numpy as np
import plotly.graph_objects as go

dash.register_page(__name__, path="/tv", name="TV")

df_all = load_data()


def get_mako_scale(n=9):
    colors = sns.color_palette("mako", n)
    return [f"rgb({int(r*255)},{int(g*255)},{int(b*255)})" for r, g, b in colors]


MAKO = get_mako_scale(9)
BG = "rgba(0,0,0,0)"


def mako_skip(n, start=18, skip=11):
    dense = get_mako_scale(64)
    return [dense[min(start + i * skip, len(dense) - 1)] for i in range(n)]


def base_layout():
    return dict(
        paper_bgcolor=BG, plot_bgcolor=BG,
        autosize=True,
        margin=dict(l=10, r=10, t=10, b=10),
        font=dict(color="rgba(15,21,56,0.9)", size=11),
    )



def get_tv_consumers(df_f):
    return df_f[
        (df_f["actividad"] == "Televisión") &
        (df_f["dimension"] == "Consume") &
        (df_f["valor"] == "Sí")
    ]["personaid"].unique()


def get_dim(df_f, personaids, dimension):
    return df_f[
        (df_f["actividad"] == "Televisión") &
        (df_f["dimension"] == dimension) &
        (df_f["personaid"].isin(personaids))
    ]

# FIGURAS
def fig_tv_dispositivos(df_f, personaids):
    sub = get_dim(df_f, personaids, "Dispositivo")
    if sub.empty:
        return go.Figure()
    g = pct_by_valor(sub)
    fig = go.Figure(go.Pie(
        labels=g["valor"], values=g["pct"], hole=0.55,
        marker=dict(colors=mako_skip(len(g))), sort=False, direction="clockwise",
        textinfo="none", texttemplate="%{value:.1f}", textfont=dict(size=13),
        hovertemplate="%{label}<br>%{value:.2f}%<extra></extra>",
    ))
    fig.update_layout(**base_layout(), legend_title_text="Dispositivo")
    return fig


def fig_tv_modalidad(df_f, personaids):
    sub = get_dim(df_f, personaids, "Modalidad")
    if sub.empty:
        return go.Figure()
    g = pct_by_valor(sub)
    fig = go.Figure(go.Pie(
        labels=g["valor"], values=g["pct"], hole=0.55,
        marker=dict(colors=mako_skip(len(g))), sort=False, direction="clockwise",
        textinfo="none", texttemplate="%{value:.1f}", textfont=dict(size=13),
        hovertemplate="%{label}<br>%{value:.2f}%<extra></extra>",
    ))
    fig.update_layout(**base_layout(), legend_title_text="Modalidad")
    return fig


def fig_tv_tipo_programa(df_f, personaids):
    sub = get_dim(df_f, personaids, "Tipo_programa")
    if sub.empty:
        return go.Figure()
    g = pct_by_valor(sub).sort_values("pct", ascending=False).reset_index(drop=True)
    n = len(g)
    dense = get_mako_scale(64)
    colors = [dense[20 + i * 3] for i in range(n)]
    fig = go.Figure(go.Bar(
        x=g["valor"], y=g["pct"],
        marker=dict(color=colors),
        customdata=g["valor"],
        hovertemplate="<b>%{customdata}</b><br>%{y:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        margin=dict(l=10, r=10, t=20, b=80),
        showlegend=False,
        xaxis=dict(tickangle=-30, showgrid=False),
        yaxis=dict(
            title="Porcentaje",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)",
            zeroline=False,
            ticksuffix="%",
            tickformat=".0f",
            range=[0, g["pct"].max() * 1.15],
        ),
    )
    return fig


def fig_tv_plataformas(df_f, personaids):
    sub = get_dim(df_f, personaids, "Plataforma")
    if sub.empty:
        return go.Figure()

    sub = sub.drop_duplicates(["personaid", "valor"])

    g = sub.groupby("valor", as_index=False)["peso"].sum()
    total = sub.groupby("personaid")["peso"].max().sum()
    g["pct"] = (g["peso"] / total * 100) if total > 0 else 0.0
    g = g.sort_values("pct", ascending=True).reset_index(drop=True)

    max_val = float(g["pct"].max())
    g["left"] = (max_val - g["pct"]) / 2

    dense = get_mako_scale(64)
    start = 18
    max_skip = max(1, (len(dense) - 1 - start) // max(len(g) - 1, 1))
    skip = min(4, max_skip)
    colors = [dense[min(start + i * skip, len(dense) - 1)] for i in range(len(g))][::-1]

    fig = go.Figure(go.Bar(
        y=g["valor"],
        x=g["pct"],
        base=g["left"],
        orientation="h",
        marker=dict(color=colors),
        text=[f"{v:.1f}" if v >= 3 else "" for v in g["pct"]],
        textposition="inside",
        insidetextanchor="middle",
        cliponaxis=False,
        width=0.75,
        hovertemplate="%{customdata:.2f}%<extra></extra>",
        customdata=g["pct"],
    ))

    fig.update_layout(
        showlegend=False,
        margin=dict(l=50, r=10, t=10, b=10),
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        xaxis=dict(visible=False, range=[0, max_val + (max_val * 0.15)]),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=11)),
    )
    return fig

# LAYOUT
layout = html.Div(className="content-area", children=[
    html.Div(className="kpis-row",
             style={"paddingTop": "4px", "paddingLeft": "8px",
                    "paddingRight": "8px", "paddingBottom": "0px"},
             children=[
                 html.Div([html.Div("Porcentaje representado", className="kpi-label"),
                           html.Div(id="tv-kpi-pct", className="kpi-value")],
                          className="kpi-box", id="tv-kpi-pct-box"),
                 html.Div([html.Div("Muestra de espectador", className="kpi-label"),
                           html.Div(id="tv-kpi-n", className="kpi-value")],
                          className="kpi-box", id="tv-kpi-n-box"),
                 html.Div([html.Div("Perfiles únicos", className="kpi-label"),
                           html.Div(id="tv-kpi-perfiles", className="kpi-value")],
                          className="kpi-box", id="tv-kpi-perfiles-box"),
             ]),
    html.Div(className="charts-grid", children=[
        html.Div(className="card-pro", children=[
            html.Div("Dispositivo de consumo (%)", className="card-head"),
            dcc.Graph(id="tv-g-dispositivos", style={"height": "100%"})]),
        html.Div(className="card-pro", children=[
            html.Div("Tipo de consumo televisivo (%)", className="card-head"),
            dcc.Graph(id="tv-g-modalidad", style={"height": "100%"})]),
        html.Div(className="card-pro", children=[
            html.Div("Tipo de programa (%)", className="card-head"),
            dcc.Graph(id="tv-g-tipo-programa", style={"height": "100%"})]),
        html.Div(className="card-pro", children=[
            html.Div("Plataformas de streaming (%)", className="card-head"),
            dcc.Graph(id="tv-g-plataformas", style={"height": "100%"})]),
    ]),
])

# CALLBACKS
@callback(
    Output("tv-kpi-pct",          "children"),
    Output("tv-kpi-pct",          "style"),
    Output("tv-kpi-pct",          "title"),
    Output("tv-kpi-pct-box",      "title"),
    Output("tv-kpi-n",            "children"),
    Output("tv-kpi-n",            "style"),
    Output("tv-kpi-n",            "title"),
    Output("tv-kpi-n-box",        "title"),
    Output("tv-kpi-perfiles",     "children"),
    Output("tv-kpi-perfiles",     "style"),
    Output("tv-kpi-perfiles",     "title"),
    Output("tv-kpi-perfiles-box", "title"),
    Input("f-region", "value"), Input("f-genero", "value"),
    Input("f-nse", "value"),    Input("f-edad",   "value"),
)
def update_tv_kpis(region, genero, nse, edad):
    df_f = apply_filters(df_all, region, genero, nse, edad)
    personaids = get_tv_consumers(df_f)
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
    Output("tv-g-dispositivos",  "figure"),
    Output("tv-g-modalidad",     "figure"),
    Output("tv-g-tipo-programa", "figure"),
    Output("tv-g-plataformas",   "figure"),
    Input("f-region", "value"), Input("f-genero", "value"),
    Input("f-nse", "value"),    Input("f-edad",   "value"),
)
def update_tv(region, genero, nse, edad):
    df_f = apply_filters(df_all, region, genero, nse, edad)
    personaids = get_tv_consumers(df_f)
    return (
        fig_tv_dispositivos(df_f, personaids),
        fig_tv_modalidad(df_f, personaids),
        fig_tv_tipo_programa(df_f, personaids),
        fig_tv_plataformas(df_f, personaids),
    )