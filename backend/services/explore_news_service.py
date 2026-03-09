from backend.tools.search_tool import search_news


def explore_news(topic):

    results = search_news(topic)

    news = []

    for r in results:

        news.append({
            "title": r["title"],
            "url": r["url"]
        })

    return news