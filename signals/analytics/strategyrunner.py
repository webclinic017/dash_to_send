"""Analytics for backtest."""
from collections import OrderedDict

import backtrader as bt
import backtrader.indicators as btind
import numpy as np
import pandas as pd
import plotly.io
from backtrader import Analyzer
from backtrader_plotly.plotter import BacktraderPlotly
from pandas import Series

from signals.data.dataloader import get_full_data_for_bt
from signals.utils.dashhelper import strategy_plot
from signals.utils.dashlogger import logger


class PairTradingStrategy(bt.Strategy):
    params = dict(
        period=10,
        qty1=0,
        qty2=0,
        printout=False,
        zs=2,
        status=0,
    )

    def __init__(self, params=None):
        if params is not None:
            for name, val in params.items():
                setattr(self.params, name, val)
        # To control operation entries
        self.orderid = None
        self.qty1 = self.p.qty1
        self.qty2 = self.p.qty2
        self.upper_limit = self.p.zs
        self.lower_limit = -self.p.zs

        self.status = self.p.status
        self.period = self.p.period

        # Signals performed with PD.OLS :
        self.transform = btind.OLS_TransformationN(self.data0, self.data1,
                                                   period=self.period)
        self.zscore = self.transform.zscore

    def log(self, txt, dt=None):
        if self.p.printout:
            dt = dt or self.data.datetime[0]
            logger.info(dt, ': ' + txt)

    def notify_order(self, order):
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
            return

        if order.status == order.Completed:
            if order.isbuy():
                buytxt = 'BUY COMPLETE, %.2f' % order.executed.price
                self.log(buytxt, order.executed.dt)
            else:
                selltxt = 'SELL COMPLETE, %.2f' % order.executed.price
                self.log(selltxt, order.executed.dt)

        elif order.status in [order.Expired, order.Canceled, order.Margin]:
            self.log('%s ,' % order.Status[order.status])
            pass

        # Allow new orders
        self.orderid = None

    def next(self):

        if self.orderid:
            return  # if an order is active, no new orders are allowed

        if self.p.printout:
            logger.info('Self  len:', len(self))
            logger.info('Data0 len:', len(self.data0))
            logger.info('Data1 len:', len(self.data1))
            logger.info('Data0 len == Data1 len:',
                        len(self.data0) == len(self.data1))

            logger.info('Data0 dt:', self.data0.datetime.datetime())
            logger.info('Data1 dt:', self.data1.datetime.datetime())

            logger.info('status is', self.status)
            logger.info('zscore is', self.zscore[0])

        if (self.zscore[0] > self.upper_limit) and (self.status != 1):
            self.status = 1
            self.order_target_percent(self.data1, 0)  # data1 = y
            self.order_target_percent(self.data0, 1)  # data0 = x

        elif (self.zscore[0] < self.lower_limit) and (self.status != 2):
            self.order_target_percent(self.data0, 0)  # data0 = x
            self.order_target_percent(self.data1, 1)  # data1 = y
            self.status = 2

    def stop(self):
        if self.p.printout:
            logger.info('==================================================')
            logger.info('Starting Value - %.2f' % self.broker.startingcash)
            logger.info('Ending   Value - %.2f' % self.broker.getvalue())
            logger.info('==================================================')


class SortinoRatio(bt.Analyzer):
    """
    Computes the Sortino ratio metric for the whole account using the strategy, based on the R package
    PerformanceAnalytics SortinoRatio function
    """
    params = {"MAR": 0}  # Minimum Acceptable Return

    def __init__(self):
        self.acct_return = dict()
        self.acct_last = self.strategy.broker.get_value()
        self.sortinodict = dict()

    def next(self):
        if len(self.data) > 1:
            # I use log returns
            curdate = self.strategy.datetime.date(0)
            self.acct_return[curdate] = np.log(self.strategy.broker.get_value()) - np.log(self.acct_last)
            self.acct_last = self.strategy.broker.get_value()

    def stop(self):
        srs = Series(self.acct_return)  # Need to pass a time-series-like object to SortinoRatio
        srs.sort_index(inplace=True)

        mean = srs.mean() * 252 - self.params.MAR
        std_neg = srs[srs < 0].std() * np.sqrt(252)
        self.sortinodict['sortinoratio'] = mean / std_neg
        del self.acct_return

    def get_analysis(self):
        return self.sortinodict


