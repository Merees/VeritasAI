from backend.tools.search_tool import search_news
from backend.tools.article_extractor import extract_article


def evidence_retriever(state):

    claim = state["claim"]

    results = search_news(claim)

    evidence = []
    sources  = []

    for r in results:

        url   = r["url"]
        title = r["title"]

        article_text = extract_article(url)

        if article_text:
            # Full text extracted successfully
            evidence.append(article_text[:800])
        else:
            # Extraction failed (paywall/blocked) — use title as minimal evidence
            # so the LLM still knows this source exists and what it's about
            evidence.append(f"[Title only — full text unavailable] {title}")

        # Always add the URL regardless of extraction success
        sources.append(url)

    return {
        **state,
        "evidence": evidence,
        "sources":  sources
    }
