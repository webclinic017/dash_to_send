"""Instantiate Dash app on index regression."""
import datetime as dt

import dash
import plotly.graph_objs as go
from dash import dash_table, dcc, html, Output, Input, State

from signals.analytics.regressions import get_regression_full_res, get_top_components_via_lasso
from signals.strategies.index_regression.layout import html_layout
from signals.utils.dashhelper import get_cols_from_reg_tbl
from signals.utils.dashlogger import logger
from signals.utils.datahelper import INDEX_COMP, ALL_INDEXES

INDEX_DROPDOWN_OPTIONS = [{'label': i[1:], 'value': i} for i in ALL_INDEXES]
STOCK_DROPDOWN_OPTIONS = {}
for k, v in INDEX_COMP.items():
    STOCK_DROPDOWN_OPTIONS[k] = [{'label': i, 'value': i} for i in v]


def init_dashboard(server):
    """Create a Plotly Dash dashboard."""
    app = dash.Dash(
        server=server,
        routes_pathname_prefix='/index_regression/',
        external_stylesheets=[
            '/static/dist/css/styles.css',
            'https://fonts.googleapis.com/css?family=Lato'
        ]
    )

    # Table building function
    def build_layout():
        layout = html.Div([
            html.Div([
                html.Div([
                    html.H3('Regression Period'),
                    dcc.DatePickerRange(
                        id='regression_period',
                        min_date_allowed=dt.date(2018, 1, 1),
                        max_date_allowed=dt.date.today(),
                        start_date=dt.date(2020, 1, 1),
                        end_date=dt.date(2021, 1, 1),
                        display_format='D MMM YYYY',
                    )],
                    style={'width': '25%', 'height': '30px', 'padding': 0, 'display': 'inline-block',
                           "margin-right": '15px', "verticalAlign": "top"}
                ),

                html.Div([
                    html.H4('Index'),
                    dcc.Dropdown(
                        id='index_dropdown',
                        options=INDEX_DROPDOWN_OPTIONS,
                        style={'height': '40px', 'width': '150px', }
                    )],
                    style={'width': '15%', 'display': 'inline-block',
                           "margin-right": '0px', "verticalAlign": "top"}
                ),

                html.Div([
                    html.H4('Stocks (Max 10 selections)'),
                    dcc.Dropdown(
                        id='stock_dropdown',
                        multi=True,
                        style={'height': '40px', }
                    )],
                    style={'width': '50%', 'display': 'inline-block',
                           "margin-right": '15px', "verticalAlign": "top"}
                ),

            ], style={"margin-left": '10px', }),
            html.P(),

            html.Div([
                html.H4('Get Regression Result (please click every time after dropdowns are changed)'),
                html.Button(
                    'Start',
                    id='reg_button',
                    style={'font-size': '14px', 'height': '40px', 'width': '140px',
                           'display': 'inline-block', "margin-bottom": '10px'}
                )],
                style={'width': '50%', 'height': '40px', 'display': 'inline-block',
                       "margin-left": '10px', }
            ),

            html.Div(
                children=[

                    html.Div(id='selection_output_container',
                             style={'color': 'blue', 'fontSize': 16, 'fontWeight': 'bold', 'margin-top': '10px',
                                    'margin-left': '10px'}),

                    dash_table.DataTable(
                        id='selection_table',
                        sort_action='native',
                        sort_mode='single',
                        page_action='native',
                        style_header={
                            'padding': '1px',
                            'minwidth': '200px',
                            'whiteSpace': 'normal',
                            'fontWeight': 'bold',
                            'textOverflow': 'ellipsis',
                            'overflow': 'hidden',
                        },
                        style_table={
                            'overflowY': 'auto',
                            'overflowx': 'auto'
                        },
                        style_cell={
                            'textAlign': 'center',
                            'height': 'auto',
                            'whiteSpace': 'normal',
                            'minwidth': '100px',
                            'padding': '1px',
                            'overflowY': 'auto',
                            'overflowx': 'auto'
                        },
                        export_format='xlsx',
                        export_headers='display',
                        fill_width=True,
                    ),

                    dcc.Graph(id='selection_plot', style={'padding': '1px', 'width': '100%', 'margin-top': '20px'}),

                    html.P(id='selection_summary', style={'whiteSpace': 'pre-wrap'}),

                    html.P(),

                    html.H2('Top 10 securities that best explains the index',
                            style={'padding': '1px', 'margin-top': '20px'}),

                    dash_table.DataTable(
                        id='opt_table',
                        sort_action='native',
                        sort_mode='single',
                        page_action='native',
                        style_header={
                            'padding': '1px',
                            'minwidth': '200px',
                            'whiteSpace': 'normal',
                            'fontWeight': 'bold',
                            'textOverflow': 'ellipsis',
                            'overflow': 'hidden',
                        },
                        style_table={
                            'overflowY': 'auto',
                            'overflowx': 'auto'
                        },
                        style_cell={
                            'textAlign': 'center',
                            'height': 'auto',
                            'whiteSpace': 'normal',
                            'minwidth': '100px',
                            'padding': '1px',
                            'overflowY': 'auto',
                            'overflowx': 'auto'
                        },
                        export_format='xlsx',
                        export_headers='display',
                        fill_width=True,
                    ),

                    dcc.Graph(id='opt_plot', style={'padding': '10px', 'width': '100%', }),

                    html.P(id='opt_str_sum', style={'whiteSpace': 'pre-wrap'}),

                    html.Div(id='opt_output_container',
                             style={'color': 'blue', 'fontSize': 16, 'fontWeight': 'bold', 'margin-top': '10px',
                                    'margin-bottom': '20px', 'margin-left': '10px'}),

                ], style={'padding': '25px', 'flex': 1}

            ),

        ])

        return layout

    # Custom HTML layout
    app.index_string = html_layout

    # Create Layout
    app.layout = build_layout

    @app.callback(
        Output('stock_dropdown', 'options'),
        [Input('stock_dropdown', 'value'), ],
        Input('index_dropdown', 'value'),
    )
    def update_dropdown_options(values, index_dropdown_value):
        """
        Define the callback to limit the number of selections in the second dropdown
        """

        stock_options = STOCK_DROPDOWN_OPTIONS.get(index_dropdown_value, [])
        if values is None:
            return stock_options
        else:
            if len(values) == 10:
                return [option for option in stock_options if option['value'] in values]
            else:
                return stock_options

    @app.callback(
        Output('selection_table', 'data'),
        Output('selection_table', 'columns'),
        Output('selection_plot', 'figure'),
        Output('selection_summary', 'children'),
        Output('selection_output_container', 'children'),
        Input('reg_button', 'n_clicks'),
        State('index_dropdown', 'value'),
        [State('stock_dropdown', 'value'), ],
        State('regression_period', 'start_date'),
        State('regression_period', 'end_date'),
        prevent_initial_call=True,
    )
    def get_rg_tb_plot(n_clicks, index_value, stock_values, start_date, end_date):
        """
        Generate regression table and plot.
        """

        logger.info(fr'Start calculation for weights between {start_date} and {end_date}, using stocks '
                    f'of {stock_values} against {index_value}.')

        if index_value is None or stock_values is None or len(stock_values) == 0:
            return [], [], go.Figure(), '', 'No index/stock value, please check!'
        else:
            try:
                rdf, out_plot, summary = get_regression_full_res(index_value, stock_values, start_date, end_date,
                                                                 fr'Plot on regression of {stock_values} and {index_value[1:]}')

                display_table_cols = get_cols_from_reg_tbl(rdf)

                out_table = rdf.to_dict('records')

                if rdf.empty:
                    reg_output_container_msg = 'Failed to get regression results, please check your inputs.'
                else:
                    reg_output_container_msg = ''

                return out_table, display_table_cols, out_plot, summary, reg_output_container_msg
            except Exception as e:
                return [], [], go.Figure(), '', fr'Cannot get the regression result due to {e}, please check your inputs.'

    @app.callback(
        Output('opt_table', 'data'),
        Output('opt_table', 'columns'),
        Output('opt_plot', 'figure'),
        Output('opt_str_sum', 'children'),
        Output('opt_output_container', 'children'),
        Input('index_dropdown', 'value'),
        Input('regression_period', 'start_date'),
        Input('regression_period', 'end_date'),
        prevent_initial_call=True,
    )
    def get_opt_plot(index_value, start_date, end_date):
        """
        Generate the table containing 10 stocks that best explain the index and the coefficients from the regressions.

        """

        if index_value is None:
            return [], [], go.Figure(), '', 'No index value, please check!'
        else:
            try:
                rdf, plot, summary = get_top_components_via_lasso(index_value, start_date, end_date,
                                                                  fr'Plot on regression of best 10 stocks and {index_value[1:]}',
                                                                  n_nonzero=10)

                display_table_cols = get_cols_from_reg_tbl(rdf)

                out_table = rdf.to_dict('records')

                if rdf.empty:
                    opt_output_container_msg = 'Failed to get regression results, please check your inputs.'
                else:
                    opt_output_container_msg = ''

                return out_table, display_table_cols, plot, summary, opt_output_container_msg
            except Exception as e:
                return [], [], go.Figure(), '', fr'Cannot get best 10 stocks due to {e},  please check your inputs.'

    return app.server