class TotalValue(Analyzer):
    """
    This analyzer will get total value from every next. 
    """

    params = ()

    def start(self):
        super(TotalValue, self).start()
        self.rets = OrderedDict()

    def next(self):
        # Calculate the return
        super(TotalValue, self).next()
        self.rets[self.datas[0].datetime.datetime()] = self.strategy.broker.getvalue()

    def get_analysis(self):
        return self.rets


def get_cerebro_and_data(stock1, stock2, start_date, end_date, ):
    cerebro = bt.Cerebro()
    df1 = get_full_data_for_bt(stock1, start_date, end_date)
    df2 = get_full_data_for_bt(stock2, start_date, end_date)

    data0 = bt.feeds.PandasData(dataname=df1, name=stock1)
    data1 = bt.feeds.PandasData(dataname=df2, name=stock2)

    cerebro.adddata(data0)
    cerebro.adddata(data1)
    cerebro.broker.setcash(1000000.0)

    cerebro.addsizer(bt.sizers.PercentSizer, percents=10)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe", timeframe=bt.TimeFrame.Days, compression=1,
                        factor=252, annualize=True)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(SortinoRatio, MAR=0.00004,
                        _name="sortino")  # Sortino ratio with risk-free rate of 0.004% daily (~1% annually)
    cerebro.addanalyzer(TotalValue, _name='totalvalue')

    return cerebro, df1, df2


def get_bt_results(stock1, stock2, start_date, end_date, params_range, params=None):
    cerebro, df1, df2 = get_cerebro_and_data(stock1, stock2, start_date, end_date, )

    cerebro.optstrategy(
        PairTradingStrategy,
        period=range(params_range['rp_min'], params_range['rp_max'] + 1, params_range['rp_step']),
        zs=range(params_range['zs_min'], params_range['zs_max'] + 1, params_range['zs_step']),

    )

    results = cerebro.run(maxcpus=1)

    par_list = [[x[0].params.period, x[0].params.zs,
                 x[0].analyzers.returns.get_analysis()['rnorm100'],
                 x[0].analyzers.drawdown.get_analysis()['max']['drawdown'],
                 x[0].analyzers.sharpe.get_analysis()['sharperatio'],
                 x[0].analyzers.sortino.get_analysis()['sortinoratio']
                 ] for x in results]

    total_df = pd.DataFrame(par_list, columns=['Rolling Period', 'ZS Limit', 'Return', 'MaxDrawdown', 'SharpeRatio',
                                               'SortinoRatio'])

    par_df = total_df[(total_df['Rolling Period'] == params['period']) & (total_df['ZS Limit'] == params['zs'])]
    idx = par_df.index.values[0]
    par_df.reset_index().drop(['index', 'Rolling Period', 'ZS Limit'], axis=1)
    total_df = total_df.sort_values('SharpeRatio', ascending=False).reset_index().drop(['index'], axis=1)

    df_tv = pd.DataFrame([results[idx][0].analyzers.totalvalue.get_analysis()]).T
    df_tv.columns = ['Total_Value']

    df_ols = pd.DataFrame()
    df_ols[stock1] = df1['close']
    df_ols[stock2] = df2['close']
    df_ols['Corr'] = df_ols[stock1].rolling(params['period']).corr(df_ols[stock2])

    plot_sub = strategy_plot(df_ols, df_tv, start_date, end_date, params['period'])

    return par_df, plot_sub, total_df


def get_bt_html_plot(stock1, stock2, start_date, end_date, params=None):
    cerebro, df1, df2 = get_cerebro_and_data(stock1, stock2, start_date, end_date, )
    cerebro.addstrategy(PairTradingStrategy, params)
    results = cerebro.run(maxcpus=1)

    figs = cerebro.plot(BacktraderPlotly(show=False, ), )
    # we just run one strategy, save the html of the plot to a variable
    plot_html = plotly.io.to_html(figs[0][0], full_html=False)

    return plot_html
