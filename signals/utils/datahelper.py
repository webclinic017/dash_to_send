import pickle

from config import BASE_DIR


def get_index_components(fdir=fr'{BASE_DIR}/signals/data/components.pkl'):
    """
    Assuming the components for 'GSPC', 'RUT', 'NDX' are static at this time, details saved in a pkl file. This function
    loads the pkl file into dict.
    Can revisit this part in the future for the cases when index re-balances/changes its components.
    :param fdir: file dir
    :type fdir: str
    :return: index as key and its components
    :rtype: dict
    """

    with open(fdir, 'rb') as handle:
        d = pickle.load(handle)
    return d


def get_all_tickers():
    """
    Load the components of the indexes and returns the full list of tickers pool.
    :return: list of tickers
    :rtype: list
    """
    d = get_index_components()
    all_tickers = [item.replace(' ', '_') for sublist in [[key, *sublist] for key, sublist in d.items()] for item in
                   sublist]
    res_l = list(set(all_tickers))
    res_l.sort()
    return res_l


INDEX_COMP = get_index_components()
ALL_TICKERS = get_all_tickers()
ALL_INDEXES = list(INDEX_COMP.keys())
ALL_STOCKS = list(set(ALL_TICKERS) - set(ALL_INDEXES))
