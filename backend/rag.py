import os
import json
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(BASE_DIR, "data", "krpower_data.json")
IMAGES_PATH = os.path.join(BASE_DIR, "data", "images.json")
PAGES_PATH = os.path.join(BASE_DIR, "data", "pages.json")

# Load product dataset
with open(DATA_PATH, "r", encoding="utf-8") as f:
    PRODUCTS = json.load(f)

# Load image map
with open(IMAGES_PATH, "r", encoding="utf-8") as f:
    IMAGES_DB = json.load(f)

# Load website pages
try:
    with open(PAGES_PATH, "r", encoding="utf-8") as f:
        WEBSITE_PAGES = json.load(f)
except FileNotFoundError:
    WEBSITE_PAGES = []


def _normalize(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _tokenize(text: str) -> set:
    base = _normalize(text)
    if not base:
        return set()
    tokens = set(base.split())
    compact = base.replace(" ", "")
    if compact:
        tokens.add(compact)
    return tokens


def _item_tokens(item: dict) -> set:
    parts = [
        item.get("slug", ""),
        item.get("name", ""),
        item.get("category", ""),
        json.dumps(item.get("specs", {})),
        " ".join(item.get("sizes", [])),
        item.get("measurement", ""),
        item.get("stock", "")
    ]
    blob = " ".join(parts)
    tokens = _tokenize(blob)
    # Add numeric-only tokens for measurements like "3000"
    numeric_tokens = {re.sub(r"[^0-9]", "", t) for t in tokens if any(c.isdigit() for c in t)}
    tokens.update({t for t in numeric_tokens if t})
    return tokens


# Precompute token sets for faster matching
PRODUCT_TOKENS = [
    (_item_tokens(item), item)
    for item in PRODUCTS
]


def search(query: str, k: int = 5):
    q_tokens = _tokenize(query)
    if not q_tokens:
        return []

    results = []
    for tokens, item in PRODUCT_TOKENS:
        matches = q_tokens & tokens
        if matches:
            results.append((len(matches), item))

    # Fall back to fuzzy substring if no token matches
    if not results:
        q_norm = _normalize(query)
        for tokens, item in PRODUCT_TOKENS:
            item_blob = " ".join(tokens)
            if q_norm and q_norm in item_blob:
                results.append((1, item))

    results.sort(key=lambda x: (-x[0], x[1].get("name", "")))
    return [item for _, item in results[:k]]


def images_for_query(query: str, k: int = 12):
    q = query.lower()
    imgs = []

    # Product matches
    for p in search(query, k=8):
        for u in p.get("images", []):
            if isinstance(u, str) and u.startswith("http"):
                imgs.append(u)
        if p.get("url") in IMAGES_DB:
            imgs.extend(IMAGES_DB[p["url"]])

    # Website page matches (for company/about/location queries)
    website_pages = search_website(query, k=5)
    for page in website_pages:
        for u in page.get("images", []):
            if isinstance(u, str) and u.startswith("http"):
                imgs.append(u)

    # Company/About - also check IMAGES_DB for backward compatibility
    if any(word in q for word in ["about", "company", "who are", "profile", "kr power", "location", "contact", "address"]):
        if "https://www.krpower.in/about-us/" in IMAGES_DB:
            imgs.extend(IMAGES_DB["https://www.krpower.in/about-us/"])
        if "https://www.krpower.in" in IMAGES_DB:
            imgs.extend(IMAGES_DB["https://www.krpower.in"])
        if "https://www.krpower.in/contact-us/" in IMAGES_DB:
            imgs.extend(IMAGES_DB["https://www.krpower.in/contact-us/"])

    # Deduplicate
    seen, final = set(), []
    for u in imgs:
        if u not in seen and u.startswith("http"):
            final.append(u)
            seen.add(u)

    return final[:k]


# Website content search functions
def _tokenize_text(text: str) -> set:
    """Helper to tokenize text for website search."""
    if not text:
        return set()
    return _tokenize(text)


PAGE_INDEX = []
for page in WEBSITE_PAGES:
    PAGE_INDEX.append({
        "page": page,
        "title_tokens": _tokenize_text(page.get("title", "")),
        "content_tokens": _tokenize_text(page.get("content", "")),
        "url_tokens": _tokenize_text(page.get("url", "")),
    })


STOP_WORDS = {
    "about", "the", "and", "for", "with", "from", "into", "that", "this",
    "what", "your", "you", "are", "who", "tell", "me", "our", "us", "in",
    "on", "to", "of", "is", "it", "a", "an"
}


def search_website(query: str, k: int = 5):
    """Search website pages for relevant content."""
    if not PAGE_INDEX:
        return []

    q_tokens = _tokenize(query)
    q_words = [w for w in re.split(r"\s+", query.lower()) if w]
    effective_words = [w for w in q_words if len(w) > 2 and w not in STOP_WORDS]

    results = []
    for entry in PAGE_INDEX:
        page = entry["page"]
        score = 0

        title_matches = len(q_tokens & entry["title_tokens"])
        content_matches = len(q_tokens & entry["content_tokens"])
        url_matches = len(q_tokens & entry["url_tokens"])

        score += title_matches * 4
        score += url_matches * 2
        score += content_matches

        title_lower = page.get("title", "").lower()
        content_lower = page.get("content", "").lower()

        if not q_tokens:
            # If tokenization failed (e.g., non-alphanumeric query), fallback to substring search
            for word in effective_words:
                if word and word in title_lower:
                    score += 4
                elif word and word in content_lower:
                    score += 2

        # Additional substring boosts for explicit keyword matches
        for word in effective_words:
            if not word:
                continue
            if word in title_lower:
                score += 3
            elif word in content_lower:
                score += 1

        if score > 0 or title_matches or content_matches or url_matches:
            results.append((score, title_matches, content_matches, page))

    if not results:
        return []

    results.sort(key=lambda x: (-x[0], -x[1], -x[2], x[3].get("url", "")))
    top_pages = [page for _, _, _, page in results[:k]]
    return top_pages


def get_company_info():
    """Extract company information from scraped website pages."""
    info = {
        "name": "K.R. Power Supports Pvt Ltd",
        "description": "",
        "contact": {
            "phone": "",
            "email": "",
            "address": "",
            "website": "https://www.krpower.in"
        }
    }
    
    # Search for contact page
    contact_pages = [p for p in WEBSITE_PAGES if "contact" in p.get("url", "").lower()]
    if contact_pages:
        contact_content = contact_pages[0].get("content", "")
        
        # Extract phone numbers - improved pattern to match Indian phone format
        # Pattern: +91 followed by 10 digits, or 0 followed by digits, or standalone 10+ digit numbers
        phone_patterns = [
            r'\+91\s*\d{10}',  # +91 1234567890
            r'\+91\s*\d{5}\s*\d{5}',  # +91 12345 67890
            r'0\d{2,3}\s*\d{7}',  # 0422 2535622
            r'\d{10,}',  # Any 10+ digit number
        ]
        phones = []
        for pattern in phone_patterns:
            found = re.findall(pattern, contact_content)
            phones.extend(found)
        
        # Clean and deduplicate phone numbers
        cleaned_phones = []
        seen = set()
        for phone in phones:
            # Remove spaces and normalize
            clean_phone = re.sub(r'\s+', ' ', phone.strip())
            if clean_phone and clean_phone not in seen and len(re.sub(r'\D', '', clean_phone)) >= 10:
                cleaned_phones.append(clean_phone)
                seen.add(clean_phone)
                if len(cleaned_phones) >= 5:  # Limit to 5 phone numbers
                    break
        
        if cleaned_phones:
            info["contact"]["phone"] = " / ".join(cleaned_phones)
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, contact_content)
        if emails:
            info["contact"]["email"] = emails[0]
        
        # Extract address - look for lines containing address keywords
        address_lines = []
        lines = contact_content.split('\n')
        collecting_address = False
        for line in lines:
            line = line.strip()
            # Check if line contains address indicators
            if any(word in line.lower() for word in ['road', 'street', 'coimbatore', 'tamil nadu', 'india', 'ganapathy', 'chinnavedampatti', 'school road']):
                collecting_address = True
            if collecting_address and line and len(line) > 5:
                # Skip if it's just a phone or email
                if not re.search(r'\+?\d|@', line):
                    address_lines.append(line)
                    if len(address_lines) >= 3:  # Take up to 3 lines
                        break
        
        # If no address found with keywords, try to find lines with "9A" or address-like patterns
        if not address_lines:
            for line in lines:
                line = line.strip()
                if ('9a' in line.lower() or '641' in line or '006' in line) and len(line) > 15:
                    address_lines.append(line)
                    break
        
        if address_lines:
            info["contact"]["address"] = ", ".join(address_lines)
    
    # Search for about page for description
    about_pages = [p for p in WEBSITE_PAGES if "about" in p.get("url", "").lower()]
    if about_pages:
        about_content = about_pages[0].get("content", "")
        # Extract company description (first substantial paragraph)
        sentences = re.split(r'[.!?]\s+', about_content)
        desc_sentences = []
        for sent in sentences:
            if len(sent) > 50 and any(word in sent.lower() for word in ['manufacturer', 'established', 'electrical', 'cable tray']):
                desc_sentences.append(sent.strip())
                if len(desc_sentences) >= 2:  # Take first 2 relevant sentences
                    break
        if desc_sentences:
            info["description"] = ". ".join(desc_sentences) + "."
    
    # Fallback to home page if about page not found
    if not info["description"]:
        home_pages = [p for p in WEBSITE_PAGES if p.get("url", "").rstrip('/') == "https://www.krpower.in"]
        if home_pages:
            home_content = home_pages[0].get("content", "")
            sentences = re.split(r'[.!?]\s+', home_content)
            for sent in sentences:
                if len(sent) > 50 and "manufacturer" in sent.lower():
                    info["description"] = sent.strip() + "."
                    break
    
    return info
