import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
wa_from = os.getenv("TWILIO_WHATSAPP_FROM")
wa_to = os.getenv("OFFICE_WHATSAPP_TO")

client = Client(account_sid, auth_token)

message = client.messages.create(
    body="✅ KR Power Chatbot WhatsApp Test Message",
    from_=wa_from,
    to=wa_to
)

print("Message SID:", message.sid)
