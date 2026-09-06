import dash
from dash import html, dcc, register_page, Input, Output, callback
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import seaborn as sns

from src.data import load_data, apply_filters
from src.metrics import kpi_representado_pct, kpi_perfiles_unicos, pct_by_valor, kpi_style, kpi_tooltip

dash.register_page(__name__, path="/cine", name="Cine")

df_all = load_data()

BG = "rgba(0,0,0,0)"
GRID = "rgba(120,130,160,0.12)"


def get_mako_scale(n=9):
    colors = sns.color_palette("mako", n)
    return [f"rgb({int(r*255)},{int(g*255)},{int(b*255)})" for r, g, b in colors]


def mako_skip(n):
    dense = get_mako_scale(64)
    return [dense[min(18 + i * 3, len(dense) - 1)] for i in range(n)]


def mako_skip_wide(n):
    dense = get_mako_scale(64)
    return [dense[min(12 + i * 13, len(dense) - 1)] for i in range(n)]


def get_cine_consumers(df_f):
    return df_f[
        (df_f["actividad"] == "Cine") &
        (df_f["dimension"] == "Consume") &
        (df_f["valor"] == "Sí")
    ]["personaid"].unique()


def get_dim(df_f, personaids, dimension):
    return df_f[
        (df_f["actividad"] == "Cine") &
        (df_f["dimension"] == dimension) &
        (df_f["personaid"].isin(personaids))
    ]


def clasificar(x):
    try:
        x = float(x)
    except:
        return x
    if x == 0:
        return "Ninguna"
    elif 0 < x < 0.5:
        return "Menos de la mitad"
    elif x == 0.5:
        return "La mitad"
    elif 0.5 < x < 1:
        return "Más de la mitad"
    elif x == 1:
        return "Todas"
    else:
        return None


def base_fig():
    return dict(
        paper_bgcolor=BG, plot_bgcolor=BG,
        autosize=True,
        font=dict(color="rgba(15,21,56,0.9)", size=11),
    )


def fig_cine_genero(df_f, personaids):
    sub = get_dim(df_f, personaids, "Genero")
    if sub.empty:
        return go.Figure()
    g = pct_by_valor(sub)
    fig = go.Figure(go.Bar(
        x=g["valor"], y=g["pct"],
        marker=dict(color=mako_skip(len(g))),
        hovertemplate="%{x}<br>%{y:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        **base_fig(), showlegend=False,
        margin=dict(l=35, r=5, t=10, b=70),
        xaxis=dict(tickangle=-30, showgrid=False),
        yaxis=dict(title="Porcentaje", ticksuffix="%", showgrid=True, gridcolor=GRID),
    )
    return fig


def fig_cine_frecuencia(df_f, personaids):
    sub = get_dim(df_f, personaids, "Frecuencia")
    if sub.empty:
        return go.Figure()
    g = sub.groupby("valor", as_index=False)["peso"].sum()
    g["pct"] = g["peso"] / g["peso"].sum() * 100
    orden = ["Semanal", "Mensual", "Anual"]
    g["orden"] = g["valor"].map({v: i for i, v in enumerate(orden)})
    g = g.dropna(subset=["orden"]).sort_values("orden")
    fig = go.Figure(go.Pie(
        labels=g["valor"], values=g["pct"], hole=0.55,
        marker=dict(colors=mako_skip_wide(len(g))), sort=False,
        textinfo="none", texttemplate="%{value:.1f}", textfont=dict(size=11),
        hovertemplate="%{label}<br>%{value:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        **base_fig(), legend_title_text="Frecuencia",
        margin=dict(l=5, r=5, t=5, b=5),
    )
    return fig


def fig_cine_proporcion(df_f, personaids):
    sub = get_dim(df_f, personaids, "Proporcion_argentinas").copy()
    if sub.empty:
        return go.Figure()
    sub["valor"] = sub["valor"].apply(clasificar)
    g = sub.groupby("valor", as_index=False)["peso"].sum()
    g["pct"] = g["peso"] / g["peso"].sum() * 100
    orden = ["Ninguna", "Menos de la mitad", "La mitad", "Más de la mitad", "Todas"]
    g["orden"] = g["valor"].map({v: i for i, v in enumerate(orden)})
    g = g.dropna(subset=["orden"]).sort_values("orden")
    if g.empty:
        return go.Figure()
    # Paleta: arranca en clarito (índice 28) y va oscureciendo hacia el 58
    dense = get_mako_scale(64)
    n = len(g)
    colors = [dense[min(28 + i * 6, len(dense) - 1)] for i in range(n)]
    fig = go.Figure(go.Bar(
        x=g["valor"], y=g["pct"],
        marker=dict(color=colors),
        hovertemplate="%{x}<br>%{y:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        **base_fig(), showlegend=False,
        margin=dict(l=35, r=5, t=10, b=50),
        xaxis=dict(showgrid=False),
        yaxis=dict(title="Porcentaje", ticksuffix="%", showgrid=True, gridcolor=GRID),
    )
    return fig


def fig_cine_proporcion_x_frec(df_f, personaids):
    """
    Stacked bar 100% horizontal: proporción de películas argentinas
    según frecuencia de asistencia (Mensual / Anual).
    """
    prop = get_dim(df_f, personaids, "Proporcion_argentinas").copy()
    frec = get_dim(df_f, personaids, "Frecuencia")[["personaid", "valor"]].rename(columns={"valor": "frecuencia"})

    if prop.empty or frec.empty:
        return go.Figure()

    prop["valor"] = pd.to_numeric(prop["valor"], errors="coerce")
    prop["cat"] = prop["valor"].apply(clasificar)

    merged = prop.merge(frec, on="personaid")
    merged = merged[merged["frecuencia"].isin(["Mensual", "Anual"])]

    orden_cat = ["Ninguna", "Menos de la mitad", "La mitad", "Más de la mitad", "Todas"]
    orden_frec = ["Mensual", "Anual"]

    pivot = merged.groupby(["frecuencia", "cat"])["peso"].sum().unstack().fillna(0)
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100
    pivot_pct = pivot_pct.reindex(columns=orden_cat, fill_value=0).reindex(orden_frec, fill_value=0)

    # Paleta: arranca más oscura
    dense = get_mako_scale(64)
    colors = [dense[18], dense[26], dense[36], dense[46], dense[56]]

    fig = go.Figure()
    for i, cat in enumerate(orden_cat):
        vals = pivot_pct[cat].tolist()
        fig.add_trace(go.Bar(
            name=cat,
            x=vals,
            y=orden_frec,
            orientation="h",
            marker_color=colors[i],
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(size=10, color="white"),
            hovertemplate=f"<b>%{{y}}</b><br>{cat}: %{{x:.2f}}%<extra></extra>",
        ))

    fig.update_layout(
        **base_fig(),
        barmode="stack",
        margin=dict(l=70, r=20, t=10, b=30),
        xaxis=dict(
            range=[0, 100], ticksuffix="%",
            showgrid=True, gridcolor=GRID,
            showline=True, linecolor=GRID,
            tickfont=dict(size=10, color="rgba(15,21,56,0.6)"),
            dtick=20,
        ),
        yaxis=dict(showgrid=False, ticklabelstandoff=10),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="center", x=0.5, font=dict(size=10),
            traceorder="normal",
        ),
    )
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
                           html.Div(id="cine-kpi-pct", className="kpi-value")],
                          className="kpi-box", id="cine-kpi-pct-box"),
                 html.Div([html.Div("Muestra de espectadores", className="kpi-label"),
                           html.Div(id="cine-kpi-n", className="kpi-value")],
                          className="kpi-box", id="cine-kpi-n-box"),
                 html.Div([html.Div("Perfiles únicos", className="kpi-label"),
                           html.Div(id="cine-kpi-perfiles", className="kpi-value")],
                          className="kpi-box", id="cine-kpi-perfiles-box"),
             ]),
    html.Div(className="charts-grid", children=[
        html.Div(className="card-pro", children=[
            html.Div("Género de película (%)", className="card-head"),
            dcc.Graph(id="cine-g-genero", style={"height": "100%"})]),
        html.Div(className="card-pro", children=[
            html.Div("Frecuencia de asistencia (%)", className="card-head"),
            dcc.Graph(id="cine-g-frecuencia", style={"height": "100%"})]),
        html.Div(className="card-pro", children=[
            html.Div("Proporción de películas argentinas (%)", className="card-head"),
            dcc.Graph(id="cine-g-proporcion", style={"height": "100%"})]),
        html.Div(className="card-pro", children=[
            html.Div("Películas argentinas según frecuencia de asistencia (%)", className="card-head"),
            dcc.Graph(id="cine-g-genero-frec", style={"height": "100%"})]),
    ]),
])


