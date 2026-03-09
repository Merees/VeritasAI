import requests
from bs4 import BeautifulSoup
from backend.tools.article_extractor import extract_article
from backend.models.ollama_client import get_llm

llm = get_llm()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def _fetch_with_session(url: str) -> str:
    """Use a persistent session with cookies — better for sites that need them."""
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        # First visit the homepage to get cookies
        from urllib.parse import urlparse
        parsed = urlparse(url)
        homepage = f"{parsed.scheme}://{parsed.netloc}"
        try:
            session.get(homepage, timeout=6)
        except Exception:
            pass
        # Now fetch the actual article
        resp = session.get(url, timeout=12, allow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer",
                          "aside", "form", "iframe", "noscript"]):
            tag.decompose()
        for selector in ["article", "[role='main']", "main",
                          ".article-body", ".post-content", ".entry-content",
                          ".story-body", ".article__body", ".article-content",
                          ".content-body", ".body-content", "#article-body"]:
            el = soup.select_one(selector)
            if el:
                text = el.get_text(separator=" ", strip=True)
                if len(text) > 200:
                    return text[:3500]
        paragraphs = soup.find_all("p")
        text = " ".join(
            p.get_text(strip=True) for p in paragraphs
            if len(p.get_text(strip=True)) > 40
        )
        return text[:3500] if len(text) > 200 else ""
    except Exception:
        return ""


def summarize_article(url):

    # Resolve Google News redirect URLs before extracting
    if "news.google.com" in url:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
            if "news.google.com" not in resp.url:
                url = resp.url
                print(f"[summarize] resolved to: {url}")
        except Exception:
            pass

    # Try article_extractor first (newspaper3k + BeautifulSoup)
    article_text = extract_article(url)

    # If that fails, try with a session (handles cookie-gated sites)
    if not article_text:
        article_text = _fetch_with_session(url)

    if not article_text:
        return {
            "summary": (
                "Could not extract this article. It may be paywalled, "
                "JavaScript-rendered, or blocking automated access. "
                "Try a different article or paste the text directly."
            )
        }

    prompt = f"""
Summarize the following news article in exactly 5 to 7 sentences.
Cover: what happened, who is involved, when and where, why it matters, and any key outcomes or reactions.
Do not use bullet points. Write in plain flowing prose.

Article:
{article_text[:3000]}
"""

    response = llm.invoke(prompt)

    return {
        "summary": str(response.content).strip()
    }