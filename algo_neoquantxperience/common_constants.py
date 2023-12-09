import pandas as pd

TOP45 = ['AFKS', 'AFLT', 'AGRO', 'ALRS', 'CBOM', 'CHMF', 'ENPG', 'FEES',
       'FIVE', 'GAZP', 'GLTR', 'GMKN', 'HYDR', 'IRAO', 'LKOH', 'MAGN',
       'MGNT', 'MOEX', 'MTSS', 'NLMK', 'NVTK', 'OZON', 'PHOR', 'PIKK',
       'PLZL', 'POLY', 'POSI', 'QIWI', 'ROSN', 'RTKM', 'RUAL', 'SBER',
       'SBERP', 'SELG', 'SGZH', 'SNGS', 'SNGSP', 'TATN', 'TATNP', 'TCSG',
       'TRNFP', 'UPRO', 'VKCO', 'VTBR', 'YNDX']

TOP45_DICT = {'AFKS': 0, 'AFLT': 1, 'AGRO': 2, 'ALRS': 3, 'CBOM': 4, 'CHMF': 5,
              'ENPG': 6, 'FEES': 7, 'FIVE': 8, 'GAZP': 9, 'GLTR': 10, 'GMKN': 11,
              'HYDR': 12, 'IRAO': 13, 'LKOH': 14, 'MAGN': 15, 'MGNT': 16, 'MOEX': 17,
              'MTSS': 18, 'NLMK': 19, 'NVTK': 20, 'OZON': 21, 'PHOR': 22, 'PIKK': 23,
              'PLZL': 24, 'POLY': 25, 'POSI': 26, 'QIWI': 27, 'ROSN': 28, 'RTKM': 29,
              'RUAL': 30, 'SBER': 31, 'SBERP': 32, 'SELG': 33, 'SGZH': 34, 'SNGS': 35,
              'SNGSP': 36, 'TATN': 37, 'TATNP': 38, 'TCSG': 39, 'TRNFP': 40, 'UPRO': 41,
              'VKCO': 42, 'VTBR': 43, 'YNDX': 44}

TICKER_TO_BRANCH_INDEX = {
    "AFKS": "MOEXBMI", "AFLT": "MOEXTN", "AGRO": "MOEXCN", "ALRS": "MOEXMM", "CBOM": "MOEXFN",
    "CHMF": "MOEXMM", "ENPG": "MOEXMM", "FEES": "MOEXEU", "FIVE": "MOEXCN", "GAZP": "MOEXOG",
    "GLTR": "MOEXTN", "GMKN": "MOEXMM", "HYDR": "MOEXEU", "IRAO": "MOEXEU", "LKOH": "MOEXOG",
    "MAGN": "MOEXMM", "MGNT": "MOEXCN", "MOEX": "MOEXFN", "MTSS": "MOEXTL", "NLMK": "MOEXMM",
    "NVTK": "MOEXOG", "OZON": "IMOEX", "PHOR": "MOEXCH", "PIKK": "IMOEX", "PLZL": "MOEXMM",
    "POLY": "MOEXMM", "POSI": "IMOEX", "QIWI": "MOEXFN", "ROSN": "MOEXOG", "RTKM": "MOEXTL",
    "RUAL": "MOEXMM", "SBER": "MOEXFN", "SBERP": "MOEXFN", "SELG": "MOEXMM", "SGZH": "MOEXBMI",
    "SNGS": "MOEXOG", "SNGSP": "MOEXOG", "TATN": "MOEXOG", "TATNP": "MOEXOG", "TCSG": "MOEXFN",
    "TRNFP": "MOEXOG", "UPRO": "MOEXEU", "VKCO": "IMOEX", "VTBR": "MOEXFN", "YNDX": "IMOEX"}

ALGOPACK_AVAILABLE_INDEXES = {'MOEXBMI': 'Индекс широкого рынка',
                              'MOEXCH': 'Индекс химии и нефтехимии',
                              'MOEXCN': 'Индекс потребительского сектора',
                              'MOEXEU': 'Индекс электроэнергетики',
                              'MOEXFN': 'Индекс финансов',
                              'MOEXMM': 'Индекс металлов и добычи',
                              'MOEXOG': 'Индекс нефти и газа',
                              'MOEXTL': 'Индекс телекоммуникаций',
                              'MOEXTN': 'Индекс транспорта',
                              'IMOEX': 'Индекс МосБиржи'}

LOTS_SIZES = pd.read_csv('datasets_for_algotrader/45tickers_metainfo.csv')

CALENDAR_DATA = pd.read_parquet('datasets_for_algotrader/calendar.parquet')

NEWS_DATA = pd.read_parquet('datasets_for_algotrader/sentiment_scores.parquet')
