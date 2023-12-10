import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    token: str = "os.getenv('TINKOFF_TOKEN')"
    sandbox_token: str = "os.getenv('TINKOFF_SANDBOX_TOKEN')"
    ticker_figi: dict[str, str] = {'AFKS': 'BBG004S68614', 'AFLT': 'BBG004S683W7',
                                   'AGRO': 'BBG007N0Z367', 'ALRS': 'BBG004S68B31',
                                   'CBOM': 'BBG009GSYN76', 'CHMF': 'BBG00475K6C3',
                                   'ENPG': 'BBG000RMWQD4', 'FEES': 'BBG00475JZZ6',
                                   'FIVE': 'BBG00JXPFBN0', 'GAZP': 'BBG004730RP0',
                                   'GLTR': 'BBG000VFX6Y4', 'GMKN': 'BBG004731489',
                                   'HYDR': 'BBG00475K2X9', 'IRAO': 'BBG004S68473',
                                   'LKOH': 'BBG004731032', 'MAGN': 'BBG004S68507',
                                   'MGNT': 'BBG004RVFCY3', 'MOEX': 'BBG004730JJ5',
                                   'MTSS': 'BBG004S681W1', 'NLMK': 'BBG004S681B4',
                                   'NVTK': 'BBG00475KKY8', 'OZON': 'BBG00Y91R9T3',
                                   'PHOR': 'BBG004S689R0', 'PIKK': 'BBG004S68BH6',
                                   'PLZL': 'BBG000R607Y3', 'POLY': 'BBG004PYF2N3',
                                   'POSI': 'TCS00A103X66', 'QIWI': 'BBG005D1WCQ1',
                                   'ROSN': 'BBG004731354', 'RTKM': 'BBG004S682Z6',
                                   'RUAL': 'BBG008F2T3T2', 'SBER': 'BBG004730N88',
                                   'SBERP': 'BBG0047315Y7', 'SELG': 'BBG002458LF8',
                                   'SGZH': 'BBG0100R9963', 'SNGS': 'BBG0047315D0',
                                   'SNGSP': 'BBG004S681M2', 'TATN': 'BBG004RVFFC0',
                                   'TATNP': 'BBG004S68829', 'TCSG': 'BBG00QPYJ5H0',
                                   'TRNFP': 'BBG00475KHX6', 'UPRO': 'BBG004S686W0',
                                   'VKCO': 'TCS00A106YF0', 'VTBR': 'BBG004730ZJ9',
                                   'YNDX': 'BBG006L8G4H1'}

