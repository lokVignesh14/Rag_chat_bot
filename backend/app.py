# backend/app.py
import os, io, json, tempfile
from datetime import datetime
from collections import defaultdict
from typing import Dict, Any, List

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv, find_dotenv
import requests

from .rag import search, images_for_query, search_website, get_company_info
from .llm import generate_reply, generate_reply_from_website
from .mailer import send_lead_email
from .messenger import send_whatsapp_alert
from .speech import transcribe
from .models import LeadIn
from .utils import clean_user_text, detect_language

# Optional Translation
try:
    from deep_translator import GoogleTranslator
    HAVE_TR = True
except:
    HAVE_TR = False

# ---------------- Company Info Block ----------------
# Load company info from scraped website (will be populated on first use)
COMPANY_INFO = None

def _get_company_info():
    """Get company info, loading from website if not already loaded."""
    global COMPANY_INFO
    if COMPANY_INFO is None:
        COMPANY_INFO = get_company_info()
        # Fallback to default if extraction failed
        if not COMPANY_INFO.get("contact", {}).get("phone"):
            COMPANY_INFO = {
                "name": "K.R. Power Supports Pvt Ltd",
                "description": (
                    "K.R. Power is a leading manufacturer of Cable Trays, Solar Panel Mounting Structures, "
                    "Panels & Bus Ducts, and Industrial Accessories. We supply to industrial, commercial, "
                    "infrastructure and EPC contractor projects across India."
                ),
                "contact": {
                    "phone": "+91 9363105598 / +91 9363005598 / +91 9843010098 / +91 9843010033 / 0422 2535622",
                    "email": "krpower1045@gmail.com",
                    "address": "9A, School Road, Chinnavedampatti, Ganapathy, Coimbatore -641 006, Tamil Nadu, India",
                    "website": "https://www.krpower.in"
                }
            }
    return COMPANY_INFO

load_dotenv(find_dotenv(), override=True)

app = FastAPI(title="KR Power Chatbot (Catalog + Chat)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True,
)

TRANSCRIPTS: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

def now_utc():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


