# backend/llm.py
from typing import List, Dict, Any

STOP_WORDS = {
    "about", "the", "and", "for", "with", "from", "into", "that", "this",
    "what", "your", "you", "are", "who", "tell", "me", "our", "us", "in",
    "on", "to", "of", "is", "it", "a", "an", "please", "could", "can"
}


def _split_sentences(text: str):
    import re
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]


def _effective_query_words(user_text: str) -> List[str]:
    import re
    words = [w.strip() for w in re.split(r"\W+", user_text.lower()) if w]
    return [w for w in words if len(w) > 2 and w not in STOP_WORDS]


def _page_relevance_score(page: Dict[str, Any], query_words: List[str]) -> int:
    combined = f"{page.get('title', '')} {page.get('content', '')}".lower()
    total_words = len(query_words)
    score = 0
    for idx, word in enumerate(query_words):
        if word and word in combined:
            score += (total_words - idx)
    return score


def generate_reply_from_website(user_text: str, pages: List[Dict[str, Any]]) -> str:
    """Generate reply from website page content."""
    if not pages:
        return None

    import re

    query_words = _effective_query_words(user_text)
    scored_pages = []

    for idx, page in enumerate(pages):
        score = _page_relevance_score(page, query_words)
        combined_tokens = {
            token for token in re.split(r"\W+", (page.get("title", "") + " " + page.get("content", "")).lower())
            if token
        }
        matched_words = [w for w in query_words if w in combined_tokens]
        scored_pages.append((score, len(matched_words), idx, page, matched_words))

    scored_pages.sort(key=lambda x: (-x[0], -x[1], x[2]))

    selected = [entry for entry in scored_pages if entry[0] > 0]
    if not selected:
        selected = scored_pages[:1]
    else:
        selected = selected[:2]  # combine up to two relevant pages

    lines = []
    used_sources = set()

    for score, _, _, page, matched_words in selected:
        title = page.get("title", "")
        content = page.get("content", "")
        url = page.get("url", "")

        sentences = _split_sentences(content)
        relevant_sentences = []

        for sent in sentences:
            sent_lower = sent.lower()
            if any(word in sent_lower for word in matched_words):
                relevant_sentences.append(sent.strip())
            elif len(sent.strip()) > 120 and len(relevant_sentences) < 3:
                relevant_sentences.append(sent.strip())

            if len(relevant_sentences) >= 4:
                break

        if not relevant_sentences and sentences:
            relevant_sentences.extend(sentences[:3])

        if title:
            lines.append(f"**{title}**")
            lines.append("")

        if relevant_sentences:
            lines.append("\n".join(relevant_sentences))
        elif content:
            lines.append(content[:500] + ("..." if len(content) > 500 else ""))

        if url and url not in used_sources:
            lines.append("")
            lines.append(f"📄 Source: {url}")
            used_sources.add(url)

        lines.append("")  # spacer between sections

    response = "\n".join(line for line in lines if line is not None).strip()
    return response or None


def _mk_specs_table(p: Dict[str, Any]) -> str:
    lines = []
    specs = p.get("specs", {}) or {}
    for k, v in specs.items():
        lines.append(f"- {k}: {v}")
    if not lines:
        return "- (No specs listed)"
    return "\n".join(lines)

def _mk_sizes(p: Dict[str, Any]) -> str:
    sizes = p.get("sizes") or []
    if not sizes:
        return "Not specified."
    return ", ".join([s if isinstance(s, str) else str(s) for s in sizes])

def _short_reviews(p: Dict[str, Any], n=2) -> str:
    rev = p.get("reviews") or []
    if not rev:
        return "No customer reviews available."
    return "\n".join([f"• {r}" for r in rev[:n]])

def generate_reply(user_text: str, products: List[Dict[str, Any]]) -> str:
    """
    Compose a helpful, on-brand answer from the product DB.
    """
    if not products:
        return "I couldn’t find details yet. Please specify the product type (e.g., perforated cable tray 3000mm)."

    wants_images = any(w in user_text.lower() for w in ["image", "pic", "photo", "gallery", "show me"])
    wants_sizes = any(w in user_text.lower() for w in ["size", "sizes", "dimension", "dimensions"])
    wants_specs = any(w in user_text.lower() for w in ["spec", "specs", "specification", "specifications"])

    top = products[0]
    name = top.get("name","Product")
    cat  = top.get("category","")
    url  = top.get("url","")

    lines = []
    lines.append(f"**{name}** — {cat}")
    if wants_specs or not wants_images:
        lines.append("")
        lines.append("**Key Specifications**")
        lines.append(_mk_specs_table(top))

    if wants_sizes or not wants_images:
        lines.append("")
        lines.append("**Available Sizes**")
        lines.append(_mk_sizes(top))

    meas = top.get("measurement")
    if meas:
        lines.append("")
        lines.append("**Measurement Guidance**")
        lines.append(meas)

    stock = top.get("stock","Available")
    lines.append("")
    lines.append(f"**Stock Status:** {stock}")

    lines.append("")
    lines.append("**Customer Feedback (highlights)**")
    lines.append(_short_reviews(top))

    if url:
        lines.append("")
        lines.append(f"Product page: {url}")

    # If multiple matches, add a hint
    if len(products) > 1 and not wants_images:
        alts = [p.get("name") for p in products[1:4]]
        alts = [a for a in alts if a]
        if alts:
            lines.append("")
            lines.append("You may also be interested in: " + "; ".join(alts))

    return "\n".join(lines)
