"""Analytics for correlations."""
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
from pykalman import KalmanFilter
from scipy import stats
from statsmodels.tsa.stattools import coint

from config import SAVE_DIR
from signals.data.dataloader import get_daily_data
from signals.utils.dashlogger import logger
from signals.utils.datahelper import ALL_STOCKS

CORRELATION_SAVE_DIR = fr'{SAVE_DIR}\pair_trading'
os.makedirs(CORRELATION_SAVE_DIR, exist_ok=True)

CORR_METHODS_TABLE_DICT = {
    'pearson': ['Correlation', 'Correlation P-value'],
    'ols': ['OLS RSquared', 'OLS Beta', 'OLS Mean Reversion Speed'],
    'kalman': ['KF Beta', 'KF Mean Reversion Speed'],
    'coint': ['Coint P-value', 'Coint t-stats'],
}
CORR_METHODS_LIST = list(CORR_METHODS_TABLE_DICT.keys())


def get_correlation_metrics(stock1, stock2, ts_x, ts_y, method):
    """
    Return the correlation metrics between two tickers given the inputs.
   :param stock1: ticker of stock1
    :type stock1: str
    :param stock2: ticker of stock2
    :type stock2: str
    :param ts_x: timeseries of stock1
    :type ts_x: pd.Series
    :param ts_y: timeseries of stock2
    :type ts_y: pd.Series
    :param method: the method chosen
    :type method: str
    :return: correlation metrics
    :rtype: dict
    """

    try:
        res = {'Stocks Pair': stock1 + ' - ' + stock2}

        if method == 'pearson':
            # calculate the correlation and p-value
            corr, pvalue = stats.pearsonr(ts_x, ts_y)
            corr_res = {'Correlation': corr, 'Correlation P-value': pvalue, }
        elif method == 'ols':
            # perform OLS regression to calculate the beta and mean reversion speed
            ts_x = sm.add_constant(ts_x)
            model = sm.OLS(ts_y, ts_x).fit()
            rsquared = model.rsquared
            beta = model.params[1]
            mean_reversion_speed_ols = -np.log(beta)
            corr_res = {'OLS RSquared': rsquared, 'OLS Beta': beta,
                        'OLS Mean Reversion Speed': mean_reversion_speed_ols, }
        elif method == 'kalman':
            # perform Kalman filter to estimate the beta and mean reversion speed
            delta = 1e-3
            trans_cov = delta / (1 - delta) * np.eye(2)
            obs_mat = np.vstack([ts_x, np.ones(len(ts_x))]).T[:, np.newaxis]
            kf = KalmanFilter(n_dim_obs=1, n_dim_state=2,
                              initial_state_mean=np.zeros(2),
                              initial_state_covariance=np.ones((2, 2)),
                              transition_matrices=np.eye(2),
                              observation_matrices=obs_mat,
                              observation_covariance=1,
                              transition_covariance=trans_cov)
            kalman_means, kalman_covs = kf.filter(ts_y.values)
            slope = kalman_means[:, 0],

            beta = slope[0][-1]
            mean_reversion_speed_kalman = -np.log(beta)
            corr_res = {'KF Beta': beta, 'KF Mean Reversion Speed': mean_reversion_speed_kalman, }
        elif method == 'coint':
            result = coint(ts_x, ts_y)
            co_int_tstats = result[0]
            co_int_pvalue = result[1]
            corr_res = {'Coint P-value': co_int_pvalue, 'Coint t-stats': co_int_tstats, }
        else:
            corr_res = {}

        res |= corr_res
    except Exception as e:
        logger.warn(fr'Cannot get correlation metrics for {stock1} and {stock2} due to {e}, pass.')
        return {}
    return res


def get_correlation_full_res_helper(symbols, input_df, method):
    """
    Helper function to align the inputs, and collect results back in a list of dicts.

    :param symbols: list of stock pairs
    :type symbols: list
    :param input_df: all historical data
    :type input_df: pd.DataFrame
    :param method: the method chosen
    :type method: str
    :return: correlation results for all the combinations
    :rtype: list
    """
    res_l = []
    for symbol in symbols:
        stock1 = symbol[0]
        stock2 = symbol[1]
        ts1 = input_df[stock1]
        ts2 = input_df[stock2]
        res_l.append(get_correlation_metrics(stock1, stock2, ts1, ts2, method))

    return res_l


def get_correlation_full_res(start_date, end_date, method, topn):
    """
    Function to retrieve all data and select the top pairs with high correlation, then pass those into the helper
    function to calculate the correlation metrics. Noting, the selection is purely based on the correlations between
    their return time series, and we are NOT filtering the pairs like 'GOOGL' and 'GOOG' at this stage.

    Return all results into a DataFrame.

    into DataFrame
    :param start_date:
    :type start_date: dt.date
    :param end_date:
    :type end_date: dt.date
    :param method:
    :type method: str
    :param topn:
    :type topn: int
    :return:
    :rtype: pd.DataFrame
    """
    # For those tickers with NaN within the selected window, we know they will not have high correlation with the other
    # stocks, fillna with zero will do the same and for later easier to process the data
    input_df = get_daily_data('return', ALL_STOCKS, start_date, end_date).fillna(0)

    corr_matrix = input_df.corr()
    corr_matrix = corr_matrix.replace(1.0, 0)
    corr_pairs = corr_matrix.unstack().sort_values(ascending=False).drop_duplicates()
    symbols = corr_pairs[:int(topn)].index.tolist()

    res_l = get_correlation_full_res_helper(symbols, input_df, method)
    df = pd.DataFrame(res_l)

    sort_col = CORR_METHODS_TABLE_DICT[method][0]
    if method in ['coint']:
        df = df.sort_values(by=[sort_col])
    else:
        try:
            df = df.sort_values(by=[sort_col], ascending=False)
        except:
            print(1)

    df = df.reset_index().drop('index', axis=1)

    # df.to_csv(fr'{CORRELATION_SAVE_DIR}\{method}_result.csv')

    return df
