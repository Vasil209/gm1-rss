# scraper.py
# Builds an RSS feed from https://display.edubs.ch/gm1 and writes it to ./public/rss.xml

from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape
import email.utils as eut
import requests
from bs4 import BeautifulSoup

URL = "https://display.edubs.ch/gm1"

def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": "GM-Muensterplatz-RSS/1.0 (+github)",
        "Accept": "text/html,application/xhtml+xml",
    }
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.text

def build_items(soup: BeautifulSoup):
    items = []
    # Find all "panels" and keep only those under the <h2>Stellvertretungen</h2> section
    for panel in soup.select("div.panel.panel-default"):
        h2 = panel.find_previous("h2")
        if not h2 or "Stellvertretungen" not in h2.get_text():
            continue

        day_h3 = panel.find_previous("h3")
        day_text = (day_h3.get_text(strip=True).rstrip(":") if day_h3 else "").strip()

        heading = panel.select_one(".panel-heading")
        body = panel.select_one(".panel-body")
        footer = panel.select_one(".panel-footer")

        title_text = " ".join(heading.stripped_strings) if heading else "Stellvertretung"
        desc_parts = []
        if day_text:
            desc_parts.append(f"Tag: {day_text}")
        if body:
            desc_parts.append(" ".join(body.stripped_strings))
        if footer:
            desc_parts.append(" ".join(footer.stripped_strings))
        description = " — ".join(desc_parts) if desc_parts else title_text

        # pubDate: now in UTC (RSS compliant)
        pub_date = eut.format_datetime(datetime.now(timezone.utc))

        # GUID: stable-ish hash of content
        guid = f"{day_text}|{title_text}|{description}"

        items.append({
            "title": title_text,
            "description": description,
            "pubDate": pub_date,
            "guid": guid,
            "link": URL,
        })
    return items

def write_rss(items):
    outdir = Path("public")
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / "rss.xml"

    head = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0">',
        "<channel>",
        "<title>GM Münsterplatz – Stellvertretungen (inoffiziell)</title>",
        f"<link>{URL}</link>",
        "<description>Automatisch generierter Feed aus dem Infoscreen (keine offizielle Quelle).</description>",
    ]

    body = []
    for it in items:
        body.extend([
            "<item>",
            f"<title>{escape(it['title'])}</title>",
            f"<description>{escape(it['description'])}</description>",
            f"<link>{escape(it['link'])}</link>",
            f"<guid isPermaLink=\"false\">{escape(it['guid'])}</guid>",
            f"<pubDate>{it['pubDate']}</pubDate>",
            "</item>",
        ])

    tail = ["</channel>", "</rss>"]

    out.write_text("\n".join(head + body + tail), encoding="utf-8")
    print(f"Wrote {out} with {len(items)} items.")

def main():
    html = fetch_html(URL)
    soup = BeautifulSoup(html, "html.parser")
    items = build_items(soup)
    write_rss(items)

if __name__ == "__main__":
    main()
