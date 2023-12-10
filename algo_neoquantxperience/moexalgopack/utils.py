import requests
import datetime

import apimoex
import pandas as pd
from moexalgo import Ticker, Market


def get_candles(ticker: str, date_start: str, date_end: str, period: str='10m', limit: int = 50000) -> pd.DataFrame:
    """
    period:
            Период в минутах 1, 10, 60 или '1m', '10m', '1h', 'D', 'W', 'M', 'Q'; по умолчанию 60
    :param ticker:
    :param date_start:
    :param date_end:
    :param period:
    :param limit:
    :return:
    """
    t = Ticker(ticker)
    res = pd.DataFrame(t.candles(date=date_start, till_date=date_end, period=period, limit=limit))
    return res


def get_today_candles(ticker_list):
    date = datetime.datetime.today().strftime("%Y-%m-%d")
    date_minus1 = (datetime.datetime.today()-datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    candles_dfs_list = []
    for ticker in ticker_list:
        try:
            ticker_df = get_candles(ticker, date, date)
            if len(ticker) < 50:
                ticker_df = get_candles(ticker, date_minus1, date)
            ticker_df['ticker'] = ticker
            candles_dfs_list.append(ticker_df)
        except Exception:
            print(f'{ticker} load failed')
    res = pd.concat(candles_dfs_list, ignore_index=True)
    return res


def get_index_tickers(index_ticker: str) -> pd.DataFrame:
    """
    Получить информацию по составу указанного индекса на текущую дату
    :return:
    """
    with requests.Session() as session:
        resp = apimoex.get_index_tickers(session, index_ticker, date=datetime.datetime.today().strftime('%Y-%m-%d'))
        index_tickers = pd.DataFrame.from_records(resp)
        index_tickers['index_ticker'] = index_ticker
    return index_tickers

