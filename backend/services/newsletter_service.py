import sqlite3
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER         = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
DB_PATH            = "newsletter.db"

from backend.services.explore_news_service import explore_news
from backend.services.summarize_service import summarize_article


# ── Database setup ──────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            email   TEXT NOT NULL UNIQUE,
            topics  TEXT NOT NULL,
            created TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def subscribe(email: str, topics: list[str]) -> dict:
    init_db()
    new_topics = [t.strip() for t in topics if t.strip()]
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Check if email already exists
        c.execute("SELECT topics FROM subscribers WHERE email = ?", (email,))
        row = c.fetchone()

        if row:
            # Merge existing topics with new ones, no duplicates
            existing = [t for t in row[0].split(",") if t]
            merged   = list(dict.fromkeys(existing + new_topics))  # preserves order, dedupes
            topics_str = ",".join(merged)
            c.execute("UPDATE subscribers SET topics = ? WHERE email = ?", (topics_str, email))
            action = "updated"
        else:
            topics_str = ",".join(new_topics)
            c.execute(
                "INSERT INTO subscribers (email, topics, created) VALUES (?, ?, ?)",
                (email, topics_str, datetime.now().isoformat())
            )
            action = "subscribed"

        conn.commit()
        conn.close()
        final_topics = topics_str.split(",")
        return {"status": action, "email": email, "topics": final_topics}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def unsubscribe(email: str) -> dict:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM subscribers WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    return {"status": "unsubscribed", "email": email}


def get_all_subscribers() -> list[dict]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT email, topics FROM subscribers")
    rows = c.fetchall()
    conn.close()
    return [{"email": r[0], "topics": [t for t in r[1].split(",") if t]} for r in rows]


def get_subscriber(email: str) -> dict | None:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT email, topics FROM subscribers WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {"email": row[0], "topics": [t for t in row[1].split(",") if t]}


def remove_topic(email: str, topic: str) -> dict:
    init_db()
    sub = get_subscriber(email)
    if not sub:
        return {"status": "error", "message": "Email not found."}
    updated = [t for t in sub["topics"] if t != topic]
    if not updated:
        # No topics left — unsubscribe entirely
        return unsubscribe(email)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE subscribers SET topics = ? WHERE email = ?",
              (",".join(updated), email))
    conn.commit()
    conn.close()
    return {"status": "updated", "email": email, "topics": updated}



    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT email, topics FROM subscribers")
    rows = c.fetchall()
    conn.close()
    return [{"email": r[0], "topics": r[1].split(",")} for r in rows]


# ── Digest builder ───────────────────────────────────────────────

def build_digest_for_topics(topics: list[str], articles_per_topic: int = 4) -> list[dict]:
    """Fetch and summarize top articles for each topic."""
    sections = []
    for topic in topics:
        try:
            results = explore_news(topic)[:articles_per_topic]
        except Exception:
            results = []

        articles = []
        for r in results:
            try:
                summary_data = summarize_article(r["url"])
                summary = summary_data.get("summary", "").strip()

                if not summary or summary.lower() == "unable to extract article":
                    # Try to guess why — either paywall or bot block
                    summary = None
                else:
                    summary = summary

                articles.append({
                    "title":         r["title"],
                    "url":           r["url"],
                    "summary":       summary,
                    "unavailable":   summary is None
                })
            except Exception:
                articles.append({
                    "title":       r["title"],
                    "url":         r["url"],
                    "summary":     None,
                    "unavailable": True
                })

        sections.append({"topic": topic, "articles": articles})
    return sections


# ── Email renderer ───────────────────────────────────────────────

