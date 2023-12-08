from tinkoff.invest.services import InstrumentsService, InstrumentStatus
from tinkoff.invest import Client
from settings import Settings

"""
Создание словаря как в settings.ticker_figi
"""

list_tickers = ['AFKS', 'AFLT', 'AGRO', 'ALRS', 'CBOM', 'CHMF', 'ENPG', 'FEES',
       'FIVE', 'GAZP', 'GLTR', 'GMKN', 'HYDR', 'IRAO', 'LKOH', 'MAGN',
       'MGNT', 'MOEX', 'MTSS', 'NLMK', 'NVTK', 'OZON', 'PHOR', 'PIKK',
       'PLZL', 'POLY', 'POSI', 'QIWI', 'ROSN', 'RTKM', 'RUAL', 'SBER',
       'SBERP', 'SELG', 'SGZH', 'SNGS', 'SNGSP', 'TATN', 'TATNP', 'TCSG',
       'TRNFP', 'UPRO', 'VKCO', 'VTBR', 'YNDX']
dict_share_figi = dict()

with Client(Settings().token) as cl:
       instruments: InstrumentsService = cl.instruments
       r = instruments.shares(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_ALL)
       all_shares = [share.__dict__ for share in r.instruments]
       for share in all_shares:
              if share['figi'].startswith('BBG') or (share['exchange'] == 'MOEX_EVENING_WEEKEND'):
                     dict_share_figi[share['ticker']] = share['figi']

dict_45_ticker_figi = {ticker: dict_share_figi[ticker] for ticker in list_tickers}
print(dict_45_ticker_figi)

