import datetime
import pickle
from typing import cast

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
                                              get_df_sentiment_with_diffs,
                                              remove_past)

st.set_page_config(layout="wide")
st.title("Анализ новостного фона")
l1, l2, l3 = st.columns((0.3, 0.3, 0.3))
date_start = l1.text_input("Start date", value="2023-06-01")
date_end = l2.text_input("End date", value="2024-01-01")
period = cast(str, l3.selectbox("Period", options=["10m", "1h", "D", "W"], index=2))
ticker = cast(str, st.selectbox("Choose ticker", options=TOP45, index=9))

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
df_scores = get_df_from_ticker_news_map(
    ticker_news_map, rerank=False, remove_template=True
)
df_scores = df_scores.loc[df_scores["date"] <= date_end]


m1, m2 = st.columns((1, 1))
indexes = [k + "__" + v for k, v in ALGOPACK_AVAILABLE_INDEXES.items()]
index = cast(str, m1.selectbox("Choose index", options=indexes, index=6)).split("__")[0]
# m2.text(ALGOPACK_AVAILABLE_INDEXES[index])
df_candles_stocks = get_candles(
    ticker,
    date_start=date_start,
    date_end=date_end,
    period=period,
)
df_candles_index = get_candles(
    index,
    date_start=date_start,
    date_end=date_end,
    period=period,
)

# m1.title("Цена акции")
fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.02)
fig.add_trace(
    go.Scatter(x=df_candles_index.begin, y=df_candles_index.close, name=f"Индекс {index} close"),
    row=1,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=df_candles_stocks.begin, y=df_candles_stocks.close, name=f"Цена акции {ticker} close"
    ),
    row=2,
    col=1,
)
df_rolling_mean = (
    df_scores.set_index("date")["score"]
    .resample("1d")
    .mean()
    .fillna(0)
    .rolling(5)
    .mean()
)
fig.add_trace(
    go.Scatter(
        x=df_rolling_mean.index,
        y=df_rolling_mean,
        name="Новостной фон",
    ),
    row=3,
    col=1,
)
fig.add_trace(
    go.Candlestick(
        x=df_scores.date,
        open=[0] * len(df_scores.score),
        close=df_scores.score,
        high=df_scores.score,
        low=df_scores.score,
        hovertext=df_scores.text,
        name="Сентимент новости",
    ),
    row=4,
    col=1,
)
idx1, idx2, idx3 = st.columns((0.2, 0.4, 0.2))
fig.update_layout(height=1000)
fig.update_xaxes(rangeslider_visible=False)
idx2.plotly_chart(fig, use_container_width=True, height=1000)
st.title("Зависимость изменения цены акции от сентимента новости")
m1, minter, m2 = st.columns((0.2, 0.1, 0.5))
m21, m22 = m2.columns((1, 1))
days_before = m21.selectbox("Период до новости", options=[1, 2, 3, 4, 5, 6, 7])
days_after = m22.selectbox(
    "Период после новости", options=[1, 2, 3, 4, 5, 20], index=4
)
df_scores["news_level"] = df_scores["score"].rolling(5).sum()
df_sentiment_with_diffs = get_df_sentiment_with_diffs(
    df_candles=df_candles_stocks,
    df_sentiment=df_scores,
    days_before=days_before,
    days_after=days_after,
)
column_to_analyze = "pct_change"
corr = df_sentiment_with_diffs.corr(numeric_only=True).loc["news_level", "pct_change"]
minter.text(f"Corr (Pearson): {corr}")
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df_sentiment_with_diffs.news_level,
        y=df_sentiment_with_diffs[column_to_analyze],
        mode="markers",
        marker={"size": 12},
    ),
)
fig.update_layout(xaxis_title="Новостной фон", yaxis_title="Percantage change")
m2.plotly_chart(fig, use_container_width=True)

with st.expander("Новости"):
    for row in df_scores.iloc[::-1].iterrows():
        s1, s2, s3 = st.columns((0.1, 0.1, 0.8))
        s1.text(row[1]["date"])
        s2.metric("Score by Gigachat", value=row[1]["score"])
        s3.text(row[1]["text"].replace("\n\n", "\n"))
