import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/",
    "DNT": "1",
}

ARTICLE_SELECTORS = [
    "article", "[role='main']", "main",
    ".article-body", ".post-content", ".entry-content",
    ".story-body", ".article__body", ".article-content",
    ".content-body", "#article-body", ".body__inner-container",
    "div._s30J", ".Normal",         # Times of India
    ".ins_storybody", ".sp-cn",     # NDTV
    ".description",                  # India Today
]


def _parse_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer",
                      "aside", "form", "iframe", "noscript"]):
        tag.decompose()
    for selector in ARTICLE_SELECTORS:
        el = soup.select_one(selector)
        if el:
            text = el.get_text(separator=" ", strip=True)
            if len(text) > 200:
                return text[:3500]
    paragraphs = soup.find_all("p")
    text = " ".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 40)
    return text[:3500] if len(text) > 200 else ""


def _fetch(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=12, allow_redirects=True)
    resp.raise_for_status()
    return resp.text


def _to_amp(url: str) -> str:
    """Return AMP URL for known Indian/JS-heavy news sites."""
    rules = [
        (r"timesofindia\.indiatimes\.com/(?!amp)", "timesofindia.indiatimes.com/amp/"),
        (r"hindustantimes\.com/(?!amp)",            "hindustantimes.com/amp/"),
        (r"ndtv\.com/(?!amp)",                      "ndtv.com/amp/"),
    ]
    for pattern, replacement in rules:
        if re.search(pattern, url):
            return re.sub(pattern, replacement, url, count=1)
    return ""


def extract_article(url: str) -> str:
    print(f"[extractor] fetching: {url}")

    # Strategy 1: direct fetch
    try:
        html = _fetch(url)
        text = _parse_html(html)
        if text:
            print(f"[extractor] OK via direct fetch ({len(text)} chars)")
            return text
        print("[extractor] direct fetch got HTML but no usable text")
    except Exception as e:
        print(f"[extractor] direct fetch failed: {e}")

    # Strategy 2: AMP version (for TOI, HT, NDTV etc.)
    amp_url = _to_amp(url)
    if amp_url:
        try:
            html = _fetch(amp_url)
            text = _parse_html(html)
            if text:
                print(f"[extractor] OK via AMP ({len(text)} chars)")
                return text
        except Exception as e:
            print(f"[extractor] AMP fetch failed: {e}")

    # Strategy 3: Google AMP cache
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        cache_url = (
            f"https://{parsed.netloc.replace('.', '-')}"
            f".cdn.ampproject.org/v/s/{parsed.netloc}{parsed.path}"
        )
        html = _fetch(cache_url)
        text = _parse_html(html)
        if text:
            print(f"[extractor] OK via Google AMP cache ({len(text)} chars)")
            return text
    except Exception as e:
        print(f"[extractor] Google AMP cache failed: {e}")

    print(f"[extractor] all strategies failed for: {url}")
    return ""