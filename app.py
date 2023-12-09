import datetime
import pickle

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from algo_neoquantxperience.common_constants import (
    ALGOPACK_AVAILABLE_INDEXES, TOP45)
from algo_neoquantxperience.moexalgopack.utils import get_candles
from algo_neoquantxperience.nlp.score import (get_scores_from_llm,
                                              get_scores_from_source)
from algo_neoquantxperience.nlp.utils import (get_df_from_ticker_news_map,
                                              remove_past)

st.set_page_config(layout="wide")
l1, l2, l3 = st.columns((0.3, 0.3, 0.3))
date_start = l1.text_input("Start date", value="2023-06-01")
date_end = l2.text_input("End date", value="2024-01-01")
period = l3.text_input("Period", value="1h")
ticker = st.selectbox("Choose ticker", TOP45)

with open("data/nlp/ticker_news_map_with_scores.pkl", "rb") as handle:
    ticker_news_map_base = pickle.load(handle)
with open("news.pkl", "rb") as handle:
    ticker_news_map = pickle.load(handle)
    ticker_news_map = {ticker: ticker_news_map[ticker]}
ticker_news_map = get_scores_from_source(ticker_news_map, ticker_news_map_base)
ticker_news_map = get_scores_from_llm(ticker_news_map)
ticker_news_map = remove_past(
    ticker_news_map,
    start_date=datetime.datetime(
        *[int(t) for t in date_start.split("-")], tzinfo=datetime.timezone.utc
    ),
)
df_scores = get_df_from_ticker_news_map(ticker_news_map)
df_candles_stocks = get_candles(
    ticker,
    date_start=date_start,  # "2023-05-24",
    date_end=date_end,  # "2023-12-04",
    period=period,  # "1h",
)


m1, m2 = st.columns((1, 1))
m1.text("Акция")
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Candlestick(
        x=df_candles_stocks.begin,
        open=df_candles_stocks.open,
        close=df_candles_stocks.close,
        high=df_candles_stocks.high,
        low=df_candles_stocks.low,
        name="stock_price",
    ),
    secondary_y=False,
)
fig.add_trace(
    go.Candlestick(
        x=df_scores.date,
        open=[0] * len(df_scores.score),
        close=df_scores.score,
        high=df_scores.score,
        low=df_scores.score,
        hovertext=df_scores.text,
        name="news_score",
        increasing_line_color="cyan",
        decreasing_line_color="gray",
    ),
    secondary_y=True,
)
fig.update_layout(width=10000)
m1.plotly_chart(fig, use_container_width=True)

m21, m22 = m2.columns((1,1))
index = m21.selectbox("Choose index", list(ALGOPACK_AVAILABLE_INDEXES.keys()))
m22.text(ALGOPACK_AVAILABLE_INDEXES[index])
df_candles_index = get_candles(
    index,
    date_start=date_start,
    date_end=date_end,
    period=period,
)
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Candlestick(
        x=df_candles_index.begin,
        open=df_candles_index.open,
        close=df_candles_index.close,
        high=df_candles_index.high,
        low=df_candles_index.low,
        name="index",
    ),
    secondary_y=False,
)
fig.add_trace(
    go.Candlestick(
        x=df_scores.date,
        open=[0] * len(df_scores.score),
        close=df_scores.score,
        high=df_scores.score,
        low=df_scores.score,
        hovertext=df_scores.text,
        increasing_line_color="cyan",
        decreasing_line_color="gray",
        name="news_score",
    ),
    secondary_y=True,
)
fig.update_layout(width=10000)
m2.plotly_chart(fig, use_container_width=True)
