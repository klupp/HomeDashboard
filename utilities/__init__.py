from aio import ThemeSwitchAIO
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px

from theme import template_theme1, template_theme2
from utilities.data.data_fetcher import fetch

from klupps_dash_model import DashModule
from utilities.data.data_fetcher import is_available
from utilities.data.utility_data import UtilityData


class UtilitiesModule(DashModule):
    def __init__(self):
        super().__init__()
        self.utility_data: UtilityData = None

    def is_available(self) -> bool:
        return is_available()

    def get_card(self, app: Dash):
        self.utility_data = fetch(False)

        utility_type_chooser = html.Div([
            dbc.Label("Choose Utility Type", html_for="utility_type_chooser"),
            dbc.Select(
                id='utility_type_chooser',
                options=[
                    {"label": contract_type, "value": contract_type} for contract_type in
                    self.utility_data.contracts_df.Type.unique()
                ],
                value='Gas'
            )
        ])

        slider = html.Div(
            [
                dbc.Label("Choose Period", html_for="utility_contract_year_chooser"),
                dcc.RangeSlider(id="utility_contract_year_chooser", min=2019, max=2022, step=1, value=[2019, 2022], marks={2019: '2019', 2020: '2020', 2021: '2021', 2022: '2022'}),
            ]
        )

        utility_graph = dcc.Graph(
            id='utility_graph'
        )

        @app.callback(
            Output("utility_contract_year_chooser", "min"),
            Output("utility_contract_year_chooser", "max"),
            Output("utility_contract_year_chooser", "value"),
            Output("utility_contract_year_chooser", "marks"),
            Input("utility_type_chooser", "value")
        )
        def update_contract_chooser(utility_type):
            contract_df = self.utility_data.contracts_df.copy()
            filtered_df = contract_df[contract_df.Type == utility_type]
            years = filtered_df.ContractYear.unique()
            return \
                int(years.min()), \
                int(years.max()), \
                [int(years.min()), int(years.max())], \
                {int(year): str(year) for year in years}

        @app.callback(
            Output("utility_graph", "figure"),
            Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
            Input("utility_type_chooser", "value"),
            Input("utility_contract_year_chooser", "value")
        )
        def create_line_plot(toggle, utility_type, contract_period):
            template = template_theme1 if toggle else template_theme2
            measurements_df = self.utility_data.measurements_df.copy()
            filtered_df = measurements_df[
                (measurements_df.Type == utility_type) &
                (measurements_df.ContractYear >= contract_period[0]) &
                (measurements_df.ContractYear <= contract_period[1])
            ]
            fig = px.line(
                filtered_df,
                x='date',
                y='aggregate_consumption',
                color='ContractName',
                markers=True,
                title=f"{utility_type} Consumption by Contract",
                hover_data={'aggregate_consumption': ':.2f'},
                labels={
                    "date": "Date of Measurement",
                    "aggregate_consumption": f"Aggregate Consumption of {utility_type} in kWh",
                    "ContractName": "Contract"
                },
                template=template)
            fig.update_layout(transition_duration=500, legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor='rgba(0,0,0,0)'))
            return fig

        return dbc.Card(
            children=[
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            utility_type_chooser,
                        ], width="auto"),
                        dbc.Col([
                            slider
                        ], width=4)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            utility_graph,
                        ], width="12")
                    ])
                ]),
            ]
        )
