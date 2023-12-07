import asyncio
import datetime
import pickle
from typing import Optional

from telethon import TelegramClient
from telethon.tl.patched import Message

from algo_neoquantxperience.common_constants import TOP45
from algo_neoquantxperience.nlp.settings import TG_API_HASH, TG_API_ID
from algo_neoquantxperience.nlp.structs import News, TickerNewsMap
from algo_neoquantxperience.nlp.utils import remove_emoji, remove_past

client = TelegramClient("anon", TG_API_ID, TG_API_HASH)


async def _aparse_telegram_messages(
    search_list: list[str],
    tg_group_id: int = -1001292964247,
) -> TickerNewsMap:
    """-1001292964247 is Full-Time Trading TG group."""
    ticker_news_map: TickerNewsMap = {}

    async def _aset_news(search_text: str) -> None:
        message: Message
        ticker_news_map[search_text] = []
        async for message in client.iter_messages(
            tg_group_id,
            search=search_text,
            reverse=True,
        ):
            ticker_news_map[search_text].append(
                News(datetime=message.date, text=message.message)
            )
        print(
            f"Num ticker_news_map with '{search_text}': {len(ticker_news_map[search_text])}.\n"
        )

    tasks = []
    for search_text in search_list:
        tasks.append(asyncio.create_task(_aset_news(search_text)))

    for task in tasks:
        await task

    return ticker_news_map


def parse_telegram_messages(
    search_list: Optional[list[str]] = None,
    tg_group_id: int = -1001292964247,
    start_date: Optional[datetime.datetime] = None,
) -> TickerNewsMap:
    """Parse telegram messages.

    Parameters
    ----------
    search_list: Optional[list[str]] = None
        List of tickers. Default: top45.
    tg_group_id: int = -1001292964247
        Telegram group ID. Default: Full-Time Trading.
    start_date: Optional[datetime.datetime] = None
        From which date to start parse. Default: all messages will be parsed.
        Notice: must use `tzinfo=datetime.timezone.utc`.

    Return
    ------
    ticker_news_map: TickerNewsMap
        Ticker: list of news mapping.
    """
    if search_list is None:
        search_list = TOP45

    with client:
        ticker_news_map = client.loop.run_until_complete(
            _aparse_telegram_messages(
                search_list=search_list,
                tg_group_id=tg_group_id,
            )
        )

    if start_date:
        ticker_news_map = remove_past(
            ticker_news_map=ticker_news_map,
            start_date=start_date,
        )
    ticker_news_map = remove_emoji(ticker_news_map)
    return ticker_news_map


if __name__ == "__main__":
    ticker_news_map = parse_telegram_messages(
        start_date=datetime.datetime(2023, 6, 1, tzinfo=datetime.timezone.utc)
    )
    with open("news.pkl", "wb") as handle:
        pickle.dump(ticker_news_map, handle, protocol=pickle.HIGHEST_PROTOCOL)
