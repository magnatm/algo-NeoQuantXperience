import os

from dotenv import load_dotenv

load_dotenv()
# Remember to use your own values from my.telegram.org!
TG_API_ID = int(os.environ["TG_API_ID"])
TG_API_HASH = os.environ["TG_API_HASH"]
