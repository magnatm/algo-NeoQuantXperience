import traceback
from algo_neoquantxperience.nlp.chain import score_chain
from algo_neoquantxperience.nlp.structs import News, TickerNewsMap


def get_ticker_news_map_with_scores(
    ticker_news_map: TickerNewsMap,
) -> TickerNewsMap:
    """Set scores that the LLM returned.
    If the score has already been set, do not change it so as not to call the model once again.
    """
    ticker_news_map_with_scores = {}
    for ticker, newses in ticker_news_map.items():
        print(f"Ticker {ticker}...")
        newses_with_scores = []
        for news in newses:
            try:
                score = float(
                    score_chain.invoke({"ticker": ticker, "news_content": news.text})
                    if news.score is None
                    else news.score
                )
            except ValueError as e:
                print(f"An exception occured: {e}")
                traceback.print_exc()
                print("Probably because of the invalid output of the LLM, set score to zero.")
                score = 0
            newses_with_scores.append(
                News(datetime=news.datetime, text=news.text, score=int(score))
            )
        ticker_news_map_with_scores[ticker] = newses_with_scores
    return ticker_news_map_with_scores
