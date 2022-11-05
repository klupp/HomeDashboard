import pandas as pd
from aio import ThemeSwitchAIO
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

from theme import template_theme1, template_theme2
import numpy as np

from klupps_dash_model import DashModule

from utilities.data.utility_data import UtilityData
from utilities.data.utility_data_fetcher_csv import UtilityDataFetcherCSV


class UtilitiesModule(DashModule):
    def __init__(self):
        super().__init__()

    def is_available(self) -> bool:
        return True

    def get_card(self, app: Dash):
        utility_data_store = dcc.Store(id='utility_data_store')

        new_measurement_button = html.Div([
            dbc.Label("Measurement", html_for="new_measurement_button"),
            html.Br(),
            dbc.Button(
                "Add New",
                id="new_measurement_button",
                external_link=True,
                target="_blank",
                href="http://192.168.0.36:5003/",
                color="primary"
            )
        ])

        utility_type_chooser = html.Div([
            dbc.Label("Choose Utility Type", html_for="utility_type_chooser"),
            dbc.Select(
                id='utility_type_chooser'
            )
        ])

        graph_type_chooser = html.Div([
            dbc.Label("Choose Graph Type", html_for="utility_graph_type_chooser"),
            dbc.Select(
                id='utility_graph_type_chooser',
                options=[
                    {"label": "Consumption", "value": "Consumption"},
                    {"label": "Price", "value": "Price"}
                ],
                value="Consumption"
            )
        ])

        slider = html.Div(
            [
                dbc.Label("Choose Period", html_for="utility_contract_year_chooser"),
                dcc.RangeSlider(
                    id="utility_contract_year_chooser",
                    min=2019,
                    max=2022,
                    step=1,
                    value=[2019, 2022],
                    marks={2019: '2019', 2020: '2020', 2021: '2021', 2022: '2022'}
                ),
            ]
        )

        utility_graph = dcc.Graph(
            id='utility_graph'
        )

        @app.callback(
            Output('utility_data_store', 'data'),
            Input("refresh_interval", "n_intervals")
        )
        def refresh_utility_data(n_intervals):
            utility_data = UtilityDataFetcherCSV()
            utility_data_json = utility_data.to_json(date_format='iso', orient='split')
            return utility_data_json

        @app.callback(
            Output('utility_type_chooser', 'options'),
            Output('utility_type_chooser', 'value'),
            Input('utility_data_store', 'data'),
        )
        def update_utility_type_chooser(utility_data_json):
            utility_data = UtilityData.from_json(utility_data_json)

            options = [
                          {"label": contract_type, "value": contract_type} for contract_type in
                          utility_data.contracts_df.Type.unique()
                      ]
            value = options[1]['value']

            return options, value

        @app.callback(
            Output("utility_contract_year_chooser", "min"),
            Output("utility_contract_year_chooser", "max"),
            Output("utility_contract_year_chooser", "value"),
            Output("utility_contract_year_chooser", "marks"),
            Input('utility_data_store', 'data'),
            Input("utility_type_chooser", "value")
        )
        def update_contract_chooser(utility_data_json, utility_type):
            utility_data = UtilityData.from_json(utility_data_json)
            contract_df = utility_data.contracts_df.copy()
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
            Input('utility_data_store', 'data'),
            Input("utility_type_chooser", "value"),
            Input("utility_contract_year_chooser", "value"),
            Input("utility_graph_type_chooser", "value")
        )
        def create_line_plot(toggle, utility_data_json, utility_type, contract_period, utility_graph_type):
            utility_data = UtilityData.from_json(utility_data_json)
            template = template_theme1 if toggle else template_theme2
            measurements_df = utility_data.measurements_df.copy()
            contracts_df = utility_data.contracts_df.copy()
            contracts_df = contracts_df[
                (contracts_df.Type == utility_type) &
                (contracts_df.ContractYear >= contract_period[0]) &
                (contracts_df.ContractYear <= contract_period[1])
            ]
            measurements_df = measurements_df.merge(contracts_df, left_on='contract', right_on='ID', sort=False)
            payment_plan_df = utility_data.contract_payment_plan_df.copy()
            payment_plan_df = payment_plan_df.merge(contracts_df, left_on='ContractID', right_on='ID', sort=False)
            df = pd.DataFrame(['contract', 'date', 'amount', 'type'])
            if utility_graph_type == 'Price':
                unit_type = 'EUR'
                mdf = measurements_df[['date', 'aggregate_price', 'contract']].copy()
                mdf.columns = ['date', 'amount', 'contract']
                mdf['type'] = 'Spent'

                pdf = payment_plan_df[['PaymentDate', 'AggregatePaymentAmount', 'ContractID']].copy()
                pdf.columns = ['date', 'amount', 'contract']
                pdf['type'] = 'Payment'

                df = pd.concat([df, mdf, pdf], ignore_index=True)
            else:
                unit_type = 'kWh'
                mdf = measurements_df[['date', 'aggregate_consumption', 'contract']].copy()
                mdf.columns = ['date', 'amount', 'contract']
                mdf['type'] = 'Consumed'
                df = pd.concat([df, mdf], ignore_index=True)

            df['date'] = pd.to_datetime(df['date'])
            df.sort_values(by='date', inplace=True, ignore_index=True)
            fig = px.line(
                df,
                x='date',
                y='amount',
                color='contract',
                title=f"{utility_type} {utility_graph_type} by Contract",
                hover_data={'amount': ':.2f'},
                line_dash='type',
                markers=True,
                labels={
                    "date": "Date of Measurement",
                    "amount": f"Cumulative {utility_graph_type} of {utility_type} in {unit_type}",
                    "contract": "Contract",
                    "type": "Type"
                },
                template=template)
            fig.update_layout(
                transition_duration=500,
                margin_r=0,
                margin_l=50,
                # legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor='rgba(0,0,0,0)')
            )

            return fig

        return dbc.Card(
            children=[
                utility_data_store,
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            new_measurement_button
                        ], width="auto"),
                        dbc.Col([
                            utility_type_chooser
                        ], width="auto"),
                        dbc.Col([
                            graph_type_chooser
                        ], width="auto")
                    ]),
                    dbc.Row([
                        dbc.Col([
                            slider
                        ], width=True)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            utility_graph,
                        ], width="12")
                    ])
                ]),
            ]
        )
