from backend.models.ollama_client import get_llm

llm = get_llm()


def fact_extractor(state):
    """
    Agent 2 — Extract all verifiable facts from each article.
    """
    articles = state["articles"]
    fact_results = []

    for article in articles:
        prompt = f"""
Extract the key verifiable facts from this news article. List only the most important facts — maximum 6.

Article URL: {article['url']}
Article Text:
{article['text'][:2000]}

Rules:
- Maximum 6 facts total.
- One sentence per fact.
- Facts only — no opinions or analysis.

Format exactly as:
Facts:
1. <fact>
2. <fact>
...
"""
        response = llm.invoke(prompt)
        fact_results.append({
            "url":   article["url"],
            "title": article["title"],
            "facts": str(response.content).strip()
        })

    return {
        **state,
        "fact_results": fact_results
    }








