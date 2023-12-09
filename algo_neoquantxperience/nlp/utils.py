import datetime

import emoji
import pandas as pd

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
    df.date = df.date.dt.tz_convert('Europe/Moscow').dt.tz_localize(None)
    return df
