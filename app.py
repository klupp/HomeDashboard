from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import ThemeSwitchAIO

from theme import url_theme1, url_theme2
from utilities import UtilitiesModule


custom_css = './assets/custom.css'
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"

app = Dash(__name__, external_stylesheets=[url_theme1, dbc_css, custom_css])

app.title = "KluppsHomeDash"

theme_switch = html.Span(
    [
        ThemeSwitchAIO(
            aio_id="theme",
            themes=[url_theme1, url_theme2],
            icons={"left": "fa fa-sun", "right": "fa fa-moon"}
        )
    ],
    className="g-0 ms-auto flex-nowrap mt-3 mt-md-0"
)

PLOTLY_LOGO = "https://images.plot.ly/logo/new-branding/plotly-logomark.png"

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=PLOTLY_LOGO, height="30px")),
                        dbc.Col(dbc.NavbarBrand("Klupps Dashboard", className="ms-2")),
                    ],
                    align="center",
                    className="g-0",
                ),
                href="#",
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                theme_switch,
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ]
    ),
    color="dark",
    dark=True
)

utilities_module = UtilitiesModule()
utilities_module.is_available()

app.layout = html.Div([
    navbar,
    dbc.Row(
        children=[
            dbc.Col(
                children=[
                    utilities_module.get_card(app)
                ],
                width="12", lg=6, xl=4
            ),
        ],
        justify='around'
    )]
)


@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0")
