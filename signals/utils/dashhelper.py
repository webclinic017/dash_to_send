import datetime as dt

import pandas as pd
import plotly.express as px
from dash.dash_table.Format import Format, Scheme
from plotly.subplots import make_subplots


def get_cols_from_reg_tbl(rdf):
    """
    Util function to get the dashtable col from input regression result DataFrame
    :param rdf:
    :type rdf: pd.DataFrame
    :return:
    :rtype: list
    """
    display_table_cols = [{'name': i, 'id': i, 'hideable': True, 'type': 'numeric',
                           'format': Format(precision=4, scheme=Scheme.exponent)} if i != 'Stocks' else {
        'name': i, 'id': i, 'hideable': True, } for i in rdf.columns]
    return display_table_cols


def get_cols_from_bt_tbl(rdf):
    """
    Util function to get the dashtable col from input backtesting result DataFrame
    :param rdf:
    :type rdf: pd.DataFrame
    :return:
    :rtype: list
    """
    display_table_cols = [{'name': i, 'id': i, 'hideable': True, 'type': 'numeric',
                           'format': {'specifier': '.4f'}} if i not in ['Rolling Period', 'ZS Limit'] else {
        'name': i, 'id': i,
        'hideable': True, } for i in rdf.columns]
    return display_table_cols


def strategy_plot(df1, df2, start_date, end_date, rolling_period):
    """
    Util function to generate pair-trading strategy performance plot in dash,subplot of rolling ols and total value.
    :param df1:
    :type df1:
    :param df2:
    :type df2:
    :param start_date:
    :type start_date:
    :param end_date:
    :type end_date:
    :param rolling_period:
    :type rolling_period:
    :return:
    :rtype:
    """
    start_date = dt.datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = dt.datetime.strptime(end_date, '%Y-%m-%d').date()
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, horizontal_spacing=0, vertical_spacing=0.01,
                        row_heights=[1, 1])

    fig.add_scatter(x=df1.index, y=df1['Corr'], mode='lines', row=1, col=1, name='ols')
    fig.add_scatter(x=df2.index, y=df2['Total_Value'], mode='lines', row=2, col=1, name='Total_Value')

    fig.update_xaxes(range=[start_date + dt.timedelta(days=int(rolling_period / 5 * 7)), end_date],
                     rangeslider_visible=False, rangebreaks=[dict(bounds=['sat', 'mon'])])
    fig.update_yaxes(title_text='Rolling OLS Corr', row=1, col=1)
    fig.update_yaxes(title_text='Total Value', row=2, col=1)

    fig.update_layout(
        # xaxis_title=None,
        # yaxis_title=None,
        # legend_title=None,
        margin=dict(l=60, r=60, t=5, b=5),
        paper_bgcolor='white',
        showlegend=False,
    )

    return fig


def get_regression_plot(xs, ys, title):
    """
    Function to generate regression scatter plot with ols trendline.
    :param xs:
    :type xs: pd.Series
    :param ys:
    :type ys: pd.Series
    :param title: plot title
    :type title: str
    :return:
    :rtype: go.Figure
    """
    df = pd.concat([xs, ys], axis=1)
    df.columns = ['x', 'y']

    fig = px.scatter(df, x='x', y='y', color_discrete_sequence=['blue'], trendline='ols',
                     trendline_color_override='red')

    fig.update_xaxes(title_text='Regression Result via OLS')
    fig.update_yaxes(title_text='Actual Index Performance')

    fig.update_layout(
        title=dict(text=title, automargin=True, yref='paper', x=0.5),
        paper_bgcolor='white',
    )

    return fig
