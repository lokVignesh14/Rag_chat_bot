# backend/crawler.py
import os
import re
import time
import json
import urllib.parse as urlparse
from collections import deque
import requests
from bs4 import BeautifulSoup
import trafilatura

BASE = os.getenv("SITE_BASE", "https://www.krpower.in")
OUT_DIR = os.path.dirname(__file__)
DATA_JSON = os.path.join(OUT_DIR, "data", "pages.json")
IMAGES_JSON = os.path.join(OUT_DIR, "data", "images.json")

ALLOWED_HOST = urlparse.urlparse(BASE).netloc

EXCLUDE_PATTERNS = [
    r"/wp-login",
    r"/cart",
    r"/checkout",
    r"/my-account",
    r"/tag/",
    r"/category/",
    r"/feed/",
    r"/author/",
    r"\.(pdf|zip|rar|7z|gz|xml|docx?)$",
]

def _allowed(url: str) -> bool:
    if not url.startswith("http"):
        return False
    u = urlparse.urlparse(url)
    if u.netloc != ALLOWED_HOST:
        return False
    for pat in EXCLUDE_PATTERNS:
        if re.search(pat, url, re.IGNORECASE):
            return False
    return True

def _abs(base, link):
    return urlparse.urljoin(base, link)

def _extract_text(html: str, url: str) -> str:
    # Try trafilatura first (best readability)
    try:
        txt = trafilatura.extract(html, include_comments=False, include_tables=False, url=url)
        if txt and len(txt.strip()) > 60:
            return txt.strip()
    except Exception:
        pass
    # Fallback: BS4 clean text
    soup = BeautifulSoup(html, "lxml")
    for bad in soup(["script", "style", "noscript"]):
        bad.extract()
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    return text

def _extract_images(soup: BeautifulSoup, page_url: str):
    imgs = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if not src:
            continue
        src = _abs(page_url, src)
        # Skip tiny/icons
        if any(x in src.lower() for x in ["/logo", "icon", "placeholder"]):
            continue
        imgs.append(src)
    return list(dict.fromkeys(imgs))[:20]

def crawl(max_pages: int = 150):
    os.makedirs(os.path.join(OUT_DIR, "data"), exist_ok=True)

    start_urls = [
        BASE,
        _abs(BASE, "/products/"),
        _abs(BASE, "/about-us/"),
        _abs(BASE, "/contact-us/"),
        _abs(BASE, "/gallery/"),
    ]

    seen = set()
    q = deque(start_urls)
    pages = []
    image_bank = {}

    session = requests.Session()
    session.headers.update({"User-Agent": "krpower-chatbot-crawler/1.0"})

    while q and len(seen) < max_pages:
        url = q.popleft()
        if url in seen or not _allowed(url):
            continue
        seen.add(url)

        try:
            r = session.get(url, timeout=15)
            if r.status_code != 200 or "text/html" not in r.headers.get("Content-Type", ""):
                continue

            html = r.text
            soup = BeautifulSoup(html, "lxml")

            # text
            text = _extract_text(html, url)
            title = (soup.title.string.strip() if soup.title and soup.title.string else url)

            # images
            imgs = _extract_images(soup, url)
            if imgs:
                image_bank[url] = imgs

            # store
            pages.append({
                "url": url,
                "title": title,
                "content": text or "",
                "images": imgs,
            })

            # enqueue links
            for a in soup.find_all("a"):
                href = a.get("href")
                if not href:
                    continue
                link = _abs(url, href.split("#")[0])
                if _allowed(link) and link not in seen:
                    q.append(link)

            print(f"✔ Crawled: {url}  (imgs:{len(imgs)})")

            time.sleep(0.5)  # be polite

        except Exception as e:
            print("✖ Error:", url, e)

    # save
    with open(DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)
    with open(IMAGES_JSON, "w", encoding="utf-8") as f:
        json.dump(image_bank, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Crawl complete. Pages: {len(pages)}  Saved: {DATA_JSON}")
    return pages

if __name__ == "__main__":
    crawl()
