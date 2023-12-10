import time, threading

import torch
import numpy as np
import pandas as pd
import datetime
import pickle

from algo_neoquantxperience.algotrader.AlgoTrader import Dispatcher
from algo_neoquantxperience.tinkoff_api.tinkoff_api import SandboxTraderTinkoff
from algo_neoquantxperience.moexalgopack.utils import get_today_candles
from algo_neoquantxperience.nlp.utils import get_df_llm_scores, get_scores_from_source, get_df_from_ticker_news_map, get_scores_from_llm
from algo_neoquantxperience.nlp.parse import parse_telegram_messages
from algo_neoquantxperience.common_constants import IMOEX_FILTERED

LOTS_SIZES = pd.read_csv('../datasets_for_algotrader/45tickers_metainfo.csv')


class TradeBot:
    def __init__(self):
        self.__running = False
        self.tinkoff_trader = SandboxTraderTinkoff()

    def run(self, cash):
        self.__running = True
        self.loop_thread = threading.Thread(target=self.main_loop, kwargs={'cash':cash})
        self.loop_thread.start()
        self.loop_thread.run()

    def main_loop(self, cash):
        candles = get_today_candles(ticker_list=IMOEX_FILTERED)
        start_prices = np.array(candles[candles['begin'] == candles['begin'].max()]['close'])
        self.dispatcher = Dispatcher(cash=cash, tradebot=self,asynchroneous_mode=True, default_prices=start_prices)
        last_time = datetime.datetime.now() - datetime.timedelta(minutes=10)
        print(f'last_time {last_time}')
        while self.__running:
            # if datetime.datetime.now().minute // 10 == 0 and datetime.datetime.now().second < 5:
            if (datetime.datetime.now() - last_time) >= datetime.timedelta(minutes=10):
                last_time = datetime.datetime.now()
                self.trading_results = pd.DataFrame(columns=['datetime', 'total_money', 'cash'])

                # with open('../../data/nlp/ticker_news_map_with_scores.pkl', 'rb') as handle:
                #     ticker_news_map_base = pickle.load(handle)
                # ticker_news_map = parse_telegram_messages(
                #     start_date=datetime.datetime(2023, 6, 1, tzinfo=datetime.timezone.utc)
                # )
                # ticker_news_map = get_scores_from_source(ticker_news_map, ticker_news_map_base)
                # ticker_news_map = get_scores_from_llm(ticker_news_map)
                # cur_news = get_df_from_ticker_news_map(ticker_news_map)

                cur_news = get_df_llm_scores('../../data/nlp/ticker_news_map_with_scores.pkl', '../../news.pkl')
                cur_candles_data = get_today_candles(IMOEX_FILTERED)
                timepoint = cur_candles_data.begin.max()
                cur_candles_data = cur_candles_data.sort_values('ticker')
                count_ids = cur_candles_data.groupby('ticker').count()
                data_till_timepoint_ut = count_ids.loc[count_ids["open"] >= 51].index
                data_cur_timepoint = cur_candles_data[cur_candles_data.begin == timepoint].sort_values('ticker')
                news_till_timepoint = cur_news[cur_news.date <= timepoint]
                self.dispatcher.predictor.update_news_data(news_data=news_till_timepoint)
                predictions, date_to_predict = self.dispatcher.predictor.predict(cur_candles_data)
                predictions = predictions * torch.Tensor(
                    LOTS_SIZES.sort_values('ticker')[LOTS_SIZES['ticker'].isin(data_till_timepoint_ut)]['LOTSIZE']).unsqueeze(1).repeat(1, 2)
                cur_ticker_open_prices = list(data_cur_timepoint[['ticker', 'open']].itertuples(index=False))
                tickers = data_cur_timepoint['ticker']
                ticker_indexes = [self.dispatcher.algotrader.tickers_numbers[i] for i in tickers]
                self.dispatcher.algotrader.timer_tic(time=timepoint, #datetime.datetime.utcfromtimestamp(timepoint.tolist() / 1e9)
                                          cur_ticker_open_prices=cur_ticker_open_prices, predictions=predictions, ticker_indexes=ticker_indexes)
                self.trading_results.loc[len(self.trading_results.index)] = [timepoint, self.dispatcher.algotrader.total_money, self.dispatcher.algotrader.cash]
                print(timepoint, self.dispatcher.algotrader.total_money, self.dispatcher.algotrader.cash)
                self.dispatcher.algotrader.update_total_money()

    def stop(self):
        self.__running = False
        self.trading_results.to_csv(f'{datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")}_trading_results.csv', index=False)
        print('Session ended!')
