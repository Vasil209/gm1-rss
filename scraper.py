import requests
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime, timezone
from xml.sax.saxutils import escape
import email.utils as eut

URL = "https://display.edubs.ch/gm1"

def fetch_html(url):
    headers = {
        "User-Agent": "GM-Muensterplatz-RSS/1.0 (+github)",
        "Accept": "text/html,application/xhtml+xml",
    }
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.text

def build_items(soup):
    items = []
    for panel in soup.select("div.panel.panel-default"):
        # Only include Stellvertretungen with "fällt aus" in body
        body = panel.select_one(".panel-body")
        if not body:
            continue
        body_text = " ".join(body.stripped_strings)
        if "fällt aus" not in body_text:
            continue

        heading = panel.select_one(".panel-heading")
        footer = panel.select_one(".panel-footer")
        day_h3 = panel.find_previous("h3")
        day_text = day_h3.get_text(strip=True).rstrip(":") if day_h3 else ""

        title = " ".join(heading.stripped_strings) if heading else "Stellvertretung"
        description_parts = []
        if day_text:
            description_parts.append(f"Tag: {day_text}")
        description_parts.append(body_text)
        if footer:
            description_parts.append(" ".join(footer.stripped_strings))
        description = " — ".join(description_parts)

        pub_date = eut.format_datetime(datetime.now(timezone.utc))
        guid = f"{day_text}|{title}|{description}"

        items.append({
            "title": title,
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
        "<title>GM Münsterplatz – Ausfälle</title>",
        f"<link>{URL}</link>",
        "<description>Automatisch generierter Feed aus dem Infoscreen (nur „fällt aus“ Einträge).</description>",
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
