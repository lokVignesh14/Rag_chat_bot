# backend/mailer.py

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv, find_dotenv
from datetime import datetime   # ✅ ADD THIS

load_dotenv(find_dotenv(), override=True)

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
OFFICE_EMAIL = os.getenv("OFFICE_EMAIL")

load_dotenv(find_dotenv(), override=True)

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
OFFICE_EMAIL = os.getenv("OFFICE_EMAIL")


def send_lead_email(name, phone, email, message, chat_history):
    body = f"""
🟢 NEW CUSTOMER INQUIRY FROM WEBSITE CHATBOT

Name: {name}
Email: {email}
Phone: {phone}

---------------------------------------
🗣️ Customer Requirement:
---------------------------------------
{message}

---------------------------------------
💬 Conversation History:
---------------------------------------
{chat_history}

---------------------------------------
Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = OFFICE_EMAIL
    msg["Subject"] = f"KR Power - New Lead from Chatbot ({name})"
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, OFFICE_EMAIL, msg.as_string())
        server.quit()
        print("✅ EMAIL SENT")
    except Exception as e:
        print("❌ EMAIL FAILED:", e)
