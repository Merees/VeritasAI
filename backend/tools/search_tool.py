import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import re


def _find_article_on_site(title: str, source_url: str) -> str:
    """Fetch publisher homepage and find the matching article link by title words."""
    if not source_url:
        return ""
    try:
        clean_title = title.lower()
        # Use significant words only (skip short words)
        words = [w for w in re.split(r'\W+', clean_title) if len(w) > 3][:6]

        resp = requests.get(
            source_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"},
            timeout=8,
            allow_redirects=True
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        domain = source_url.rstrip("/")

        best_url, best_score = "", 0
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True).lower()
            href = str(a.get("href", ""))
            score = sum(1 for w in words if w in text)
            if score > best_score and score >= min(3, len(words)):
                best_score = score
                if href.startswith("http"):
                    best_url = href
                elif href.startswith("/"):
                    best_url = domain + href

        return best_url
    except Exception:
        return ""


def search_news(query):
    results = []

    try:
        url = f"https://news.google.com/rss/search?q={quote(query)}&hl=en-US&gl=US&ceid=US:en"
        response = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        root = ET.fromstring(response.content)

        items_data = []
        for item in root.findall(".//item")[:5]:
            title = item.findtext("title", "").strip()
            link  = item.findtext("link", "").strip()
            source_el = item.find("source")
            source_url = source_el.get("url", "").strip() if source_el is not None else ""
            if " - " in title:
                title = title.rsplit(" - ", 1)[0].strip()
            if title and link:
                items_data.append({"title": title, "link": link, "source_url": source_url})

        # Resolve all URLs in parallel
        def resolve(item):
            real = _find_article_on_site(item["title"], item["source_url"])
            return {"title": item["title"], "url": real or item["link"]}

        with ThreadPoolExecutor(max_workers=5) as ex:
            for future in as_completed({ex.submit(resolve, i): i for i in items_data}):
                try:
                    results.append(future.result())
                except Exception:
                    pass

    except Exception:
        pass

    return results








