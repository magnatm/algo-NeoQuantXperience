import datetime
import pickle
from os import path

import emoji
import numpy as np
import pandas as pd

from algo_neoquantxperience.nlp.score import (get_scores_from_llm,
                                              get_scores_from_source)
from algo_neoquantxperience.nlp.structs import News, TickerNewsMap


def remove_past(
    ticker_news_map: TickerNewsMap,
    start_date: datetime.datetime,
) -> TickerNewsMap:
    output_filter_date: TickerNewsMap = {}
    for ticker, newses in ticker_news_map.items():
        chosen_date = max(
            (news.datetime for news in newses if news.datetime < start_date)
        )
        output_filter_date[ticker] = [
            news for news in newses if news.datetime >= chosen_date
        ]
    return output_filter_date


def remove_emoji(ticker_news_map: TickerNewsMap) -> TickerNewsMap:
    output_filter_emoji = {}
    for ticker, newses in ticker_news_map.items():
        output_filter_emoji[ticker] = [
            News(datetime=news.datetime, text=emoji.replace_emoji(news.text))
            for news in newses
        ]
    return output_filter_emoji


def get_df_from_ticker_news_map(
    ticker_news_map: TickerNewsMap,
    rerank: bool = False,
    remove_template: bool = False,
) -> pd.DataFrame:
    dfs = []
    for ticker, newses in ticker_news_map.items():
        dates, scores, texts = [], [], []
        for news in newses:
            dates.append(news.datetime)
            scores.append(news.score)
            texts.append(news.text)
        dfs.append(
            pd.DataFrame(
                {
                    "ticker": ticker,
                    "date": dates,
                    "score": scores,
                    "text": texts,
                }
            )
        )
    df = pd.concat(dfs)
    df = df.astype({"score": float})
    df = df.sort_values(by=["ticker", "date"]).reset_index(drop=True)
    df.date = df.date.dt.tz_convert("Europe/Moscow").dt.tz_localize(None)

    def _rerank(score: float) -> float:
        if score >= 2:
            return 1.0
        elif -2 < score < 2:
            return 0.0
        else:
            return -1.0

    if rerank:
        df.loc[:, "score"] = df["score"].map(_rerank)

    bad_template = "САМЫЕ ВАЖНЫЕ СОБЫТИЯ ЭТОЙ НЕДЕЛИ"
    if remove_template:
        df = df.loc[~df['text'].str.contains(bad_template)].reset_index(drop=True)
    return df


def get_df_llm_scores(
    path_to_news_with_scores: str, path_to_actual_news: str
) -> pd.DataFrame:
    with open(path_to_news_with_scores, "rb") as handle:
        ticker_news_map_base = pickle.load(handle)
    with open(path_to_actual_news, "rb") as handle:
        ticker_news_map = pickle.load(handle)
    ticker_news_map = get_scores_from_source(ticker_news_map, ticker_news_map_base)
    ticker_news_map = get_scores_from_llm(ticker_news_map)
    df = get_df_from_ticker_news_map(ticker_news_map)
    return df


def get_df_sentiment_with_diffs(
    df_candles: pd.DataFrame,
    df_sentiment: pd.DataFrame,
    days_before: int = 1,
    days_after: int = 3,
) -> pd.DataFrame:
    df_tmp = df_sentiment.copy()
    df_tmp["diff"] = np.nan
    for row in df_sentiment.iterrows():
        news_date = pd.to_datetime(row[1].date.date())
        close_before = (
            df_candles[df_candles.begin < news_date]
            .tail(days_before)["close"]
            .values.mean()
        )
        close_after = (
            df_candles[df_candles.begin >= news_date]
            .head(days_after)["close"]
            .values.mean()
        )
        df_tmp.loc[row[0], "diff"] = close_after - close_before
        df_tmp.loc[row[0], "pct_change"] = (
            df_candles[df_candles.begin >= news_date]
            .head(days_after)["close"]
            .pct_change(periods=1)
            .mean()
            * 100
        )

    return df_tmp
