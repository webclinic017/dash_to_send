"""Data set-up"""
import datetime as dt

import numpy as np
import pandas as pd
import pymongo
import yfinance as yf

from signals.utils.dashlogger import logger

MCLIENT = pymongo.MongoClient("mongodb://localhost:27017/")
DB_STOCK = MCLIENT['stock_prices']
COLLECTION_CLOSE = DB_STOCK['close']
COLLECTION_LAST_UPDATE = DB_STOCK['last_update']
COLLECTION_RETURN = DB_STOCK['return']


def update_price_data(symbols, col, start_date, end_date):
    """
    Fetch data through yfinance and save it to db.
    :param symbols: tickers of indexes and stocks
    :type symbols: list
    :param col: column name
    :type col: string
    :param start_date: start date
    :type start_date: str
    :param end_date: end date
    :type end_date: str
    :return: finish message
    :rtype: str
    """

    df = pd.DataFrame()

    close_col = DB_STOCK[col]

    try:
        for symbol in symbols:
            logger.info(f'Loading ticker: {symbol}.')
            # Download stock price data from Yahoo Finance
            data = yf.download(symbol, start=start_date, end=end_date)[[col.capitalize()]]
            data_s = data.rename(columns={col.capitalize(): symbol})
            df = pd.concat([df, data_s], axis=1)

        # Convert the DataFrame to a dictionary
        new_data = df.reset_index()

        # Check if the value already exists in the old data
        query = {'Date': {'$in': list(new_data['Date'])}}
        existing_data = close_col.find(query)

        if existing_data:
            try:
                # Update or insert new documents
                for document in new_data.to_dict(orient='records'):
                    close_col.update_one({'Date': document['Date']}, {"$set": document}, upsert=True)

            except pymongo.errors.ServerSelectionTimeoutError:
                logger.error('Could not connect to the database.')
        else:
            close_col.insert_many(new_data.to_dict(orient='records'))

        # only update the info if end_date is newer
        COLLECTION_LAST_UPDATE.update_many({'last_update': {'$lt': end_date}}, {"$set": {'last_update': end_date}})

        return 'Data successfully saved.'

    except Exception as e:
        logger.error("%s to %s data update failed due to %s. " % (start_date, end_date, e))


def update_return_data():
    """
    A function to read price data and calculate log return, save to db.
    It is called once price data is updated, i.e. per day, since the price data could be updated from the raw source,
    just to make it safer to re-calculate the return data in case any historical data changed for certain reasons.
    :return: function finished message
    :rtype: str
    """
    close_data = get_df_from_collection(COLLECTION_CLOSE)

    log_returns = np.log(close_data) - np.log(close_data.shift(1))
    log_returns = log_returns.reset_index()
    try:
        COLLECTION_RETURN.delete_many({})
        COLLECTION_RETURN.insert_many(log_returns.to_dict(orient='records'))
        return 'Data successfully saved.'

    except Exception as e:
        logger.error("Return data update failed due to %s. " % e)


def get_daily_data(col, symbols, start_date, end_date):
    """
    Function to fetch the data from database, given the inputs.
    :param col: The name of the collections, i.e. 'close', 'return'
    :type col: str
    :param symbols: tickers of indexes and stocks
    :type symbols: list
    :param start_date: start date, format of '%Y-%m-%d'
    :type start_date: str
    :param end_date: end date, format of '%Y-%m-%d'
    :type end_date: str
    :return: the corresponding data
    :rtype: pd.DataFrame
    """
    collection = DB_STOCK[col]
    query = {'Date': {'$gte': dt.datetime.strptime(start_date, '%Y-%m-%d'),
                      '$lte': dt.datetime.strptime(end_date, '%Y-%m-%d')}}

    projection = {'Date': 1} | {s: 1 for s in symbols}

    df = get_df_from_collection(collection, query=query, projection=projection)
    return df


def get_df_from_collection(collection, query={}, projection={}):
    """
    Function to transfer cursor to DataFrame, with Date as the index

    :param collection:
    :type collection:
    :param query:
    :type query:
    :param projection:
    :type projection:
    :return: dataframe
    :rtype: pd.DataFrame
    """
    try:
        df = pd.DataFrame(collection.find(query, projection))
        df = df.drop('_id', axis=1).set_index('Date')
        return df
    except Exception as e:
        logger.error("Failed to get df from the cursor due to %s. " % e)
        return pd.DataFrame()


def get_full_data_for_bt(stock, start_date, end_date):
    """
    A function to collect a few data to make the OHLCV for use in backtesting.
    :return: OHLCV data for the stock within start_date and end_date
    :rtype: pd.DateFrame
    """
    df = pd.DataFrame()
    for col in ['open', 'high', 'low', 'close', 'volume']:
        cdf = get_daily_data(col, [stock], start_date, end_date)
        cdf = cdf.rename(columns={stock: col})
        df = pd.concat([df, cdf], axis=1)
    df = df.dropna()
    df.index.name = 'date'

    return df

