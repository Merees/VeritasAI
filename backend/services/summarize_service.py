from backend.tools.article_extractor import extract_article
from backend.models.ollama_client import get_llm

llm = get_llm()


def summarize_article(url):

    article_text = extract_article(url)

    if not article_text:
        return {"summary": "Unable to extract article"}

    prompt = f"""
Summarize the following news article in 4-5 sentences.

Article:
{article_text[:2000]}
"""

    response = llm.invoke(prompt)

    return {
        "summary": response.content.strip()
    }