# -------------------- Speech-to-Text --------------------
@app.post("/stt")
async def stt(file: UploadFile = File(...)):
    try:
        suffix = os.path.splitext(file.filename or ".webm")[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            audio_path = tmp.name
        result = transcribe(audio_path)
        if isinstance(result, dict):
            return {"text": result.get("text",""), "language": result.get("language")}
        return {"text": str(result)}
    except Exception as e:
        return {"error": f"STT failed: {e}"}


# -------------------- Text-to-Speech --------------------
@app.post("/tts")
async def tts(payload: dict):
    try:
        text = (payload or {}).get("text", "").strip()
        lang = (payload or {}).get("lang", "en")
        if not text:
            return {"error": "No text provided"}

        from gtts import gTTS
        buf = io.BytesIO()
        gTTS(text=text, lang=lang if len(lang) <= 5 else "en").write_to_fp(buf)
        buf.seek(0)

        out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        with open(out.name, "wb") as f:
            f.write(buf.read())

        return FileResponse(out.name, media_type="audio/mpeg", filename="reply.mp3")
    except Exception as e:
        return {"error": f"TTS failed: {e}"}


# -------------------- MAIN CHAT LOGIC --------------------
@app.post("/chat")
async def chat(payload: dict):
    try:
        user_text = clean_user_text((payload or {}).get("message", ""))
        session_id = (payload or {}).get("session_id", "web")
        target_lang = (payload or {}).get("target_lang", "auto")

        if not user_text:
            return {"reply": "Please type your question."}

        src_lang = detect_language(user_text) or "en"
        
        # Get company info from scraped website
        company_info = _get_company_info()

        # ---- Company Auto Reply Detection ----
        lower = user_text.lower()
        if any(q in lower for q in [
            "about company", "who are you", "tell me about", "what is kr power", "your company", "about kr power"
        ]):
            # Try to get detailed info from website first
            website_pages = search_website(user_text, k=3)
            if website_pages:
                reply = generate_reply_from_website(user_text, website_pages)
                if not reply:
                    reply = (
                        f"**{company_info['name']}**\n\n"
                        f"{company_info['description']}\n\n"
                        f"📞 {company_info['contact']['phone']}\n"
                        f"✉️ {company_info['contact']['email']}\n"
                        f"📍 {company_info['contact']['address']}\n"
                        f"🌐 {company_info['contact']['website']}"
                    )
            else:
                reply = (
                    f"**{company_info['name']}**\n\n"
                    f"{company_info['description']}\n\n"
                    f"📞 {company_info['contact']['phone']}\n"
                    f"✉️ {company_info['contact']['email']}\n"
                    f"📍 {company_info['contact']['address']}\n"
                    f"🌐 {company_info['contact']['website']}"
                )
            products = []
        # ---- Location/Contact Auto Reply Detection ----
        elif any(q in lower for q in [
            "office location", "location", "address", "where are you", "where is your office",
            "contact", "contact details", "contact info", "phone", "email", "phone number",
            "office address", "company address", "headquarters", "head office", "visit",
            "come to", "reach", "reach us", "find you", "locate"
        ]):
            # Try to get contact info from website first
            website_pages = search_website(user_text, k=3)
            if website_pages:
                reply = generate_reply_from_website(user_text, website_pages)
                if not reply:
                    reply = (
                        f"📍 **Office Location & Contact Details:**\n\n"
                        f"**Address:**\n{company_info['contact']['address']}\n\n"
                        f"📞 **Phone:**\n{company_info['contact']['phone']}\n\n"
                        f"✉️ **Email:**\n{company_info['contact']['email']}\n\n"
                        f"🌐 **Website:**\n{company_info['contact']['website']}"
                    )
            else:
                reply = (
                    f"📍 **Office Location & Contact Details:**\n\n"
                    f"**Address:**\n{company_info['contact']['address']}\n\n"
                    f"📞 **Phone:**\n{company_info['contact']['phone']}\n\n"
                    f"✉️ **Email:**\n{company_info['contact']['email']}\n\n"
                    f"🌐 **Website:**\n{company_info['contact']['website']}"
                )
            products = []
        else:
            # First try product search
            products = search(user_text, k=6)
            if products:
                reply = generate_reply(user_text, products) or "Can you specify the product type?"
            else:
                # If no products found, search website content
                website_pages = search_website(user_text, k=3)
                if website_pages:
                    reply = generate_reply_from_website(user_text, website_pages)
                    if not reply:
                        reply = "I couldn't find specific information about that. Could you please rephrase your question or ask about our products, services, or company information?"
                else:
                    reply = "I couldn't find details yet. Please specify the product type (e.g., perforated cable tray 3000mm) or ask about our company, location, or services."

        # Images
        gallery = images_for_query(user_text, k=10)

        # Product Cards
        cards = []
        for p in products[:4]:
            cards.append({
                "name": p.get("name"),
                "url": p.get("url"),
                "category": p.get("category"),
                "images": p.get("images", [])[:8],
                "in_stock": p.get("stock", "Available"),
                "specs": p.get("specs", {}),
                "sizes": p.get("sizes", []),
                "reviews": p.get("reviews", []),
                "measurement": p.get("measurement")
            })

        # Translate Reply
        if target_lang != "auto" and HAVE_TR:
            try:
                reply = GoogleTranslator(source="auto", target=target_lang).translate(reply)
            except:
                pass

        TRANSCRIPTS[session_id].append({
            "ts": now_utc(), "q": user_text, "a": reply
        })

        user_turns = len([x for x in TRANSCRIPTS[session_id] if x.get("q")])
        resp = {"reply": reply, "images": gallery, "cards": cards}

        if user_turns >= 3:
            resp["request_contact"] = True

        return resp

    except Exception as e:
        return {"reply": f"⚠️ Error: {e}"}


# -------------------- LEAD FORM SUBMIT --------------------
@app.post("/lead")
async def lead(req: Request, payload: LeadIn):
    try:
        ip = req.headers.get("x-forwarded-for", req.client.host if req.client else None)
        session_id = getattr(payload, "session_id", "web")
        transcript_text = ""
        if payload.history:
            transcript_text = "\n".join(
                f"{msg.get('role', 'user').title()}: {msg.get('message','')}"
                for msg in payload.history
                if msg.get("message")
            )
        else:
            history = TRANSCRIPTS.get(session_id, [])
            transcript_text = "\n".join(
                f"[{t['ts']}] Q: {t['q']}\nA: {t['a']}\n"
                for t in reversed(history[-50:])
                if t.get("q") or t.get("a")
            )

        if not transcript_text.strip():
            transcript_text = "No conversation history captured."

        note = payload.message or ""
        send_lead_email(
            payload.name,
            payload.phone,
            payload.email,
            note,
            transcript_text
        )

        try:
            send_whatsapp_alert(f"New Lead: {payload.name} | {payload.phone}")
        except:
            pass

        return {"status": "sent"}
    except Exception as e:
        return {"error": f"Lead save failed: {e}"}
