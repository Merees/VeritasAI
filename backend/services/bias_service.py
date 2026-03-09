from backend.tools.article_extractor import extract_article
from backend.graph.bias_workflow     import create_bias_workflow

workflow = create_bias_workflow()


def analyse_bias(urls: list[str]) -> dict:
    """
    Main entry point. Takes 2-4 article URLs, runs the multi-agent pipeline,
    returns a structured bias report.
    """
    if len(urls) < 2:
        return {"error": "Please provide at least 2 article URLs to compare."}
    if len(urls) > 4:
        urls = urls[:4]  # cap at 4

    # Extract article text for each URL
    articles = []
    for url in urls:
        text = extract_article(url)
        # Try to get a title from first line of text or fall back to domain
        title = ""
        if text:
            first_line = text.strip().split('\n')[0][:120]
            title = first_line if len(first_line) > 20 else url
        else:
            try:
                from urllib.parse import urlparse
                title = urlparse(url).netloc.replace('www.', '')
            except Exception:
                title = url

        articles.append({
            "url":   url,
            "title": title,
            "text":  text or "[Could not extract article text — paywalled or blocked]"
        })

    # Initial state
    state = {
        "articles":          articles,
        "framing_results":   [],
        "fact_results":      [],
        "omission_analysis": "",
        "bias_scores":       [],
        "bias_narrative":    "",
        "final_report":      ""
    }

    result = workflow.invoke(state)

    return {
        "articles":          result["articles"],
        "framing_results":   result["framing_results"],
        "fact_results":      result["fact_results"],
        "omission_analysis": result["omission_analysis"],
        "bias_scores":       result["bias_scores"],
        "bias_narrative":    result["bias_narrative"]
    }
