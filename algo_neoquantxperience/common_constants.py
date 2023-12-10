import pandas as pd

TOP45 = ['AFKS', 'AFLT', 'AGRO', 'ALRS', 'CBOM', 'CHMF', 'ENPG', 'FEES',
       'FIVE', 'GAZP', 'GLTR', 'GMKN', 'HYDR', 'IRAO', 'LKOH', 'MAGN',
       'MGNT', 'MOEX', 'MTSS', 'NLMK', 'NVTK', 'OZON', 'PHOR', 'PIKK',
       'PLZL', 'POLY', 'POSI', 'QIWI', 'ROSN', 'RTKM', 'RUAL', 'SBER',
       'SBERP', 'SELG', 'SGZH', 'SNGS', 'SNGSP', 'TATN', 'TATNP', 'TCSG',
       'TRNFP', 'UPRO', 'VKCO', 'VTBR', 'YNDX']

IMOEX_FILTERED = ['AFKS', 'AFLT', 'AGRO', 'ALRS', 'CBOM', 'CHMF', 'ENPG', 'FEES',
       'FIVE', 'GAZP', 'GLTR', 'GMKN', 'HYDR', 'IRAO', 'LKOH', 'MAGN',
       'MGNT', 'MTSS', 'NLMK', 'NVTK', 'OZON', 'PHOR', 'PIKK',
       'PLZL', 'POLY', 'POSI', 'ROSN', 'RUAL', 'SELG', 'SNGS', 'TATN',
        'TATNP', 'TCSG', 'TRNFP', 'UPRO', 'VKCO', 'VTBR', 'YNDX']

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

TINKOFF_API_TICKERS = {'BBG004S68614': 'AFKS',
 'BBG004S683W7': 'AFLT',
 'BBG007N0Z367': 'AGRO',
 'BBG004S68B31': 'ALRS',
 'BBG009GSYN76': 'CBOM',
 'BBG00475K6C3': 'CHMF',
 'BBG000RMWQD4': 'ENPG',
 'BBG00475JZZ6': 'FEES',
 'BBG00JXPFBN0': 'FIVE',
 'BBG004730RP0': 'GAZP',
 'BBG000VFX6Y4': 'GLTR',
 'BBG004731489': 'GMKN',
 'BBG00475K2X9': 'HYDR',
 'BBG004S68473': 'IRAO',
 'BBG004731032': 'LKOH',
 'BBG004S68507': 'MAGN',
 'BBG004RVFCY3': 'MGNT',
 'BBG004730JJ5': 'MOEX',
 'BBG004S681W1': 'MTSS',
 'BBG004S681B4': 'NLMK',
 'BBG00475KKY8': 'NVTK',
 'BBG00Y91R9T3': 'OZON',
 'BBG004S689R0': 'PHOR',
 'BBG004S68BH6': 'PIKK',
 'BBG000R607Y3': 'PLZL',
 'BBG004PYF2N3': 'POLY',
 'TCS00A103X66': 'POSI',
 'BBG005D1WCQ1': 'QIWI',
 'BBG004731354': 'ROSN',
 'BBG004S682Z6': 'RTKM',
 'BBG008F2T3T2': 'RUAL',
 'BBG004730N88': 'SBER',
 'BBG0047315Y7': 'SBERP',
 'BBG002458LF8': 'SELG',
 'BBG0100R9963': 'SGZH',
 'BBG0047315D0': 'SNGS',
 'BBG004S681M2': 'SNGSP',
 'BBG004RVFFC0': 'TATN',
 'BBG004S68829': 'TATNP',
 'BBG00QPYJ5H0': 'TCSG',
 'BBG00475KHX6': 'TRNFP',
 'BBG004S686W0': 'UPRO',
 'TCS00A106YF0': 'VKCO',
 'BBG004730ZJ9': 'VTBR',
 'BBG006L8G4H1': 'YNDX'}


# LOTS_SIZES = pd.read_csv('datasets_for_algotrader/45tickers_metainfo.csv')
#
# CALENDAR_DATA = pd.read_parquet('datasets_for_algotrader/calendar.parquet')
#
# NEWS_DATA = pd.read_parquet('datasets_for_algotrader/sentiment_scores.parquet')
