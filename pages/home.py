from __future__ import annotations

from dash import html, dcc, register_page, Input, Output, callback
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import seaborn as sns

from src.data import load_data, apply_filters
from src.metrics import kpi_representado_pct, n_personas, kpi_perfiles_unicos, kpi_style, kpi_tooltip

pio.templates.default = "plotly"

register_page(__name__, path="/", name="Inicio")

df_all = load_data()

BG = "rgba(0,0,0,0)"
AX_LINE = "rgba(120,130,160,0.25)"
GRID = "rgba(120,130,160,0.12)"
TICK = "rgba(15,21,56,0.8)"


def get_mako_scale(n=9):
    colors = sns.color_palette("mako", n)
    return [f"rgb({int(r*255)},{int(g*255)},{int(b*255)})" for r, g, b in colors]


MAKO = get_mako_scale(9)


def apply_light_style(fig: go.Figure, *, percent_axis=None, heatmap=False) -> go.Figure:
    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG,
        autosize=True,
        font=dict(color="rgba(15,21,56,0.9)", size=11),
        margin=dict(l=30, r=30, t=30, b=30),
    )
    fig.update_xaxes(showgrid=not heatmap, gridcolor=GRID, zeroline=False,
                     linecolor=AX_LINE, tickcolor=AX_LINE, tickfont=dict(color=TICK))
    fig.update_yaxes(showgrid=not heatmap, gridcolor=GRID, zeroline=False,
                     linecolor=AX_LINE, tickcolor=AX_LINE, tickfont=dict(color=TICK))
    if percent_axis == "x":
        fig.update_xaxes(ticksuffix="%")
    elif percent_axis == "y":
        fig.update_yaxes(ticksuffix="%")
    return fig



# ==========================================================
# FIGURAS
# ==========================================================

def fig_participacion_apilada(df_f: pd.DataFrame) -> go.Figure:
    df_f = df_f[df_f["dimension"] == "Consume"]
    g = df_f.groupby(["actividad", "flag_consumo"],
                     as_index=False)["peso"].sum()
    g["total_act"] = g.groupby("actividad") ["peso"].transform("sum")
    g["pct"] = np.where(g["total_act"] == 0, 0,
                        (g["peso"] / g["total_act"]) * 100)
    g["consume"] = g["flag_consumo"].map({1: "Sí", 0: "No"})
    fig = px.bar(g, x="actividad", y="pct", color="consume", barmode="stack",
                 color_discrete_map={"Sí": MAKO[6], "No": MAKO[2]},
                 category_orders={"consume": ["Sí", "No"]},
                 labels={"actividad": "Actividad", "pct": "Porcentaje", "consume": "Consume"})
    fig.update_traces(hovertemplate="%{y}.2f}%<extra></extra>")
    fig.update_layout(xaxis_title="Actividad",
                      yaxis_title="Porcentaje", legend_title_text="Consume")
    return apply_light_style(fig, percent_axis="y")


def fig_top_consumo(df_f: pd.DataFrame) -> go.Figure:
    if df_f.empty:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor=BG, plot_bgcolor=BG,
                          margin=dict(l=10, r=10, t=5, b=5))
        return fig
    df_f = df_f[df_f["dimension"] == "Consume"]
    yes = df_f[df_f["flag_consumo"] == 1].groupby(
        "actividad", as_index=False)["peso"].sum()
    tot = df_f.groupby("actividad", as_index=False)[
        "peso"].sum().rename(columns={"peso": "peso_total"})
    g = yes.merge(tot, on="actividad", how="right").fillna(0.0)
    g["pct"] = np.where(g["peso_total"] == 0, 0,
                        (g["peso"] / g["peso_total"]) * 100)
    g = g.sort_values("pct", ascending=False).reset_index(drop=True)
    gp = g.iloc[::-1].reset_index(drop=True)
    max_val = float(gp["pct"].max()) if len(gp) else 0.0
    gp["left"] = (max_val - gp["pct"]) / 2
    n = len(gp)
    i0 = int(len(MAKO) * 0.25)
    i1 = int(len(MAKO) * 0.95)
    mako_slice = MAKO[i0:i1]
    idx = np.linspace(0, len(mako_slice) - 1, n).round().astype(int)
    colors = [mako_slice[i] for i in idx][::-1]
    fig = go.Figure(go.Bar(
        y=gp["actividad"], x=gp["pct"], base=gp["left"], orientation="h",
        marker=dict(color=colors),
        text=[f"{v:.1f}" if v >= 3 else "" for v in gp["pct"]],
        textposition="inside", insidetextanchor="middle",
        hovertemplate="%{y}<br>%{customdata:.2f}%<extra></extra>",
        customdata=gp["pct"],
    ))
    fig.update_layout(showlegend=False, margin=dict(l=90, r=20, t=10, b=10),
                      paper_bgcolor=BG, plot_bgcolor=BG,
                      xaxis=dict(visible=False),
                      yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=11)))
    return fig


