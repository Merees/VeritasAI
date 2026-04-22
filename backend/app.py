from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

from backend.services.verify_news_service import verify_news
from backend.services.summarize_service import summarize_article
from backend.services.explore_news_service import explore_news
from backend.services.bias_service import analyse_bias
from backend.services.newsletter_service import (
    subscribe, unsubscribe, get_subscriber, get_all_subscribers,
    send_newsletter_to_all, send_preview, remove_topic
)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Existing models ───────────────────────────────────────────────

class NewsInput(BaseModel):
    text: str

class UrlInput(BaseModel):
    url: str


# ── Newsletter models ─────────────────────────────────────────────

class SubscribeInput(BaseModel):
    email:  str
    topics: List[str]

class RemoveTopicInput(BaseModel):
    email: str
    topic: str

class UnsubscribeInput(BaseModel):
    email:          str
    admin_password: str

class UserUnsubscribeInput(BaseModel):
    email: str

class SendNewsletterInput(BaseModel):
    admin_password: str

class PreviewInput(BaseModel):
    email:          str
    topics:         List[str]
    admin_password: str


def check_admin(password: str):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid admin password")


class BiasInput(BaseModel):
    urls: List[str]


# ── Existing routes ───────────────────────────────────────────────

@app.post("/verify-news")
def verify(input: NewsInput):
    return verify_news(input.text)

@app.post("/summarize-news")
def summarize(input: UrlInput):
    return summarize_article(input.url)

@app.get("/explore-news")
def explore(topic: str):
    return explore_news(topic)


@app.get("/debug-rss")
def debug_rss(topic: str = "technology"):
    import requests, xml.etree.ElementTree as ET
    from urllib.parse import quote
    url = f"https://news.google.com/rss/search?q={quote(topic)}&hl=en-US&gl=US&ceid=US:en"
    resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    root = ET.fromstring(resp.content)
    items = []
    for item in root.findall(".//item")[:2]:
        source = item.find("source")
        items.append({
            "title":       item.findtext("title", ""),
            "link":        item.findtext("link", ""),
            "description": item.findtext("description", ""),
            "guid":        item.findtext("guid", ""),
            "source_url":  source.get("url", "") if source is not None else "",
            "source_text": source.text if source is not None else "",
        })
    return items


@app.get("/resolve-url")
def resolve_url(url: str):
    """Resolve Google News redirect URLs to real article URLs."""
    import re
    import requests
    if "news.google.com" not in url:
        return {"url": url}
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
        resp = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        if "news.google.com" not in resp.url:
            return {"url": resp.url}
        # Parse page for real URL
        matches = re.findall(
            r'https?://(?!(?:www\.)?google\.com)[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}/[^\s"\'<>]{10,}',
            resp.text
        )
        if matches:
            return {"url": matches[0]}
    except Exception:
        pass
    return {"url": url}


@app.post("/analyse-bias")
def bias_analysis(input: BiasInput):
    return analyse_bias(input.urls)


@app.get("/news-ticker")
def news_ticker():
    categories = ["World", "Technology", "Sports", "Business", "Science", "Politics", "Entertainment", "Health"]
    result = {}
    for cat in categories:
        try:
            articles = explore_news(cat)
            result[cat] = articles[:5]
        except Exception:
            result[cat] = []
    return result


# ── Newsletter routes ─────────────────────────────────────────────

@app.post("/newsletter/subscribe")
def newsletter_subscribe(input: SubscribeInput):
    return subscribe(input.email, input.topics)

# User self-service — no admin password needed
@app.get("/newsletter/my-subscription")
def my_subscription(email: str):
    sub = get_subscriber(email)
    if not sub:
        raise HTTPException(status_code=404, detail="Email not found.")
    return sub

@app.post("/newsletter/remove-topic")
def newsletter_remove_topic(input: RemoveTopicInput):
    return remove_topic(input.email, input.topic)

@app.post("/newsletter/user-unsubscribe")
def newsletter_user_unsubscribe(input: UserUnsubscribeInput):
    sub = get_subscriber(input.email)
    if not sub:
        raise HTTPException(status_code=404, detail="Email not found.")
    return unsubscribe(input.email)

# Admin routes
@app.post("/newsletter/unsubscribe")
def newsletter_unsubscribe(input: UnsubscribeInput):
    check_admin(input.admin_password)
    return unsubscribe(input.email)

@app.get("/newsletter/subscribers")
def newsletter_subscribers(admin_password: str):
    check_admin(admin_password)
    return get_all_subscribers()

@app.post("/newsletter/send")
def newsletter_send(input: SendNewsletterInput):
    check_admin(input.admin_password)
    return send_newsletter_to_all()

@app.post("/newsletter/preview")
def newsletter_preview(input: PreviewInput):
    check_admin(input.admin_password)
    return send_preview(input.email, input.topics)