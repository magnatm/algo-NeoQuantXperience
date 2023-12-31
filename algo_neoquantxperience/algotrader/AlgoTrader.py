from enum import Enum
import threading as th  
import numpy as np
import datetime
import torch
from algo_neoquantxperience.algotrader.make_future_timesteps import make_future_timesteps, MakeFutureKnownDataArgs, MakeFutureDateArgs
import pandas as pd
from algo_neoquantxperience.common_constants import TOP45_DICT

LOTS_SIZES = pd.read_csv('../datasets_for_algotrader/45tickers_metainfo.csv')
CALENDAR_DATA = pd.read_parquet('../datasets_for_algotrader/calendar.parquet')

def _add_time_idxs(df: pd.DataFrame) -> pd.DataFrame:
    counts = df.groupby(["id"])["id"].count()
    max_count = counts.max()

    time_idx_eq_end_column = []
    for count in counts.values:
        time_idx_eq_end_column += np.arange(max_count - count, max_count).tolist()

    df["time_idx_eq_end"] = time_idx_eq_end_column
    df["time_idx_eq_end"] = df["time_idx_eq_end"].astype(int)

    return df


class Predicton:
    def __init__(self, model_path='TemporalFusionTransformer.pt'):
        self.model = torch.load(model_path)
        self.ids_in_train = ['AFKS', 'AFLT', 'AGRO', 'ALRS', 'CBOM', 'CHMF', 'ENPG', 'FEES',
       'FIVE', 'GAZP', 'GLTR', 'GMKN', 'HYDR', 'IRAO', 'LKOH', 'MAGN',
       'MGNT', 'MOEX', 'MTSS', 'NLMK', 'NVTK', 'OZON', 'PHOR', 'PIKK',
       'PLZL', 'POLY', 'POSI', 'QIWI', 'ROSN', 'RTKM', 'RUAL', 'SBER',
       'SBERP', 'SELG', 'SGZH', 'SNGS', 'SNGSP', 'TATN', 'TATNP', 'TCSG',
       'TRNFP', 'UPRO', 'VKCO', 'VTBR', 'YNDX']
        self.last_x = 0
        
    def fades(self,x):
        if np.isnan(x):
            self.last_x = 0.99 * self.last_x
            return self.last_x
        self.last_x = x
        return self.last_x
        
        
    def update_news_data(self,news_data):
        news_data['date'] = news_data['date'].dt.ceil('10min',nonexistent='shift_backward')  
        news_data = news_data.set_index('date').groupby('ticker').resample("10min", origin="end").agg("mean", numeric_only=True).reset_index()
        news_data = news_data.rename(columns={'date':'begin'})
        # news_data['begin'] = pd.to_datetime(news_data.begin).dt.tz_localize(None) + datetime.timedelta(hours=3)
        self.news_data = news_data[['score','begin','ticker']]
        
        
    def predict(self, history_data):
        self.last_x = 0
        history_data = history_data.loc[history_data['ticker'].isin(self.ids_in_train)]
        history_data['begin'] = pd.to_datetime(history_data['begin'])
        min_last_date = history_data.groupby('ticker')['begin'].max().min()
        history_data = history_data.loc[history_data['begin'] <= min_last_date]
        history_data = pd.merge(left=history_data, right=self.news_data, how='left', on=['begin','ticker'])
        
        history_data['score'] = history_data['score'].apply(self.fades)
        history_data['id'] = history_data['ticker']
        # print(history_data.groupby('id')['id'].count())
        history_data = history_data.sort_values(['id','begin'])
        history_data = history_data.set_index('begin').groupby('id').resample("10min", origin="end").aggregate("mean").reset_index().ffill()
        
        history_data['ticker'] = history_data['id']
        # print(history_data.groupby('ticker')['ticker'].count())
        df_orig = _add_time_idxs(history_data)
        
        
        minute_calendar_df = CALENDAR_DATA
        minute_calendar_df = minute_calendar_df.rename(columns={'date':"begin"})

        df = df_orig.merge(minute_calendar_df, how="left", on='begin')


        df_anomaly_filtered_test = make_future_timesteps(
        df,
        add_timesteps=1,
        forward_fill_column_names=['ticker'],
        date_args=MakeFutureDateArgs(
            date_column_name='begin',
            freq='10min',
        ),
        known_data_args=MakeFutureKnownDataArgs(
            minute_calendar_df,
            common_column_names=['begin'],
        )
        )
        df_anomaly_filtered_forecast = make_future_timesteps(
        df,
        add_timesteps=1,
        forward_fill_column_names=['ticker'],
        date_args=MakeFutureDateArgs(
            date_column_name='begin',
            freq='10min',
        ),
        known_data_args=MakeFutureKnownDataArgs(
            minute_calendar_df,
            common_column_names=['begin'],
        )
        ).ffill()
        preds, indexes = self.model.predict(df_anomaly_filtered_forecast.ffill(), mode="quantiles", return_index=True)
        time_idx_pred = indexes['time_idx_eq_end'].unique()[0]
        date_to_predict = df_anomaly_filtered_forecast.loc[df_anomaly_filtered_forecast['time_idx_eq_end']==time_idx_pred]['begin'].unique()[0]
        return preds[:,0][:,0:5:4], date_to_predict
    


    

