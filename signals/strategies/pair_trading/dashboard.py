"""Instantiate Dash app on pair-trading."""
import datetime as dt
import time

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dash_table, dcc, html, Output, Input, State
from dash.dash_table.Format import Format, Scheme

from signals.analytics.correlations import CORR_METHODS_LIST, get_correlation_full_res
from signals.analytics.strategyrunner import get_bt_results, get_bt_html_plot
from signals.strategies.pair_trading.layout import html_layout
from signals.utils.dashhelper import get_cols_from_bt_tbl
from signals.utils.dashlogger import logger, dashLoggerHandler

RP_MIN = 50
RP_MAX = 150
RP_STEP = 50
ZS_MIN = 1
ZS_MAX = 3
ZS_STEP = 1


def init_dashboard(server):
    """Create a Plotly Dash dashboard."""
    app = dash.Dash(
        server=server,
        routes_pathname_prefix='/pair_trading/',
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            '/static/dist/css/styles.css',
            'https://fonts.googleapis.com/css?family=Lato'
        ]
    )

    # Table building function
    def build_layout():
        layout = html.Div([
            html.Div([
                html.Div([
                    html.H4('Regression Period'),
                    dcc.DatePickerRange(
                        id='regression_period',
                        min_date_allowed=dt.date(2018, 1, 1),
                        max_date_allowed=dt.date.today(),
                        start_date=dt.date(2020, 1, 1),
                        end_date=dt.date(2021, 1, 1),
                        display_format='D MMM YYYY',
                    ), ],
                    style={'width': '25%', 'height': '30px', 'display': 'inline-block',
                           "margin-right": '0px', "verticalAlign": "top"}
                ),

                html.Div([
                    html.H4('Method'),
                    dcc.Dropdown(
                        CORR_METHODS_LIST,
                        'pearson',
                        id='method',
                        style={'height': '40px', }
                    )],
                    style={'width': '15%', 'height': '40px', 'display': 'inline-block',
                           "margin-right": '50px', "verticalAlign": "top"}
                ),
                html.Div([
                    html.H4('Top N pairs'),
                    dcc.Input(
                        value=10,
                        id='topnpairs',
                        debounce=True,
                        type='number',
                        style={'height': '40px', 'width': '60px', 'backgroundColor': '#D3D3D3',
                               'boarderColor': '#D3D3D3'}
                    )],
                    style={'width': '15%', 'display': 'inline-block',
                           "margin-right": '0px', "verticalAlign": "top"}
                ),

                html.Div([
                    html.H4('Get Correlations'),
                    html.Button(
                        'Start',
                        id='corr_button',
                        style={'font-size': '14px', 'height': '40px', 'width': '140px',
                               'display': 'inline-block', "margin-bottom": '10px', "margin-left": '5px', }
                    )],
                    style={'width': '15%', 'height': '40px', 'display': 'inline-block',
                           "margin-left": '0px', "verticalAlign": "top"}  # "margin-top": '10px',
                ),

            ], style={'margin-left': '10px', }),
            html.P(),

            html.Div(
                children=[
                    dash_table.DataTable(
                        id='regression_table',
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
                ],
                style={'padding': '25px', 'flex': 1}
            ),

            html.Div([
                html.Div([
                    html.H4('Backtest Period'),
                    dcc.DatePickerRange(
                        id='backtest_period',
                        min_date_allowed=dt.date(2018, 1, 1),
                        max_date_allowed=dt.date.today(),
                        start_date=dt.date(2020, 1, 1),
                        end_date=dt.date(2021, 1, 1),
                        display_format='D MMM YYYY',
                    )],
                    style={'width': '25%', 'height': '30px', 'display': 'inline-block',
                           "margin-right": '0px', "verticalAlign": "top"}
                ),

            ], style={'margin-left': '10px', }),
            html.P(),

            html.Div(id='slider-output-container',
                     style={'color': 'blue', 'fontSize': 16, 'fontWeight': 'bold', 'margin-top': '70px',
                            'margin-bottom': '20px', 'margin-left': '10px'}),

            html.Div([
                html.Div([
                    html.Label('Rolling Period'),
                    dcc.Slider(
                        min=RP_MIN,
                        max=RP_MAX,
                        step=RP_STEP,
                        value=100,
                        id='rp_slider',
                    )
                ], style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'top'}),
                html.Div([
                    html.Label('Z-Score Limit'),
                    dcc.Slider(
                        min=ZS_MIN,
                        max=ZS_MAX,
                        step=ZS_STEP,
                        value=2,
                        id='zs_slider'
                    )
                ], style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'top'})
            ], style={'margin-left': '10px', }),

            html.Div(
                children=[
                    dash_table.DataTable(
                        id='strategy_table',
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
                ],
                style={'padding': '25px', 'flex': 1}
            ),

            dcc.Graph(id='strategy_plot', style={'padding': '1px', 'width': '100%'}),

            html.Div(
                [

                    dbc.Button(
                        "Click to see trades details", id="open-body-scroll", n_clicks=0, style={'height': '40px',
                                                                                                 'width': '15%', }
                    ),
                    dbc.Modal(
                        [
                            dbc.ModalHeader(dbc.ModalTitle("Trade details of strategy backtesting")),
                            dbc.ModalBody([
                                html.Iframe(
                                    id='bt_plot',
                                    style={
                                        'border': 'none',
                                        'height': '1400px',
                                        'width': '100%',
                                        'padding': '0',
                                        'margin': '0'
                                    }
                                )]),
                            dbc.ModalFooter(
                                dbc.Button(
                                    "Close",
                                    id="close-body-scroll",
                                    className="ms-auto",
                                    n_clicks=0,
                                )
                            ),
                        ],
                        id="modal-body-scroll",
                        size='xl',
                        scrollable=True,
                        is_open=False,
                    ),
                ], style={'margin-left': '10px', }
            ),

            html.Div('Parameters running the strategy ranked by Sharp Ratio, top row shows optimized parameters ',
                     style={'color': 'blue', 'fontSize': 16, 'fontWeight': 'bold', 'margin-top': '20px',
                            'margin-bottom': '5px', 'margin-left': '10px'}),

            html.Div(
                children=[
                    dash_table.DataTable(
                        id='optimization_table',
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
                ],
                style={'padding': '25px', 'flex': 1}
            ),

            html.Div([
                dcc.Interval(id='log-interval', interval=10 * 1000, n_intervals=0),
                html.H4(id='div_out', children='Log'),
                html.Iframe(id='console-out', srcDoc='',
                            style={'width': '100%', 'height': '100%', "border": "2px solid black"})
            ]),

        ])

        return layout

    # Custom HTML layout
    app.index_string = html_layout

    # Create Layout
    app.layout = build_layout()

    @app.callback(
        Output('regression_table', 'data'),
        Output('regression_table', 'columns'),
        Output('regression_table', 'active_cell'),
        State('regression_table', 'active_cell'),
        Input('corr_button', 'n_clicks'),
        Input('method', 'value'),
        Input('topnpairs', 'value'),
        Input('regression_period', 'start_date'),
        Input('regression_period', 'end_date'),
        prevent_initial_call=True)
    def get_correlation_table(active_cell, submit, method, topn, start_date, end_date):
        """
        Get top correlated pairs in table.

        """

        try:
            topn = int(topn)
        except Exception as e:
            logger.wanr(fr'Topn must be an int, got error of: {e}. Please check your input, using 10 as default.')
            topn = 10

        logger.info(
            fr'Start calculation finding {topn} most correlated pairs between '
            f'{start_date} and {end_date}, showing metrics under the method of "{method}".'
        )

        t1 = time.time()

        rdf = get_correlation_full_res(start_date, end_date, method, topn)

        display_table_cols = []
        for i in rdf.columns:
            if i == 'Stocks Pair':
                display_table_cols.append({'name': i, 'id': i, 'hideable': True, })
            elif ('P-value' in i) or ('t-stats' in i):
                display_table_cols.append({'name': i, 'id': i, 'hideable': True, 'type': 'numeric',
                                           'format': Format(precision=4, scheme=Scheme.exponent)})
            else:
                display_table_cols.append({'name': i, 'id': i, 'hideable': True, 'type': 'numeric',
                                           'format': {'specifier': '.4f'}})

        out_table = rdf.to_dict('records')
        if active_cell is None:
            active_cell = {'row': 0, 'column': 0, 'column_id': 'Stocks Pair', 'row_id': out_table[0]['Stocks Pair']}

        logger.info('Finished calculation finding the most correlated pairs.')

        t2 = time.time()
        dlt = t2 - t1
        logger.info('Total time used in finding most correlated pairs: ' + '%0.2f' % dlt + ' seconds.')

        return out_table, display_table_cols, active_cell

    @app.callback(
        Output('slider-output-container', 'children'),
        Input('regression_table', 'active_cell'),
        State('regression_table', 'data'),
        Input('rp_slider', 'value'),
        Input('zs_slider', 'value'),
        prevent_initial_call=True,
    )
    def update_slider_output(active_cell, tdf, rp_value, zs_value):
        """
        Callback function to update the sliders outputs.

        """
        tdf = pd.DataFrame(tdf)
        [stock1, stock2] = tdf.loc[active_cell['row'], 'Stocks Pair'].split(' - ')

        return fr'You have selected pair of "{stock1}" and "{stock2}" to backtest with parameter of ' \
               fr'Rolling Period: "{rp_value}", Z-Score limit: "{zs_value}".'

    @app.callback(
        Output('strategy_table', 'data'),
        Output('strategy_table', 'columns'),
        Output('strategy_plot', 'figure'),
        Output('bt_plot', 'srcDoc'),
        Output('optimization_table', 'data'),
        Output('optimization_table', 'columns'),
        # Input('bt_button', 'n_clicks'),
        Input('regression_table', 'active_cell'),
        State('regression_table', 'data'),
        Input('backtest_period', 'start_date'),
        Input('backtest_period', 'end_date'),
        Input('rp_slider', 'value'),
        Input('zs_slider', 'value'),
        prevent_initial_call=True,
    )
    def get_bt_plot(active_cell, tdf, start_date, end_date, rp_value, zs_value):
        """
        Backtesting results in table and plot.

        """

        logger.info(fr'Start generating results of backtesting between {start_date} and {end_date}.')
        t1 = time.time()

        params_range = {'rp_min': RP_MIN, 'rp_max': RP_MAX, 'rp_step': RP_STEP, 'zs_min': ZS_MIN, 'zs_max': ZS_MAX,
                        'zs_step': ZS_STEP}
        params = {'period': rp_value, 'zs': zs_value, }

        tdf = pd.DataFrame(tdf)
        [stock1, stock2] = tdf.loc[active_cell['row'], 'Stocks Pair'].split(' - ')
        par_df, plot_sub, total_df = get_bt_results(stock1=stock1, stock2=stock2, start_date=start_date,
                                                    end_date=end_date, params_range=params_range, params=params)
        display_table_cols = get_cols_from_bt_tbl(par_df)

        out_table = par_df.to_dict('records')

        display_table_cols_total = get_cols_from_bt_tbl(total_df)

        out_table_total = total_df.to_dict('records')

        html_plot = get_bt_html_plot(stock1, stock2, start_date, end_date, params=params)

        logger.info('Finished generating results of backtesting.')

        t2 = time.time()
        dlt = t2 - t1
        logger.info('Total time used in running backtest: ' + '%0.2f' % dlt + ' seconds.')

        return out_table, display_table_cols, plot_sub, html_plot, out_table_total, display_table_cols_total

    @app.callback(
        Output("modal-body-scroll", "is_open"),
        [
            Input("open-body-scroll", "n_clicks"),
            Input("close-body-scroll", "n_clicks"),
        ],
        [State("modal-body-scroll", "is_open")],
    )
    def toggle_modal(n1, n2, is_open):
        """
        dbc.modal helper callback. dbc.Modal used to show trade details in the running the strategy in backtesting.

        """
        if n1 or n2:
            return not is_open
        return is_open

    @app.callback(
        Output('console-out', 'srcDoc'),
        Input('log-interval', 'n_intervals')
    )
    def update_output(n):
        """
        Set callback to grab dash logging in the console to a separate box in the GUI.
        """
        return ('\n'.join(dashLoggerHandler.queue)).replace('\n', '<BR>')

    return app.server
