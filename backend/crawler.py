# backend/crawler.py
import os
import re
import time
import json
import urllib.parse as urlparse
from collections import deque
from bs4 import BeautifulSoup
import trafilatura

# Try to use Selenium for JS-rendered content, fallback to requests
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        SELENIUM_AVAILABLE = True
        WEBDRIVER_MANAGER_AVAILABLE = True
    except ImportError:
        SELENIUM_AVAILABLE = True
        WEBDRIVER_MANAGER_AVAILABLE = False
except ImportError:
    SELENIUM_AVAILABLE = False
    import requests

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

def _get_driver():
    """Initialize and return a Selenium WebDriver."""
    if not SELENIUM_AVAILABLE:
        return None
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        if WEBDRIVER_MANAGER_AVAILABLE:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # Try to use system ChromeDriver
            driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"⚠️  Selenium setup failed: {e}")
        print("   Falling back to requests (may not work for JS-rendered sites)")
        return None

def _fetch_with_selenium(driver, url):
    """Fetch page content using Selenium."""
    try:
        driver.get(url)
        # Wait for page to load (wait for body or a common element)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except TimeoutException:
            pass
        
        # Additional wait for JavaScript to render content
        time.sleep(2)
        
        # Get the page source after JS execution
        html = driver.page_source
        return html
    except Exception as e:
        print(f"   Selenium fetch error: {e}")
        return None

def _fetch_with_requests(url):
    """Fallback: Fetch page content using requests."""
    if not SELENIUM_AVAILABLE:
        import requests
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        try:
            r = session.get(url, timeout=15)
            if r.status_code == 200 and "text/html" in r.headers.get("Content-Type", ""):
                return r.text
        except Exception as e:
            print(f"   Requests fetch error: {e}")
    return None

def crawl(max_pages: int = 150, use_selenium: bool = True):
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

    # Initialize driver if Selenium is available and requested
    driver = None
    if use_selenium and SELENIUM_AVAILABLE:
        print("🚀 Initializing Selenium WebDriver for JavaScript-rendered content...")
        driver = _get_driver()
        if driver:
            print("✅ Selenium WebDriver ready")
        else:
            print("⚠️  Falling back to requests")
            use_selenium = False
    elif not SELENIUM_AVAILABLE:
        print("⚠️  Selenium not available, using requests (may not work for JS sites)")
        use_selenium = False

    while q and len(seen) < max_pages:
        url = q.popleft()
        if url in seen or not _allowed(url):
            continue
        seen.add(url)

        try:
            # Fetch HTML
            if use_selenium and driver:
                html = _fetch_with_selenium(driver, url)
            else:
                html = _fetch_with_requests(url)
            
            if not html:
                print(f"✖ Skipped (no content): {url}")
                continue

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
            links_found = 0
            for a in soup.find_all("a"):
                href = a.get("href")
                if not href:
                    continue
                link = _abs(url, href.split("#")[0])
                if _allowed(link) and link not in seen and link not in q:
                    q.append(link)
                    links_found += 1

            print(f"✔ Crawled: {url}  (imgs:{len(imgs)}, links:{links_found}, content:{len(text)} chars)")

            time.sleep(1)  # be polite

        except Exception as e:
            print(f"✖ Error: {url} - {e}")

    # Cleanup
    if driver:
        try:
            driver.quit()
        except:
            pass

    # save
    with open(DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)
    with open(IMAGES_JSON, "w", encoding="utf-8") as f:
        json.dump(image_bank, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Crawl complete. Pages: {len(pages)}  Saved: {DATA_JSON}")
    return pages

if __name__ == "__main__":
    crawl()