def fig_hist_cantidad_actividades(df_f: pd.DataFrame) -> go.Figure:
    if df_f.empty:
        return go.Figure()
    df_f = df_f[df_f["dimension"] == "Consume"]
    piv = df_f.pivot_table(index="personaid", columns="actividad",
                           values="flag_consumo", aggfunc="max", fill_value=0)
    w = df_f.groupby("personaid")["peso"].max().reindex(piv.index).fillna(0.0)
    cant = piv.sum(axis=1).astype(int)
    dist = (pd.DataFrame({"cant": cant, "peso": w})
            .groupby("cant", as_index=False)["peso"].sum()
            .sort_values("cant").reset_index(drop=True))
    total = dist["peso"].sum()
    dist["pct"] = 0.0 if total == 0 else (dist["peso"] / total) * 100
    dist["label"] = dist["cant"].astype(int).astype(str)
    mako_dense = get_mako_scale(64)
    n = len(dist)
    donut_colors = [
        mako_dense[min(12 + i * 13, len(mako_dense) - 1)] for i in range(n)][::-1]
    fig = go.Figure(go.Pie(
        labels=dist["label"], values=dist["pct"], hole=0.6,
        marker=dict(colors=donut_colors), sort=False, direction="clockwise",
        textinfo="none", texttemplate="%{value:.1f}",
        hovertemplate="%{label}<br>%{value:.2f}%<extra></extra>",
    ))
    fig.update_layout(legend_title_text="Cantidad", legend=dict(x=0.92, y=0.5),
                      margin=dict(l=0, r=0, t=0, b=0))
    return apply_light_style(fig)


def fig_heatmap_coconsumo_joint(df_f: pd.DataFrame) -> go.Figure:
    if df_f.empty:
        return go.Figure()
    df_f = df_f[df_f["dimension"] == "Consume"]
    piv = df_f.pivot_table(index="personaid", columns="actividad",
                           values="flag_consumo", aggfunc="max", fill_value=0)
    w = df_f.groupby("personaid")["peso"].max().reindex(piv.index).fillna(0.0)
    total_w = w.sum()
    acts = list(piv.columns)
    mat = np.zeros((len(acts), len(acts)))
    for i, a in enumerate(acts):
        for j, b in enumerate(acts):
            both = (piv[a] == 1) & (piv[b] == 1)
            mat[i, j] = 0.0 if total_w == 0 else (
                w[both].sum() / total_w) * 100
    i0 = int(len(MAKO) * 0.25)
    i1 = int(len(MAKO) * 0.95)
    mako_slice = list(reversed(MAKO[i0:i1]))
    fig = px.imshow(mat, x=acts, y=acts, text_auto=".1f",
                    color_continuous_scale=mako_slice, aspect="auto", zmin=0, zmax=100)
    fig.update_traces(texttemplate="%{z:.1f}", textfont=dict(size=12),
                      hovertemplate="%{y} × %{x}<br>%{z:.2f}%<extra></extra>")
    fig.update_layout(margin=dict(l=2, r=2, t=2, b=2),
                      coloraxis_showscale=False)
    fig.update_xaxes(constrain="domain", automargin=True)
    return apply_light_style(fig, heatmap=True)


