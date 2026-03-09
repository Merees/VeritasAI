from backend.models.ollama_client import get_llm

llm = get_llm()


def framing_extractor(state):
    """
    Agent 1 — For each article, analyse framing, tone, and language choice.
    """
    articles = state["articles"]  # list of {url, text, title}
    framing_results = []

    for article in articles:
        prompt = f"""
You are a media analyst. Analyse the framing of this news article. Be concise — 1-2 sentences per field.

Article URL: {article['url']}
Article Text:
{article['text'][:2000]}

Format exactly as:
Headline Framing: <1-2 sentences>
Narrative Angle: <1-2 sentences>
Tone: <1 sentence>
Perspective: <1 sentence>
Framing Summary: <2 sentences max>
"""
        response = llm.invoke(prompt)
        framing_results.append({
            "url":      article["url"],
            "title":    article["title"],
            "framing":  str(response.content).strip()
        })

    return {
        **state,
        "framing_results": framing_results
    }








