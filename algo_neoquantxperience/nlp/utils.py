import datetime

import emoji

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
