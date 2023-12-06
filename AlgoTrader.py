from enum import Enum
import threading as th  


class Algotrader:
    def __init__(self, cash, cur_prices, tickers, comission=0, timeout=10):
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
                self.expected_income.append((i, volumes_to_buy[i] * (predictions[i][0] - price)))
        self.expected_income = sorted(self.expected_income, key= lambda x: x[1], reverse=True)
        instrument = self.expected_income[0][0]
        self.buy_try_number = 0
        # self.strategy_actions.append(self.stategy_types.BUY, self.timeout)
        th.Timer(self.timeout, self.buy_timeout)
        buy_request_id = request_to_buy(self.tickers[instrument], self.volumes_to_buy[instrument], self.requests_prices[instrument], self.bought)
        self.buy_request_ids[instrument] = buy_request_id
        
        
    def buy_timeout(self):
        self.buy_try_number += 1
        if self.buy_try_number >= len(self.expected_income):
            delete_buy_request(self.buy_request_ids[self.expected_income[self.buy_try_number-1][0]])
            self.clear_buy_request_cashe()
            return
        instrument = self.expected_income[self.buy_try_number][0]
        delete_buy_request(self.buy_request_ids[self.expected_income[self.buy_try_number-1][0]])
        buy_request_id = request_to_buy(self.tickers[instrument], self.volumes_to_buy[instrument], self.requests_prices[instrument], self.bought)
        self.buy_request_ids[instrument] = buy_request_id
        
    def clear_buy_request_cashe(self):
        self.requests_prices = {}
        self.volumes_to_buy = {}
        self.expected_income = []
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