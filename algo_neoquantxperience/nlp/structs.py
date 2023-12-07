import datetime
from dataclasses import dataclass
from typing import Optional

Ticker = str


@dataclass
class News:
    datetime: datetime.datetime
    text: str
    score: Optional[float] = None


TickerNewsMap = dict[Ticker, list[News]]
