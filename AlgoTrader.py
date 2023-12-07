from enum import Enum
import threading as th  
import numpy as np
import datetime


class Dispatcher:
    def __init__(self, config, tickers, cash, config_path, task_dir_path, ids_in_train, path_to_calendar, asynchroneous_mode=False, default_prices = None):
        self.config = config
        self.asynchroneous_mode = asynchroneous_mode
        self.tickers_len = len(tickers)
        self.default_prices = default_prices
        # Тут должны создаваться стратегии и получаться начальные цены
        # Список начальных цен записывается в cur_prices
        if default_prices == None:
            cur_prices = torch.zeros(self.tickers_len)
        else:
            cur_prices = self.default_prices
        self.algotrader = Algotrader(cash, cur_prices, range(self.tickers_len), self, comission=1e-5, timeout=10)
        self.predictor = DDDF_predictor(config_path, task_dir_path, ids_in_train, path_to_calendar)
    
    def predict(self, raw_data, ids_in_train):
        return predict(raw_data, config, ids_in_train)
    
    
    def request_buy_or_sell(self, instrument, volume, price, buy=True, callback=None):
        request_number = round(torch.rand(1).item() * 1000)
        print("instrument:",instrument)
        print("volume:",volume)
        print("price:",price)
        if callback:
            callback(instrument, volume, price)
        return request_number
    
    def delete_request(self,buy_request_id):
        print("buy_request_id:",buy_request_id)
        
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
            
    def timer_tic(self, time, price):
        


    
class Algotrader:
    def __init__(self, cash, cur_prices, tickers, dispatcher, comission=1e-5, timeout=10):
        self.cash = cash
        self.total_money = cash
        self.volumes = np.zeros(len(cur_prices))
        self.current_prices = cur_prices
        self.comission = comission
        self.timeout = timeout
        self.buy_try_number = -1
        self.requests_prices = {}
        self.volumes_to_buy = {}
        self.volumes_to_sell = {}
        self.expected_income = []
        self.strategy_actions = []
        self.strategy_types = Enum('Action', ['BUY','SELL','HOLD']) 
        self.buy_request_ids = {}
        self.sell_requests_list = []
        self.tickers = tickers
        # Режим быстрой торговли даёт более выгодные цены, чтобы сделки быстрее закрывались
        self.fast_mode = False
        self.fast_coef = 0.5
        self.dispatcher = dispatcher
        self.opening_time = datetime.timedelta(hours=10)
        self.closing_time = datetime.timedelta(hours=18, minutes=45)
        self.opening_delta = datetime.timedelta(minutes=30)
        self.closing_delta = datetime.timedelta(minutes=15)
        
    
    def update_prices(self, cur_prices):
        self.current_prices = np.array(cur_prices)
        

    def update_total_money(self, cur_prices=None):
        if cur_prices:
            self.update_prices(cur_prices)
        self.total_money = self.cash + (sum(self.volumes * self.current_prices))
        
    def update_strategy(self, predictions):
        self.requests_prices = {}
        self.volumes_to_buy = {}
        self.expected_income = []
        for i in range(len(predictions)):
            
            # состовляем предложения о продаже. Для начала продаём только те акции, которые выгодно продавать сами по себе
            # в дальнейшем добавим продажу акций, чтобы получить деньги для покупки других, более выгодных
            # затем уже добавим фьючерсные сделки
            if self.volumes[i] > 0: # пока у нас нет фьючерсных сделок 
                if predictions[i][1] < self.current_prices[i] * (1 - self.comission):
                    price = self.calc_sell_price(self.current_prices[i], predictions[i][1])
                    volume_to_sell = min(self.volumes[i], (0.5 * self.total_money) // (price - predictions[i][1]))
                    request_id = dispatcher.request_buy_or_sell(self.tickers[i], volume_to_sell, price, buy=False, callback=self.sold)
                    self.sell_requests_list.append(request_id)
                    
            # состовляем предложения о покупке
            if predictions[i][0] > self.current_prices[i] * (1 + self.comission):
                price = self.calc_buy_price(self.current_prices[i], predictions[i][0])
                can_buy = self.cash // price
                volume_to_buy =  min(can_buy, (0.5 * self.total_money) // (predictions[i][0] - price))
                if volume_to_buy > 0:
                    self.requests_prices[i] = price
                    self.volumes_to_buy[i] = volume_to_buy
                    self.expected_income.append((i, self.volumes_to_buy[i] * (predictions[i][0] - price)))

        if len(self.expected_income) > 0:
            self.expected_income = sorted(self.expected_income, key= lambda x: x[1], reverse=True)
            instrument = self.expected_income[0][0]
            self.buy_try_number = 0
            # self.strategy_actions.append(self.stategy_types.BUY, self.timeout)
            if self.dispatcher.asynchroneous_mode:
                th.Timer(self.timeout, self.buy_timeout)
            buy_request_id = dispatcher.request_buy_or_sell(self.tickers[instrument], self.volumes_to_buy[instrument], self.requests_prices[instrument], buy=True, callback=self.bought)
            self.buy_request_ids[instrument] = buy_request_id
        
        
    def buy_timeout(self):
        self.buy_try_number += 1
        if self.buy_try_number >= len(self.expected_income):
            delete_buy_request(self.buy_request_ids[self.expected_income[self.buy_try_number-1][0]])
            self.clear_buy_request_cashe()
            return
        instrument = self.expected_income[self.buy_try_number][0]
        delete_buy_request(self.buy_request_ids[self.expected_income[self.buy_try_number-1][0]])
        buy_request_id = dispatcher.request_buy_or_sell(self.tickers[instrument], self.volumes_to_buy[instrument], self.requests_prices[instrument], buy=True, callback=self.bought)
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
    
    
    def timer_tic(self, time, prices_list, prediction):
        self.current_time = time
        
        t = self.dispatcher.get_timedelta_today(time)
        if t < self.opening_time or t > self.closing_time:
            print('Биржа закрыта')
            return
        
        self.update_prices(prices_list)
        
        if t - self.opening_time < self.opening_delta:
            print('Специальный режим сразу после открытия биржи')
        elif self.closing_time - t < self.closing_delta: 
            print('Специальный режим перед закрытием биржи')
        else:
            self.update_strategy(prediction)
            print('total money', self.total_money)
            
            
    
    
    
    def sold(self, instrument, volume, price):
        self.volumes[instrument] -= volume
        self.cash += volume * price
        self.update_total_money()