# ==========================================================
# CALLBACKS
# ==========================================================

@callback(
    Output("cine-kpi-pct",          "children"),
    Output("cine-kpi-pct",          "style"),
    Output("cine-kpi-pct",          "title"),
    Output("cine-kpi-pct-box",      "title"),
    Output("cine-kpi-n",            "children"),
    Output("cine-kpi-n",            "style"),
    Output("cine-kpi-n",            "title"),
    Output("cine-kpi-n-box",        "title"),
    Output("cine-kpi-perfiles",     "children"),
    Output("cine-kpi-perfiles",     "style"),
    Output("cine-kpi-perfiles",     "title"),
    Output("cine-kpi-perfiles-box", "title"),
    Input("f-region", "value"), Input("f-genero", "value"),
    Input("f-nse", "value"),    Input("f-edad",   "value"),
)
def update_cine_kpis(region, genero, nse, edad):
    df_f = apply_filters(df_all, region, genero, nse, edad)
    personaids = get_cine_consumers(df_f)
    n = len(personaids)
    df_c = df_f[df_f["personaid"].isin(personaids)]
    pct = kpi_representado_pct(df_all, df_c)
    perfiles = kpi_perfiles_unicos(df_c)
    st = kpi_style(n)
    tt = kpi_tooltip(n)
    return (
        f"{pct:.1f}%", st, tt, tt,
        f"{n:,}",      st, tt, tt,
        f"{perfiles:,}", st, tt, tt,
    )


@callback(
    Output("cine-g-genero",      "figure"),
    Output("cine-g-frecuencia",  "figure"),
    Output("cine-g-proporcion",  "figure"),
    Output("cine-g-genero-frec", "figure"),
    Input("f-region", "value"), Input("f-genero", "value"),
    Input("f-nse", "value"),    Input("f-edad",   "value"),
)
def update_cine(region, genero, nse, edad):
    df_f = apply_filters(df_all, region, genero, nse, edad)
    personaids = get_cine_consumers(df_f)
    return (
        fig_cine_genero(df_f, personaids),
        fig_cine_frecuencia(df_f, personaids),
        fig_cine_proporcion(df_f, personaids),
        fig_cine_proporcion_x_frec(df_f, personaids),
    )