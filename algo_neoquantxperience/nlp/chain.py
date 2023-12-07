from dotenv import load_dotenv
from langchain.llms import GigaChat
from langchain.prompts import PromptTemplate

load_dotenv()

score_template = """Ты трейдер фондовой биржы. Оцени новость по шкале от -3 до 3 по степени благоприятности для покупки акций {ticker}. Чем выше оценка, тем более благоприятны условия для покупки акций.
Ответь числом, не добавляй деталей.

Новость:
{news_content}
Оценка:
"""
score_prompt_template = PromptTemplate.from_template(score_template)
llm = GigaChat(verify_ssl_certs=False, temperature=1e-6)
score_chain = score_prompt_template | llm