class Dispatcher:
    def __init__(self, cash, tradebot, asynchroneous_mode=False, default_prices=None):
        self.asynchroneous_mode = asynchroneous_mode
        self.default_prices = default_prices
        # Тут должны создаваться стратегии и получаться начальные цены
        # Список начальных цен записывается в cur_prices
        # if default_prices == None:
        #     cur_prices = torch.zeros(self.tickers_len)
        # else:
        #     cur_prices = self.default_prices
        self.algotrader = Algotrader(cash, default_prices, self, comission=1e-5, timeout=10)
        self.tradebot = tradebot
        # self.predictor = Predicton(config_path, tickers, ids_in_train, path_to_calendar)
        self.predictor = Predicton()
        self.lot_sizes = LOTS_SIZES.sort_values('ticker')['LOTSIZE']
        self.start_dataset = None
        self.backtest_results = None
        self.ticker_reversed_dict = {value: ind for ind, value in self.algotrader.tickers_numbers.items()}
        self.trading_delta = datetime.timedelta(minutes=10)
    
    def request_buy_or_sell(self, instrument, volume, price, buy=True, callback=None):
        #request_number = round(torch.rand(1).item() * 1000)
        print("instrument:", self.ticker_reversed_dict[instrument])
        print("volume:",volume)
        print("price:",price)

        if buy:
            order_id = self.tradebot.tinkoff_trader.buy(ticker=self.ticker_reversed_dict[instrument], quantity=volume)
            order_state = self.tradebot.tinkoff_trader.get_order_state(order_id=order_id)
            if order_state==1:
                if callback:
                    callback(instrument, volume, price)
        else:
            order_id = self.tradebot.tinkoff_trader.sell(ticker=self.ticker_reversed_dict[instrument], quantity=volume)
            order_state = self.tradebot.tinkoff_trader.get_order_state(order_id=order_id)
            if order_state == 1:
                if callback:
                    callback(instrument, volume, price)
        return order_id
    
    def delete_request(self,buy_request_id):
        print("buy_request_id:", buy_request_id)
        
    def get_timedelta_today(self, date_time):
        return date_time - self.midnight(date_time)
        
        
    def midnight(self, date_time):
        return date_time.replace(hour=0, minute=0, second=0)
    
        
    def test_algotrader(self):
        T = 50
        n = self.tickers_len
        predictions_tensor_diff = 0.5 - torch.rand(T,n)
        price_tensor_diff = predictions_tensor_diff + 0.1 * (0.5 - torch.rand(T,n))
        prediction_tensor_diff_25 = predictions_tensor_diff - 0.05 * torch.rand(T,n)
        prediction_tensor_diff_75 = predictions_tensor_diff + 0.05 * torch.rand(T,n)
        prices = self.default_prices
        trading_time = self.midnight(datetime.datetime.now()) + datetime.timedelta(hours=9, minutes=30)
        trading_delta = datetime.timedelta(minutes=10)
        for i in range(T-1):
            trading_time += trading_delta
            prediction_25 = prices + prediction_tensor_diff_25[i]
            prediction_75 = prices + prediction_tensor_diff_75[i]
            prediction = torch.stack([prediction_25, prediction_75], dim=1)
            self.algotrader.timer_tic(trading_time, prices, prediction)
            prices += price_tensor_diff[i]

    def backtest_algotrader(self, df_45_by_10min: pd.DataFrame, news_data: pd.DataFrame) -> pd.DataFrame:
        self.backtest_results = pd.DataFrame(columns=['datetime', 'total_money', 'cash'])
        filter = ['SBER', 'SBERP', 'SNGSP', 'SGZH', 'RTKM', 'QIWI', 'MOEX']
        timepoints_df_45_by_10min = sorted(list(df_45_by_10min['begin'].unique()))[50:]  # чтобы была история данных для предиктора
        for timepoint in timepoints_df_45_by_10min:
            data_till_timepoint = df_45_by_10min[df_45_by_10min.begin <= timepoint].sort_values('ticker')
            count_ids = data_till_timepoint.groupby('ticker').count()
            data_till_timepoint_ut = count_ids.loc[count_ids["open"]>=51].index
            
