import os
from twilio.rest import Client

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = "whatsapp:+14155238886"
DEFAULT_TO = os.getenv("WHATSAPP_TO")

client = None

def _ensure():
    global client
    if client is None:
        client = Client(TWILIO_SID, TWILIO_AUTH)

def send_whatsapp_alert(message: str, to: str = None):
    _ensure()  # ✅ FIX — ensures Twilio is connected automatically

    to = to or DEFAULT_TO
    if not to:
        print("⚠️ No WHATSAPP_TO configured — WhatsApp not sent.")
        return

    try:
        msg = client.messages.create(
            from_=TWILIO_FROM,
            to=f"whatsapp:{to}",
            body=message
        )
        print("✅ WhatsApp Sent:", msg.sid)
    except Exception as e:
        print("⚠️ WhatsApp Failed:", e)