def render_html_email(recipient_email: str, sections: list[dict]) -> str:
    date_str = datetime.now().strftime("%B %d, %Y")
    article_blocks = ""

    for section in sections:
        article_blocks += f"""
        <tr><td style="padding: 28px 0 8px 0;">
          <div style="font-family:'Georgia',serif;font-size:11px;letter-spacing:3px;
                      text-transform:uppercase;color:#b8860b;border-bottom:1px solid #2a2a2a;
                      padding-bottom:10px;margin-bottom:18px;">
            {section['topic'].upper()}
          </div>
        </td></tr>"""

        for art in section["articles"]:
            if art.get("unavailable"):
                summary_block = """
          <table cellpadding="0" cellspacing="0" style="margin-bottom:6px;">
            <tr>
              <td style="background:rgba(184,134,11,0.08);border:1px solid rgba(184,134,11,0.25);
                         border-radius:3px;padding:8px 12px;">
                <span style="font-family:monospace;font-size:11px;color:#b8860b;letter-spacing:1px;">
                  ⓘ FULL TEXT UNAVAILABLE
                </span>
                <span style="font-family:'Georgia',serif;font-size:12px;color:#6b6d75;
                             display:block;margin-top:3px;line-height:1.5;">
                  This article may be behind a paywall or blocked automated access.
                  Click the link below to read it directly.
                </span>
              </td>
            </tr>
          </table>"""
            else:
                summary_block = f"""
          <p style="font-family:'Georgia',serif;font-size:14px;color:#9a9a9a;
             line-height:1.7;margin:0 0 8px 0;">{art['summary']}</p>"""

            article_blocks += f"""
        <tr><td style="padding-bottom:24px;">
          <a href="{art['url']}" style="font-family:'Georgia',serif;font-size:17px;
             font-weight:bold;color:#e8e6e0;text-decoration:none;line-height:1.4;
             display:block;margin-bottom:8px;">{art['title']}</a>
          {summary_block}
          <a href="{art['url']}" style="font-family:monospace;font-size:11px;
             color:#b8860b;text-decoration:none;letter-spacing:1px;">READ FULL ARTICLE →</a>
        </td></tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0b0c0f;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0b0c0f;">
  <tr><td align="center" style="padding:40px 20px;">
    <table width="600" cellpadding="0" cellspacing="0"
           style="background:#13151a;border:1px solid #252830;border-radius:4px;overflow:hidden;">

      <!-- Header -->
      <tr><td style="padding:36px 40px 28px 40px;border-bottom:1px solid #252830;">
        <div style="font-family:'Georgia',serif;font-size:26px;font-weight:bold;color:#e8e6e0;
                    letter-spacing:-0.5px;">
          Veritas<span style="color:#d4a843;">AI</span>
        </div>
        <div style="font-family:monospace;font-size:10px;letter-spacing:3px;
                    text-transform:uppercase;color:#6b6d75;margin-top:4px;">
          Daily News Digest
        </div>
        <div style="font-family:monospace;font-size:11px;color:#6b6d75;margin-top:12px;">
          {date_str}
        </div>
      </td></tr>

      <!-- Intro -->
      <tr><td style="padding:24px 40px 0 40px;">
        <p style="font-family:'Georgia',serif;font-size:14px;color:#6b6d75;
                  line-height:1.6;margin:0;font-style:italic;">
          Your personalised briefing for today — curated and summarised by AI.
        </p>
      </td></tr>

      <!-- Articles -->
      <tr><td style="padding:0 40px;">
        <table width="100%" cellpadding="0" cellspacing="0">
          {article_blocks}
        </table>
      </td></tr>

      <!-- Footer -->
      <tr><td style="padding:28px 40px;border-top:1px solid #252830;">
        <p style="font-family:monospace;font-size:10px;color:#3a3a3a;
                  text-align:center;margin:0;letter-spacing:1px;">
          Sent to {recipient_email} · VeritasAI Newsletter
        </p>
      </td></tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""
    return html


# ── Gmail sender ─────────────────────────────────────────────────

def send_digest_email(recipient: str, sections: list[dict]) -> dict:
    date_str = datetime.now().strftime("%B %d, %Y")
    subject  = f"VeritasAI Daily Digest — {date_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_USER
    msg["To"]      = recipient

    html_body = render_html_email(recipient, sections)
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, recipient, msg.as_string())
        return {"status": "sent", "to": recipient}
    except Exception as e:
        return {"status": "error", "to": recipient, "message": str(e)}


# ── Main send-to-all ──────────────────────────────────────────────

def send_newsletter_to_all() -> dict:
    subscribers = get_all_subscribers()
    if not subscribers:
        return {"status": "no_subscribers", "sent": 0, "failed": 0, "results": []}

    results = []
    sent    = 0
    failed  = 0

    for sub in subscribers:
        sections = build_digest_for_topics(sub["topics"])
        result   = send_digest_email(sub["email"], sections)
        results.append(result)
        if result["status"] == "sent":
            sent += 1
        else:
            failed += 1

    return {"status": "done", "sent": sent, "failed": failed, "results": results}


# ── Single preview send ───────────────────────────────────────────

def send_preview(email: str, topics: list[str]) -> dict:
    sections = build_digest_for_topics(topics)
    return send_digest_email(email, sections)