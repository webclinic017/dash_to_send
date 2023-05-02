"""Analytics for regressions."""

import numpy as np
import pandas as pd
import plotly.graph_objs as go
import statsmodels.api as sm
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.linear_model import Lasso
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from signals.data.dataloader import get_daily_data
from signals.utils.dashhelper import get_regression_plot
from signals.utils.dashlogger import logger
from signals.utils.datahelper import INDEX_COMP


def get_regression_full_res(index_value, stock_values, start_date, end_date, title, add_plot=True):
    """
    Function to calculate regression results between the index and given basket of stocks between the date range.
    Can also return a regression scatter plot.

    :param index_value:
    :type index_value: str
    :param stock_values:
    :type stock_values: list
    :param start_date:
    :type start_date: str
    :param end_date:
    :type end_date: str
    :param title: plot title
    :type title: str
    :param add_plot:
    :type add_plot: bool
    :return: regression result between given stocks and index, and scatter plot
    :rtype: pd.DataFrame and fo.Figure
    """
    tickers = [index_value] + stock_values

    df = get_daily_data('return', tickers, start_date, end_date).fillna(0)
    x = df[stock_values]
    y = df[index_value]

    model = sm.OLS(y, x).fit()
    predictions = model.predict(x)
    coef = model.params.values
    res_df = pd.DataFrame(columns=stock_values, data=[coef])
    res_df['Stocks'] = 'Coefficient'

    cols = res_df.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    res_df = res_df[cols]

    str_sum = str(model.summary())

    if add_plot:
        y_predict = (coef * x).sum(axis=1)

        reg_plot = get_regression_plot(y_predict, y, title)

        return res_df, reg_plot, str_sum
    else:
        return res_df, go.Figure(), str_sum


def get_top_components_via_lasso(index_value, start_date, end_date, title, n_nonzero=10):
    """
    Function to identify the set of n(n_nonzero) securities that best explains the index given the certain date range.
    We use Lasso to decrease the features/stocks in the regression. The parameters to run Lasso can be further
    optimized by grid search in later version. Here we just use hard-coded ones.

    :param index_value: stock index
    :type index_value: str
    :param start_date: regression start date
    :type start_date: str
    :param end_date: regression end date
    :type end_date: str
    :param title: plot title
    :type title: str
    :param n_nonzero: number of stocks to chose
    :type n_nonzero: int
    :return: results of selected stocks and regression result vs the index
    :rtype: pd.DataFrame
    """
    stocks = INDEX_COMP[index_value]
    # When selecting the top stocks via Lasso, those with all NaN data within the selected time window
    # will not be considered.
    df = get_daily_data('return', [index_value] + stocks, start_date, end_date).dropna(axis=1, how='all').fillna(0)

    features = list(df.columns)
    features.remove(index_value)
    X = df[features]
    y = df[index_value]

    scaler = StandardScaler()
    selector = SelectKBest(f_regression, k=n_nonzero)
    # we can do a grid search to get optimized parameters, here we use hard-coded one
    lasso = Lasso(alpha=1e-6, max_iter=1000000)

    pipeline = Pipeline([
        ('scaler', scaler),
        ('selector', selector),
        ('model', lasso)
    ])

    pipeline.fit(X, y)

    selected_feature_indices = selector.get_support(indices=True)
    selected_features = [features[i] for i in selected_feature_indices]
    coefficients = pipeline.named_steps['model'].coef_

    if np.count_nonzero(coefficients) == n_nonzero:
        logger.info(f'Selected features: {selected_features, coefficients}')

    else:
        logger.warn(
            f'Could not find {n_nonzero} non-zero coefficients, likely due to alpha step not small enough, still return the feature list.')

    res, plot, summary = get_regression_full_res(index_value, selected_features, start_date, end_date, title)

    return res, plot, summary
