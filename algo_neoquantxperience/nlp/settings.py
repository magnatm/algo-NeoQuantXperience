import os

from dotenv import load_dotenv

load_dotenv()
# Remember to use your own values from my.telegram.org!
TG_API_ID = int(os.environ["TG_API_ID"])
TG_API_HASH = os.environ["TG_API_HASH"]

TOP45 = [
    "AFKS",
    "AFLT",
    "AGRO",
    "ALRS",
    "CBOM",
    "CHMF",
    "ENPG",
    "FEES",
    "FIVE",
    "GAZP",
    "GLTR",
    "GMKN",
    "HYDR",
    "IRAO",
    "LKOH",
    "MAGN",
    "MGNT",
    "MOEX",
    "MTSS",
    "NLMK",
    "NVTK",
    "OZON",
    "PHOR",
    "PIKK",
    "PLZL",
    "POLY",
    "POSI",
    "QIWI",
    "ROSN",
    "RTKM",
    "RUAL",
    "SBER",
    "SBERP",
    "SELG",
    "SGZH",
    "SNGS",
    "SNGSP",
    "TATN",
    "TATNP",
    "TCSG",
    "TRNFP",
    "UPRO",
    "VKCO",
    "VTBR",
    "YNDX",
]