#             data_till_timepoint_ut = sorted(data_till_timepoint.ticker.unique())
            news_till_timepoint = news_data[news_data.date <= timepoint]
            self.predictor.update_news_data(news_data=news_till_timepoint)
            predictions, date_to_predict = self.predictor.predict(data_till_timepoint)
            print(date_to_predict)
            data_cur_timepoint = data_till_timepoint[data_till_timepoint.begin == timepoint].sort_values('ticker')
            predictions = predictions * torch.Tensor(LOTS_SIZES.sort_values('ticker')[LOTS_SIZES['ticker'].isin(data_till_timepoint_ut)]['LOTSIZE']).unsqueeze(1).repeat(1, 2)
            
            data  = pd.DataFrame(np.array(predictions), columns=['0.25','0.75'])
            data['top45'] = LOTS_SIZES['ticker']
            predictions = torch.Tensor(np.array(data[~data['top45'].isin(filter)][['0.25','0.75']]))

            filtered_data_cur_timepoint = data_cur_timepoint[['ticker', 'open']][~data_cur_timepoint['ticker'].isin(filter)]
            cur_ticker_open_prices = list(filtered_data_cur_timepoint.itertuples(index=False))
            tickers = data_cur_timepoint['ticker'][~data_cur_timepoint['ticker'].isin(filter)]
            ticker_indexes = [self.algotrader.tickers_numbers[i] for i in tickers]
            self.algotrader.timer_tic(time=datetime.datetime.utcfromtimestamp(timepoint.tolist()/1e9), cur_ticker_open_prices=cur_ticker_open_prices, predictions=predictions, ticker_indexes= ticker_indexes)
            self.backtest_results.loc[len(self.backtest_results.index)] = [timepoint, self.algotrader.total_money, self.algotrader.cash]
            self.algotrader.update_total_money()
        return self.backtest_results

    def timer_tic(self, new_data, prices):
        predictions, date = self.predictor.predict(new_data)
        lot_prices = prices * self.lot_sizes
        predictions_lots = predictions * self.lot_sizes
        self.algotrader.timer_tic(date, lot_prices, predictions_lots)
        


    