# =========================================================
# LAYOUT
# =========================================================

layout = html.Div(
    className="content-area",
    children=[

        # KPIs globales
        html.Div(
            className="kpis-row",
            style={"paddingTop": "4px", "paddingLeft": "8px",
                   "paddingRight": "8px", "paddingBottom": "0px"},
            children=[
                html.Div([
                    html.Div("Porcentaje representado", className="kpi-label"),
                    html.Div(id="kpi-representado", className="kpi-value"),
                ], className="kpi-box", id="kpi-representado-box"),
                html.Div([
                    html.Div("Muestra", className="kpi-label"),
                    html.Div(id="kpi-personas", className="kpi-value"),
                ], className="kpi-box", id="kpi-personas-box"),
                html.Div([
                    html.Div("Perfiles únicos", className="kpi-label"),
                    html.Div(id="kpi-perfiles", className="kpi-value"),
                ], className="kpi-box", id="kpi-perfiles-box"),
            ],
        ),

        html.Div(
            className="charts-grid",
            children=[
                html.Div(className="card-pro", children=[
                    html.Div("Consumo por actividad (%)",
                             className="card-head"),
                    dcc.Graph(id="g-participacion", style={"height": "100%"}),
                ]),
                html.Div(className="card-pro", children=[
                    html.Div("Ranking de consumo (%)", className="card-head"),
                    dcc.Graph(id="g-ranking", style={"height": "100%"}),
                ]),
                html.Div(className="card-pro", children=[
                    html.Div("Actividades por persona (%)",
                             className="card-head"),
                    dcc.Graph(id="g-anillo", style={"height": "100%"}),
                ]),
                html.Div(className="card-pro", children=[
                    html.Div("Consumo simultáneo de actividades (%)",
                             className="card-head"),
                    dcc.Graph(id="g-heatmap", style={"height": "100%"}),
                ]),
            ],
        ),
    ],
)


# ==========================================================
# CALLBACKS
# ==========================================================

@callback(
    Output("kpi-representado",     "children"),
    Output("kpi-representado",     "style"),
    Output("kpi-representado",     "title"),
    Output("kpi-representado-box", "title"),
    Output("kpi-personas",         "children"),
    Output("kpi-personas",         "style"),
    Output("kpi-personas",         "title"),
    Output("kpi-personas-box",     "title"),
    Output("kpi-perfiles",         "children"),
    Output("kpi-perfiles",         "style"),
    Output("kpi-perfiles",         "title"),
    Output("kpi-perfiles-box",     "title"),
    Input("f-region", "value"),
    Input("f-genero", "value"),
    Input("f-nse",    "value"),
    Input("f-edad",   "value"),
)
def update_kpis(region, genero, nse, edad):
    df_f = apply_filters(df_all, region, genero, nse, edad)
    muestras = n_personas(df_f)
    pct = kpi_representado_pct(df_all, df_f)
    perfiles = kpi_perfiles_unicos(df_f)
    st = kpi_style(muestras)
    tt = kpi_tooltip(muestras)
    return (
        f"{pct:.1f}%",      st, tt, tt,
        f"{muestras:,}",    st, tt, tt,
        f"{perfiles:,}",    st, tt, tt,
    )


@callback(
    Output("g-participacion", "figure"),
    Output("g-ranking",       "figure"),
    Output("g-anillo",        "figure"),
    Output("g-heatmap",       "figure"),
    Input("f-region", "value"),
    Input("f-genero", "value"),
    Input("f-nse",    "value"),
    Input("f-edad",   "value"),
)
def update_graficos(region, genero, nse, edad):
    df_f = apply_filters(df_all, region, genero, nse, edad)
    return (
        fig_participacion_apilada(df_f),
        fig_top_consumo(df_f),
        fig_hist_cantidad_actividades(df_f),
        fig_heatmap_coconsumo_joint(df_f),
    )