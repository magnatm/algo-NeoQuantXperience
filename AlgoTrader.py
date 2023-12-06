from enum import Enum
import threading as th  
import numpy as np
import datetime

# Эту функцию стратегии вызываем мы
def request_buy_or_sell(instrument, volume, price, buy=True, callback=None):
    request_number = 132
    print("instrument:",instrument)
    print("volume:",volume)
    print("price:",price)
    if callback:
        callback(instrument, volume, price)
    return request_number

# Эту функцию у стратегии вызываем только в асинхронном режиме
def delete_request(buy_request_id):
    print("buy_request_id:",buy_request_id)


class Algotrader:
    def __init__(self, cash, cur_prices, tickers, model, comission=0, timeout=10):
        self.cash = cash
        self.total_money = cash
        self.volumes = np.zeros(len(cur_prices))
        self.current_prices = cur_prices
        self.comission = comission
        self.timeout = timeout
        self.buy_try_number = -1
        self.requests_prices = {}
        self.volumes_to_buy = {}
        self.expected_income = []
        self.strategy_actions = []
        self.strategy_types = Enum('Action', ['BUY','SELL','HOLD']) 
        self.buy_request_ids = {}
        self.tickers = tickers
        # Режим быстрой торговли даёт более выгодные цены, чтобы сделки быстрее закрывались
        self.fast_mode = False
        self.fast_coef = 0.5
        self.model = model
        self.opening_time = datetime.timedelta(hours=10)
        self.closing_time = datetime.timedelta(hours=18, minutes=45)
        self.opening_delta = datetime.timedelta(minutes=30)
        self.closing_delta = datetime.timedelta(minutes=15)
        
    
    def update_prices(self, cur_prices):
        self.current_prices = cur_prices
        

    def update_total_money(self, cur_prices=None):
        if cur_prices:
            self.update_prices(cur_prices)
        self.total_money = self.cash + (sum(self.volumes * self.current_prices))
        
    def update_strategy(self, predictions):
        self.requests_prices = {}
        self.volumes_to_buy = {}
        self.expected_income = []
        for i in range(len(predictions)):
            # состовляем предложения о покупке
            if predictions[i][0] > self.current_prices[i] * (1 + self.comission):
                price = self.calc_buy_price(self.current_prices[i], predictions[i][0])
                self.requests_prices[i] = price
                can_buy = self.cash // price
                self.volumes_to_buy[i] = min(can_buy, (0.5 * self.total_money) / (predictions[i][0] - price))
                self.expected_income.append((i, self.volumes_to_buy[i] * (predictions[i][0] - price)))
        self.expected_income = sorted(self.expected_income, key= lambda x: x[1], reverse=True)
        instrument = self.expected_income[0][0]
        self.buy_try_number = 0
        # self.strategy_actions.append(self.stategy_types.BUY, self.timeout)
        th.Timer(self.timeout, self.buy_timeout)
        buy_request_id = request_buy_or_sell(self.tickers[instrument], self.volumes_to_buy[instrument], self.requests_prices[instrument], self.bought)
        self.buy_request_ids[instrument] = buy_request_id
        
        
    def buy_timeout(self):
        self.buy_try_number += 1
        if self.buy_try_number >= len(self.expected_income):
            delete_buy_request(self.buy_request_ids[self.expected_income[self.buy_try_number-1][0]])
            self.clear_buy_request_cashe()
            return
        instrument = self.expected_income[self.buy_try_number][0]
        delete_buy_request(self.buy_request_ids[self.expected_income[self.buy_try_number-1][0]])
        buy_request_id = request_buy_or_sell(self.tickers[instrument], self.volumes_to_buy[instrument], self.requests_prices[instrument], self.bought)
        self.buy_request_ids[instrument] = buy_request_id
        
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
    
    
    # Эту функцию вызывает стратегия
    def timer_tic(self, time, prices_list):
        self.current_time = time
        self.update_prices(prices_list)
        t = self.get_timedelta_today(time)
        if t - self.opening_time < self.opening_delta:
            pass
        elif self.closing_time - t < self.closing_delta: 
            pass
        else:
            prediction = self.model.predict(prices_list)
            self.update_strategy(prediction)
            
            
    def get_timedelta_today(self, date_time):
        midnight = date_time.copy()
        midnight.hours = 0
        midnight.minutes = 0
        midnight.seconds = 0
        return date_time - midnight