from dash import Dash, html, dcc, page_container, Input, Output, callback
import dash_bootstrap_components as dbc

from src.data import load_data, dropdown_options

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)

df_all = load_data()

PAGE_TITLES = {
    "/":           "Inicio",
    "/tv":         "TV",
    "/cine":       "Cine",
    "/redes":      "Redes Sociales",
    "/videojuegos":"Videojuegos",
}

app.layout = html.Div(
    className="app-shell",
    children=[

        dcc.Location(id="url", refresh=False),

        # SIDEBAR
        html.Div(
            className="sidebar-pro",
            children=[
                html.Div([
                    html.Div("Pantallas y Cultura Digital en Argentina",
                             className="nav-title"),
                    html.Div(
                        "Análisis ponderado según la Encuesta Nacional de Consumos Culturales 2022",
                        className="nav-subtitle"),
                ]),

                html.Hr(),

                dbc.Nav(
                    [
                        dbc.NavLink("Inicio",        href="/",
                                    active="exact", className="navlink"),
                        dbc.NavLink("TV",           href="/tv",
                                    active="exact", className="navlink"),
                        dbc.NavLink("Cine",         href="/cine",
                                    active="exact", className="navlink"),
                        dbc.NavLink("Redes",        href="/redes",
                                    active="exact", className="navlink"),
                        dbc.NavLink("Videojuegos",  href="/videojuegos",
                                    active="exact", className="navlink"),
                    ],
                    vertical=True,
                ),
            ],
        ),

        # CONTENIDO PRINCIPAL
        html.Div(
            className="page-wrap",
            children=[
                html.Div(
                    className="topbar",
                    children=[
                        html.Div(
                            className="topbar-inner",
                            children=[
                                html.Div(id="page-title", className="page-title-topbar"),
                                html.Div(
                                    className="filters-row",
                                    children=[
                                        dcc.Dropdown(
                                            id="f-region",
                                            options=dropdown_options(df_all, "region"),
                                            multi=True,
                                            placeholder="Región",
                                            className="filter-dd",
                                        ),
                                        dcc.Dropdown(
                                            id="f-genero",
                                            options=dropdown_options(df_all, "genero"),
                                            multi=True,
                                            placeholder="Género",
                                            className="filter-dd",
                                        ),
                                        dcc.Dropdown(
                                            id="f-nse",
                                            options=dropdown_options(df_all, "nse_3"),
                                            multi=True,
                                            placeholder="Nivel Socioeconómico",
                                            className="filter-dd",
                                        ),
                                        dcc.Dropdown(
                                            id="f-edad",
                                            options=dropdown_options(
                                                df_all, "grupos_edad"),
                                            multi=True,
                                            placeholder="Grupo de Edad",
                                            className="filter-dd",
                                        ),
                                        html.Button(
                                            "✕ Borrar filtros",
                                            id="btn-clear-filters",
                                            className="btn-clear-filters",
                                            n_clicks=0,
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),

                # CONTENIDO DE CADA PÁGINA
                page_container,
            ],
        ),
    ],
)


@callback(
    Output("page-title", "children"),
    Input("url", "pathname"),
)
def update_page_title(pathname):
    return PAGE_TITLES.get(pathname, "")


@callback(
    Output("f-region", "value"),
    Output("f-genero", "value"),
    Output("f-nse",    "value"),
    Output("f-edad",   "value"),
    Input("btn-clear-filters", "n_clicks"),
    prevent_initial_call=True,
)
def clear_filters(n):
    return None, None, None, None


if __name__ == "__main__":
    app.run(debug=True, port=8051)