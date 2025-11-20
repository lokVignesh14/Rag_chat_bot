# streamlit_app.py
import streamlit as st
import requests
import base64

BACKEND = "http://127.0.0.1:8000"

st.set_page_config(page_title="KR Power Chatbot", layout="wide")
st.markdown("<h2 style='text-align:center'>⚡ KR Power AI Product Assistant</h2>", unsafe_allow_html=True)
st.caption("Ask about Cable Trays, Solar Structures, Panels & Bus Ducts, Accessories…")

# --- session state ---
if "messages" not in st.session_state: st.session_state.messages = []
if "msg_count" not in st.session_state: st.session_state.msg_count = 0
if "session_id" not in st.session_state: st.session_state.session_id = "web_user"
if "images" not in st.session_state: st.session_state.images = []
if "cards" not in st.session_state: st.session_state.cards = []
if "last_user_text" not in st.session_state: st.session_state.last_user_text = ""

# --- helpers ---
KR_COMPANY_INFO = {
    "name": "K.R. Power Supports Pvt Ltd",
    "description": (
        "K.R. Power is a leading manufacturer of Cable Trays, Solar Panel Mounting Structures, "
        "Panels & Bus Ducts, and Industrial Accessories. We supply to industrial, commercial, "
        "infrastructure and EPC contractor projects across India."
    ),
    "contact": {
        "phone": "+91 9363105598 / +91 9363005598+91 9843010098 / +91 9843010033 /0422 2535622",
        "email": "krpower1045@gmail.com",
        "address": "9A, School Road, Chinnavedampatti,Ganapathy, Coimbatore -641 006Tamil Nadu, India",
        "website": "https://www.krpower.in"
    }
}

def is_greeting(text: str) -> bool:
    if not text:
        return False
    t = text.strip().lower()
    return t in {"hi", "hello", "hey", "hai", "hii"} or any(t.startswith(x) for x in ["hi ", "hello ", "hey "])

