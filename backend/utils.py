import re
from langdetect import detect, LangDetectException

def clean_user_text(text: str) -> str:
    """
    Remove extra spaces, newlines, HTML leftovers.
    """
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


def detect_language(text: str) -> str:
    """
    Detect user's language. Fallback to English.
    """
    try:
        lang = detect(text)
        return lang
    except LangDetectException:
        return "en"


def safe_print(*args, **kwargs):
    """
    Print without crashing if non-UTF chars appear.
    (Useful when running on Windows terminals.)
    """
    try:
        print(*args, **kwargs)
    except:
        try:
            txt = " ".join(str(a) for a in args)
            print(txt.encode("utf-8", "ignore").decode("utf-8", "ignore"))
        except:
            pass


def shorten_text(text: str, max_len: int = 500) -> str:
    """
    Limit long text blocks (e.g., RAG context previews).
    """
    if len(text) <= max_len:
        return text
    return text[:max_len] + " ..."


def merge_chat_history(history: list) -> str:
    """
    Merge chat history into a short context block for LLM.
    """
    merged = []
    for role, msg in history[-6:]:  # last 6 messages only
        merged.append(f"{role.upper()}: {msg}")
    return "\n".join(merged)
