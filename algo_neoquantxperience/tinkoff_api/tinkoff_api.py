"""
Основной класс для работы с запросами на покупку/продажу позиций через брокера "Тинькофф банк", использую его API
"""
import uuid
from settings import Settings
from tinkoff.invest import Client, MoneyValue, OrderDirection, OrderType
from tinkoff.invest.sandbox.client import SandboxClient
from tinkoff.invest.services import Services


SETTINGS = Settings()


def decorator_create_client(func):
    def executer_func(self, **kwargs):
        with Client(SETTINGS.token) as client:
            arguments = kwargs
            arguments.update({'client': client})
            return_value = func(self, **kwargs)
        return return_value
    return executer_func


def decorator_create_sandbox_client(func):
    def executer_func(self, **kwargs):
        with SandboxClient(SETTINGS.sandbox_token) as sb_client:
            arguments = kwargs
            arguments.update({'client': sb_client})
            return_value = func(self, **kwargs)
        return return_value
    return executer_func


class BaseTraderTinkoff:
    def get_account_id(self, client: Services) -> str:
        """
        Метод получения идентификатора счёта пользователя
        :param client:
        :return:
        """
        return [acc.id for acc in client.users.get_accounts().accounts][0]

    def get_portfolio(self, client: Services, account_id: str) -> dict:
        """
        Метод получения общей информации по счету:
          - total_amount_shares - Общая стоимость акций в портфеле.
          - total_amount_bonds - Общая стоимость облигаций в портфеле.
          - total_amount_etf - Общая стоимость фондов в портфеле.
          - total_amount_currencies - Общая стоимость валют в портфеле.
          - total_amount_futures - Общая стоимость фьючерсов в портфеле.
          - expected_yield - Текущая относительная доходность портфеля, в %.
          - positions - Список позиций портфеля.
          - account_id - Идентификатор счёта пользователя.
          - total_amount_options - Общая стоимость опционов в портфеле.
          - total_amount_sp - Общая стоимость структурных нот в портфеле.
          - total_amount_portfolio - Общая стоимость портфеля.
          - virtual_positions - Массив виртуальных позиций портфеля.
        :param client:
        :param account_id: Идентификатор счёта пользователя
        :return: Словарь с информацией по счету
        """
        return client.operations.get_portfolio(account_id=account_id).__dict__

    def _post_reauest(self, client: Services, ticker: str,
                      quantity: int, direction: OrderDirection, order_type: OrderType = OrderType.ORDER_TYPE_MARKET) -> None:
        """
        Основной запрос, который используется в покупке и продаже, отличающийся только direction
        :param client:
        :param ticker:
        :param quantity:
        :param direction:
        :param order_type: Тип заявки:
                                - ORDER_TYPE_UNSPECIFIED - 0 - Значение не указано
                                - ORDER_TYPE_LIMIT - 1 - Лимитная
                                - ORDER_TYPE_MARKET - 2 - Рыночная (Установлена по дефолту)
                                - ORDER_TYPE_BESTPRICE - 3 - Лучшая цена
        :return:
        """
        figi = SETTINGS.ticker_figi.get(ticker, ticker)
        account_id = self.get_account_id(client=client)
        client.orders.post_order(
            figi=figi,
            quantity=quantity,
            account_id=account_id,
            order_id=uuid.uuid4().__str__(),
            direction=direction,
            order_type=order_type

        )

    def post_buy(self, client: Services, ticker: str,quantity: int) -> None:
        """
        Функция для обработки запроса на покупку актива по тикеру
        :param client:
        :param ticker:
        :param quantity:
        :param order_type: ORDER_TYPE_MARKET - 2 - Рыночная (Установлена по дефолту)
        :return:
        """
        self._post_reauest(client=client,
                           ticker=ticker,
                           quantity=quantity,
                           direction=OrderDirection.ORDER_DIRECTION_BUY,
                           order_type=OrderType.ORDER_TYPE_MARKET)

    def post_sell(self, client: Services, ticker: str,quantity: int) -> None:
        """
        Функция для обработки запроса на продажу актива по тикеру
        :param client:
        :param ticker:
        :param quantity:
        :param order_type: ORDER_TYPE_MARKET - 2 - Рыночная (Установлена по дефолту)
        :return:
        """
        self._post_reauest(client=client,
                           ticker=ticker,
                           quantity=quantity,
                           direction=OrderDirection.ORDER_DIRECTION_SELL,
                           order_type=OrderType.ORDER_TYPE_MARKET)


class SandboxTraderTinkoff:

    def __init__(self):
        self.btt = BaseTraderTinkoff()

    def create_amount_to_payin(self, units: int, nano: int, currency: str) -> MoneyValue:
        """
        Функция создания значения для пополнения счета
        :param units: Целое значение, которое обозначает, например, рубли
        :param nano: Целое значение, которое обозначает, например, копейки. Nano меет вид 1 копейка = 10_000_000
        :param currency: Строковое обозначение валюты: rub, usd, ...
        :return:
        """
        nano = nano * 10_000_000
        return MoneyValue(units=units, nano=nano, currency=currency)

    @decorator_create_sandbox_client
    def payin_sandbox(self, client: Services, amount: MoneyValue) -> MoneyValue:
        """
        Метод пополнения счёта в песочнице.
        :return: Текущий баланс счёта
        """
        naccount_id = self.btt.get_account_id(client=client)
        return client.sandbox.sadbox_pay_in(account_id=account_id, amount=amount)

    @decorator_create_sandbox_client
    def buy(self, client: Services, ticker: str, quantity: int):
        self.btt.post_buy(client=client, ticker=ticker,quantity=quantity)

    @decorator_create_sandbox_client
    def sell(self, client: Services, ticker: str, quantity: int):
        self.btt.post_sell(client=client, ticker=ticker,quantity=quantity)

    @decorator_create_sandbox_client
    def portfolio(self, client: Services) -> dict:
        account_id = self.btt.get_account_id(client=client)
        return self.btt.get_portfolio(client=client, account_id=account_id)


class RealTraderTinkoff:
    def __init__(self):
        self.btt = BaseTraderTinkoff()

    @decorator_create_client
    def buy(self, client: Services, ticker: str, quantity: int):
        self.btt.post_buy(client=client, ticker=ticker,quantity=quantity)

    @decorator_create_client
    def sell(self, client: Services, ticker: str, quantity: int):
        self.btt.post_sell(client=client, ticker=ticker,quantity=quantity)

    @decorator_create_client
    def portfolio(self, client: Services) -> dict:
        account_id = self.btt.get_account_id(client=client)
        return self.btt.get_portfolio(client=client, account_id=account_id)


# EXAMPLE
# if __name__ == '__main__':
#     sbtt = SandboxTraderTinkoff()
#     #rtt = RealyTraderTinkoff()
#     #rtt.buy(ticker='AFLT', quantity=1)
#     #for pos in rtt.portfolio().get('positions'):
#     #    print(pos.figi, pos.quantity.units)
#
#     for pos in sbtt.portfolio().get('positions'):
#         print(pos.figi, pos.quantity.units)
#
#     # amount = sbtt.create_amount_to_payin(units=100_000, nano=90_000_000, currency='rub')
#     # sbtt.payin_sandbox(amount=amount)
#
#     for pos in sbtt.portfolio().get('positions'):
#         print(pos.figi, pos.quantity.units)
#         if 'RUB' not in pos.figi:
#             sbtt.sell(ticker=pos.figi, quantity=1)
#
#     for pos in sbtt.portfolio().get('positions'):
#        print(pos.figi, pos.quantity.units)