def is_image_request(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    keywords = ["image", "images", "picture", "pictures", "photo", "photos", "show image", "show images", "gallery"]
    return any(k in t for k in keywords)

# --- sidebar: language & (fallback) voice upload ---
with st.sidebar:
    st.subheader("🌍 Reply Language")
    langs = [
        "auto","en","hi","ta","te","ml","kn","mr","bn","gu","pa","ur",
        "ar","de","es","fr","it","ja","ko","ru","tr","vi","zh-CN","zh-TW"
    ]
    target_lang = st.selectbox("Translate bot replies to:", langs, index=0)

    # Contact / Lead form appears after 3 user turns
    st.divider()
    if st.session_state.msg_count >= 3:
        st.subheader("📨 Send Enquiry")
        with st.form("lead_form_sidebar", clear_on_submit=True):
            name  = st.text_input("Your Name")
            phone = st.text_input("Phone Number")
            email = st.text_input("Email Address")
            note  = st.text_area("Notes (optional)", "Customer inquiry from chatbot")
            submitted = st.form_submit_button("Send Enquiry")
            if submitted:
                try:
                    history_payload = [
                        {"role": role, "message": msg}
                        for role, msg in st.session_state.messages
                        if isinstance(msg, str) and msg.strip()
                    ]
                    r = requests.post(f"{BACKEND}/lead", json={
                        "session_id": st.session_state.session_id,
                        "name": name,
                        "phone": phone,
                        "email": email,
                        "message": note or "",
                        "history": history_payload
                    })
                    js = r.json()
                    if js.get("status") == "sent":
                        st.success("✅ Sent. Our team will reach out shortly.")
                        st.session_state.msg_count = 0
                    else:
                        st.error(js.get("error") or "Failed to send.")
                except Exception as e:
                    st.error(str(e))

# --- chat history ---
for role, msg in st.session_state.messages:
    st.chat_message("user" if role == "user" else "assistant").write(msg)

# --- images section (from last response) ---
if st.session_state.images and is_image_request(st.session_state.last_user_text):
    st.subheader("🖼️ Related Images")
    cols = st.columns(4)
    valid_images = [img for img in st.session_state.images[:8] if isinstance(img, str) and img.startswith("http")]
    for i, u in enumerate(valid_images):
        with cols[i % 4]:
            try:
                st.image(u, use_container_width=True)
            except Exception:
                pass

# --- product cards (from last response) ---
if st.session_state.cards:
    st.subheader("📦 Product Matches")
    for c in st.session_state.cards:
        if not isinstance(c, dict):
            continue
        with st.expander(f"{c.get('name','Product')} — {c.get('category','')}"):
            # images
            c_images = [u for u in (c.get("images") or []) if isinstance(u, str) and u.startswith("http")]
            if c_images:
                st.markdown("**📸 Product Images:**")
                grid = st.columns(min(4, len(c_images)))
                for idx, img in enumerate(c_images[:8]):
                    with grid[idx % len(grid)]:
                        try:
                            st.image(img, use_container_width=True)
                        except Exception:
                            pass

            # stock
            stock = str(c.get("in_stock", "Available"))
            stock_badge = "🟢" if any(w in stock.lower() for w in ["yes", "available", "in stock"]) else "🟡"
            st.markdown(f"**{stock_badge} Stock Status:** {stock}")

            # sizes
            sizes = c.get("sizes") or []
            if sizes:
                st.markdown("**📏 Available Sizes:**")
                size_cols = st.columns(2)
                for i, s in enumerate(sizes):
                    label = s.get("name") if isinstance(s, dict) else str(s)
                    with size_cols[i % 2]:
                        st.write(f"- {label}")

            # specs
            specs = c.get("specs") or {}
            if specs:
                st.markdown("**⚙️ Specifications:**")
                for k, v in specs.items():
                    st.write(f"- **{k}:** {v}")

            # measurement
            measurement = c.get("measurement") or ""
            if measurement:
                st.markdown("**📐 Measurement Details:**")
                if isinstance(measurement, dict):
                    for k, v in measurement.items():
                        st.write(f"- **{k}:** {v}")
                else:
                    st.write(str(measurement))

            if c.get("url"):
                st.markdown(f"🔗 [View Full Product Page]({c['url']})", unsafe_allow_html=True)

# --- input row: chat_input + mic button ---
st.divider()
row = st.columns([1])
with row[0]:
    prompt = st.chat_input("Type your message…")

# --- handle text prompt turn ---
if prompt:
    st.session_state.messages.append(("user", prompt))
    st.session_state.msg_count += 1
    st.session_state.last_user_text = prompt

    # Greeting override for hi/hello to ensure correct first impression
    if is_greeting(prompt):
        reply = (
            f"Hi! I am the AI assistant of {KR_COMPANY_INFO['name']}. How can I help you today?\n\n"
            f"{KR_COMPANY_INFO['description']}\n\n"
            f"📞 {KR_COMPANY_INFO['contact']['phone']}\n"
            f"✉️ {KR_COMPANY_INFO['contact']['email']}\n"
            f"📍 {KR_COMPANY_INFO['contact']['address']}\n"
            f"🌐 {KR_COMPANY_INFO['contact']['website']}"
        )
        st.session_state.messages.append(("assistant", reply))
        # Also call backend to record transcript history, but ignore its reply
        try:
            _ = requests.post(f"{BACKEND}/chat", json={
                "message": prompt,
                "session_id": st.session_state.session_id,
                "target_lang": target_lang
            })
        except Exception:
            pass
        # No images/cards on simple greeting
        st.session_state.images = []
        st.session_state.cards = []
    else:
        with st.spinner("Thinking…"):
            res = requests.post(f"{BACKEND}/chat", json={
                "message": prompt,
                "session_id": st.session_state.session_id,
                "target_lang": target_lang
            }).json()

        reply = res.get("reply", "(no reply)")
        st.session_state.messages.append(("assistant", reply))

        # visuals (only keep images if user asked for them)
        imgs = [u for u in (res.get("images") or []) if isinstance(u, str) and u.startswith("http")]
        st.session_state.images = (imgs[:8] if imgs else []) if is_image_request(prompt) else []
        cards = res.get("cards") or []
        st.session_state.cards = cards if isinstance(cards, list) else []

    st.rerun()

# --- Speak last reply ---
st.divider()
btn_cols = st.columns(2)
with btn_cols[0]:
    if st.button("🔊 Speak last reply"):
        last = None
        for role, text in reversed(st.session_state.messages):
            if role == "assistant":
                last = text
                break
        if not last:
            st.warning("No bot reply yet.")
        else:
            r = requests.post(f"{BACKEND}/tts", json={
                "text": last,
                "lang": target_lang if target_lang != "auto" else "en"
            })
            if r.status_code == 200:
                b64 = base64.b64encode(r.content).decode()
                st.audio(f"data:audio/mpeg;base64,{b64}")
            else:
                st.error(r.text)

with btn_cols[1]:
    st.empty()