class Algotrader:
    def __init__(self, cash, lot_prices, dispatcher, comission=1e-5, timeout=10):
        self.cash = cash
        self.total_money = cash
        self.volumes = np.zeros(len(lot_prices))
        self.lot_prices = lot_prices
        self.comission = comission
        self.timeout = timeout
        self.buy_try_number = -1
        self.requests_prices = {}
        self.volumes_to_buy = {}
        self.volumes_to_sell = {}
        self.expected_income = []
        self.strategy_actions = []
        #self.strategy_types = Enum('Action', ['BUY','SELL','HOLD']) 
        self.buy_request_ids = {}
        self.sell_request_ids = {}
        self.sell_requests_list = []
        self.tickers_numbers = TOP45_DICT
        # Режим быстрой торговли даёт более выгодные цены, чтобы сделки быстрее закрывались
        self.fast_mode = False
        self.fast_coef = 0.5
        self.dispatcher = dispatcher
        self.opening_time = datetime.timedelta(hours=10)
        self.closing_time = datetime.timedelta(hours=18, minutes=45)
        self.opening_delta = datetime.timedelta(minutes=30)
        self.closing_delta = datetime.timedelta(minutes=15)
        self.min_relative_income = []
        self.max_relative_income = []
    
    def update_prices(self, cur_ticker_open_prices):
        for t, p in cur_ticker_open_prices:
            n = self.tickers_numbers[t]
            self.lot_prices[n] = p * self.dispatcher.lot_sizes[n]


    def update_total_money(self, cur_ticker_open_prices=None):
        if cur_ticker_open_prices:
            self.update_prices(cur_ticker_open_prices)
        self.total_money = self.cash + (sum(self.volumes * self.lot_prices))
        
    def update_strategy(self, predictions, cur_ticker_open_prices, ticker_indexes):
        self.requests_prices = {}
        self.volumes_to_buy = {}
        self.expected_income = []
        self.min_relative_income = []
        self.max_relative_income = []
        # for i in range(len(predictions)):
        convert_dict = {i: ind for ind, i in enumerate(ticker_indexes)}
        for t, p in cur_ticker_open_prices:
            i = self.tickers_numbers[t]
            i1 = convert_dict[i]
            # состовляем предложения о продаже. Для начала продаём только те акции, которые выгодно продавать сами по себе
            # в дальнейшем добавим продажу акций, чтобы получить деньги для покупки других, более выгодных
            # затем уже добавим фьючерсные сделки
            if self.volumes[i] > 0: # пока у нас нет фьючерсных сделок 
                if predictions[i1][1] < self.lot_prices[i] * (1 - self.comission):
                    price = self.calc_sell_price(self.lot_prices[i], predictions[i1][1])
                    volume_to_sell = min(self.volumes[i], (0.5 * self.total_money) // (price - predictions[i1][1]))
                    request_id = self.dispatcher.request_buy_or_sell(i, volume_to_sell, price, buy=False, callback=self.sold)
                    self.sell_request_ids[i] = request_id
                else:
                    self.max_relative_income.append((i,(predictions[i1][1] - self.lot_prices[i] / self.lot_prices[i])))
            # состовляем предложения о покупке
            if predictions[i1][0] > self.lot_prices[i] * (1 + self.comission):
                price = self.calc_buy_price(self.lot_prices[i], predictions[i1][0])
                can_buy = self.cash // price
                volume_to_buy = min(can_buy, (0.5 * self.total_money) // (predictions[i1][0] - price))
                if volume_to_buy > 0:
                    self.requests_prices[i] = price
                    self.volumes_to_buy[i] = volume_to_buy
                    self.expected_income.append((i, self.volumes_to_buy[i] * (predictions[i1][0] - price)))
                    self.min_relative_income.append((i,(predictions[i1][0] - self.lot_prices[i] * (1 + self.comission)) / self.lot_prices[i]))
            
    
        if len(self.expected_income) > 0:
            self.expected_income = sorted(self.expected_income, key= lambda x: x[1], reverse=True)
            self.min_relative_income = sorted(self.min_relative_income, key= lambda x: x[1], reverse=True)
            # Отсортирован по возростанию в отличии от остальных
            self.max_relative_income = sorted(self.max_relative_income, key= lambda x: x[1], reverse=False)
            instrument = self.expected_income[0][0]
            self.buy_try_number = 0
            
            if self.dispatcher.asynchroneous_mode:
                th.Timer(self.timeout, self.buy_timeout)
            buy_request_id = self.dispatcher.request_buy_or_sell(instrument, self.volumes_to_buy[instrument], self.requests_prices[instrument], buy=True, callback=self.bought)
            self.buy_request_ids[instrument] = buy_request_id
            for i, rel_income in self.max_relative_income:
                if self.volumes[i] > 0:
                    if rel_income  < self.min_relative_income[0][1] * (1 - 2 * self.comission):
                        sell_request_id = self.dispatcher.request_buy_or_sell(i, self.volumes_to_buy[i], self.requests_prices[i], buy=False, callback=self.sold)
                        self.sell_request_ids[i] = sell_request_id
                        if self.dispatcher.asynchroneous_mode:
                            th.Timer(self.timeout, lambda : self.sell_timeout(i))
            
            
            
            
    def sell_timeout(self, instrument):
        self.dispatcher.delete_request(self.sell_request_ids[instrument])
    
            
    def buy_timeout(self):
        self.buy_try_number += 1
        if self.buy_try_number >= len(self.expected_income):
            self.dispatcher.delete_request(self.buy_request_ids[self.expected_income[self.buy_try_number-1][0]])
            self.clear_buy_request_cashe()
            return
        instrument = self.expected_income[self.buy_try_number][0]
        self.dispatcher.delete_request(self.buy_request_ids[self.expected_income[self.buy_try_number-1][0]])
        buy_request_id = self.dispatcher.request_buy_or_sell(instrument, self.volumes_to_buy[instrument], self.requests_prices[instrument], buy=True, callback=self.bought)
        self.buy_request_ids[instrument] = buy_request_id
        
        
    def calc_sell_price(self, cur_price, prediction):
        if self.fast_mode:
            return ((cur_price * (1 - self.comission) * (1 - self.fast_coef)) + (prediction * self.fast_coef)) 
        return cur_price * (1 - self.comission)
        
        
    def clear_buy_request_cashe(self):
        self.requests_prices = {}
        self.volumes_to_buy = {}
        self.expected_income = []
        # self.strategy_actions.pop(-1)
        self.buy_request_ids = {}
        self.buy_try_number = -1
    
    
    def bought(self, instrument, volume, price):
        self.volumes[instrument] += volume
        self.cash -= volume * price
        self.update_total_money()
        self.clear_buy_request_cashe()
        
        
    def calc_buy_price(self, cur_price, prediction):
        if self.fast_mode:
            return ((cur_price * (1 + self.comission) * (1 - self.fast_coef)) + (prediction * self.fast_coef)) 
        return cur_price * (1 + self.comission)
    
    
    def timer_tic(self, time, cur_ticker_open_prices, predictions, ticker_indexes):
        self.current_time = time
        
        t = self.dispatcher.get_timedelta_today(time)
        if t < self.opening_time or t > self.closing_time:
            print('Биржа закрыта')
            return
        
        self.update_prices(cur_ticker_open_prices)
        
        if t - self.opening_time < self.opening_delta:
            if t - self.opening_delta < self.dispatcher.trading_delta:
                news_df = self.dispatcher.predictor.news_data
                plus_array = news_df.loc[(news_df['score']==3) & (news_df['date'] > (t-datetime.timedelta(hours=24)+self.closing_delta))][['ticker']].values()
                minus_array = news_df.loc[(news_df['score']==-3) & (news_df['date'] > (t-datetime.timedelta(hours=24)+self.closing_delta))][['ticker']].values()
                for t in minus_array:
                    i = self.tickers_numbers[t]
                    if self.volumes[i] > 0:
                        sell_request_id = self.dispatcher.request_buy_or_sell(i, self.volumes[i], self.requests_prices[i], buy=False, callback=self.sold)
                        self.sell_request_ids[i] = sell_request_id
                        if self.dispatcher.asynchroneous_mode:
                            th.Timer(self.timeout, lambda : self.sell_timeout(i))
                tickers_for_pred_dict = {t: ind for ind, t in enumerate(ticker_indexes)}
                
                self.clear_buy_request_cashe()
                
                for t in plus_array:
                    i = self.tickers_numbers[t]
                    i1 = tickers_for_pred_dict[t]
                    if predictions[i1][0] > self.lot_prices[i] * (1 + self.comission):
                        price = self.calc_buy_price(self.lot_prices[i], predictions[i1][0])
                        can_buy = self.cash // price
                        volume_to_buy = min(can_buy, (0.5 * self.total_money) // (predictions[i1][0] - price))
                        if volume_to_buy > 0:
                            self.requests_prices[i] = price
                            self.volumes_to_buy[i] = volume_to_buy
                            self.expected_income.append((i, self.volumes_to_buy[i] * (predictions[i1][0] - price)))
                            self.min_relative_income.append((i,(predictions[i1][0] - self.lot_prices[i] * (1 + self.comission)) / self.lot_prices[i]))
                            
                if len(self.expected_income) > 0:
                    self.expected_income = sorted(self.expected_income, key= lambda x: x[1], reverse=True)
                    self.min_relative_income = sorted(self.min_relative_income, key= lambda x: x[1], reverse=True)
                    # Отсортирован по возрастанию в отличие от остальных
                    self.max_relative_income = sorted(self.max_relative_income, key= lambda x: x[1], reverse=False)
                    instrument = self.expected_income[0][0]
                    self.buy_try_number = 0
            
                    if self.dispatcher.asynchroneous_mode:
                        th.Timer(self.timeout, self.buy_timeout)
                    buy_request_id = self.dispatcher.request_buy_or_sell(instrument, self.volumes_to_buy[instrument], self.requests_prices[instrument], buy=True, callback=self.bought)
                    self.buy_request_ids[instrument] = buy_request_id

                        
        elif self.closing_time - t < self.closing_delta: 
            self.clear_buy_request_cashe()
            print('Специальный режим перед закрытием биржи')
        else:
            self.update_strategy(predictions, cur_ticker_open_prices, ticker_indexes)
            print('total money', self.total_money)
            
    
    def sold(self, instrument, volume, price):
        self.volumes[instrument] -= volume
        self.cash += volume * price
        self.update_total_money()
