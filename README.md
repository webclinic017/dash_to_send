# BlueCrest Signal Dashboards

This project is built using a Flask application that contains multiple Dash apps, each hosted on a separate web route.
To
start the site, simply run the <mark>wsgi.py</mark> file in your Python IDE

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the build requirements.

```bash
pip install -r requirements.txt
```

## Project tree

The main source code for this project is located in the 'signals' folder, which is organized into several subfolders:

- analytics:
    - contains modules for performing calculations related to correlation and regression, as well as a backtesting
      strategy runner.
- data:
    - includes scripts for loading data from yfinance to MongoDB, as well as loading data from MongoDB for use
      downstream.
- strategies:
    - contains the dashboard GUI and layout for the two projects on pair-trading and index-regression.
- utils:
    - utility functions related to logging, data loading, figure plotting, dash formatting, and more

```bash
signals
├───analytics
│   └───correlations.py
│   └───regressions.py
│   └───strategyrunner.py
├───data
│   └───components.pkl
│   └───dataloader.py
├───static
├───strategies
│   ├───index_regression
│   │   └───dashboard.py
│   │   └───layout.py
│   └───pair_trading
│   │   └───dashboard.py
│   │   └───layout.py
├───templates
├───utils
│   │   └───dashhelper.py
│   │   └───dashlogger.py
│   │   └───datalogger.py
└───__init__.py
└───__assets__.py
└───__routes__.py
└───__users__.py

```

## Memo

### Dash/Flask



The two current Dash apps can be found in 'signals/strategies/..'. To add additional Dash apps or signals, it follows a
similar format. First, register the app in 'signals/init.py'. Next, set up a link to the app on the home page by
editing 'signals/templates/index.jinja2'.

Additionally, Flask in this project allows the admin to set a password for controlling user access to the pages, though
this feature is currently commented out for ease of use

![](/signals/static/img/home.png)


### Pair-Trading



- The raw data for this project is downloaded from yfinance to MongoDB, with all GUI and analytics in the repository
  retrieving data from MongoDB directly ( calling```python pymongo.MongoClient("mongodb://localhost:27017/")```).
- The components of each index are saved in the 'data/components.pkl' file, assuming such information remains static.
- 'Backtrader' is used to run backtest strategies, with a few customized classes added to enable backtrader to run
  certain performance metrics as requested.
- The strategy for backtesting stocks pair-trading is to capture when their correlation has an extreme Z-Score. Users
  can control
  two parameters using sliders: the rolling period (in days) for calculating the correlation, and the Z-Score limit for
  both the upper and lower sides.
- The GUI is self-explanatory, and in addition to tables and plots on the main page, trade details in running the
  backtest can also be viewed
  via a dbc.Button/Modal."


### Index-Regression

- To obtain the regression results for a given list of stocks from the dropdown menu, sm.OLS is used.
- For identifying the best 10 stocks to represent the index, Lasso regression is utilized.


### Snapshots of GUI

- Pair-Trading

![](/signals/static/img/pt.png)

- Backtest strategy

![](/signals/static/img/bt.png)

- Index-regression

![](/signals/static/img/ir.png)


