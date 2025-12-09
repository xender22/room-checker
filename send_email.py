from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from email_data import EmailData


print("Loading environment variables...")
load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
TO_EMAIL = os.getenv("TO_EMAIL")
TARGET_URL = os.getenv("TARGET_URL")
ROOM_NO = os.getenv("ROOM_NO")
FIRESTORE_API_KEY = os.getenv("FIRESTORE_API_KEY")

# Firebase DB Load
cred = credentials.Certificate(FIRESTORE_API_KEY)
firebase_admin.initialize_app(cred)
db = firestore.client()

def set_email_status(status: bool):
    db.collection("functions").document("room_availability").set({
        "email_sent": status,
        "timestamp": datetime.now()
    })

def get_email_status():
    doc = db.collection("functions").document("room_availability").get()
    return doc.to_dict().get("email_sent")

def check_room_availability():
    print("Checking room availability...")
    response = requests.get(TARGET_URL, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    headers = soup.find_all("div", class_="ext-spheader")

    for header in headers:
        h3 = header.find("h3")
        if not h3:
            continue
        room_no = h3.text.strip()

        if room_no == ROOM_NO:
            print(header)
            full_span = header.find("span", string=lambda t: t and "Full" in t)
            print(full_span)
            if full_span:
                print("Room is full!")
                return False
            else:
                print("Room is available!")
                return True

    return False

def send_email(email_data: EmailData):
    response = False
    print("Sending test email...")

    msg = MIMEMultipart()
    msg["From"] = email_data.from_address
    msg["To"] = email_data.to_address
    msg["Subject"] = email_data.subject
    msg.attach(MIMEText(email_data.body, "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        print("Email sent!")
        response = True

    return response


if __name__ == "__main__":
    print("Starting script...")
    email_sent = get_email_status()
    room_available = check_room_availability()
    email_data = EmailData(SMTP_USER, TO_EMAIL)

# If the room is available and the email hasn't been sent yet, send the email'
    if room_available and not email_sent:
        email_data.subject = "Room available!"
        email_data.body = f"Room {ROOM_NO} is available! Book now at: {TARGET_URL}"
        email_sent = send_email(email_data)
        set_email_status(email_sent)
        print("Email sent:", get_email_status())

# If the room is not available and the email has been sent, set the email status to false.
    if not room_available and email_sent:
        email_data.subject = "Room taken!"
        email_data.body = (
            f"Room {ROOM_NO} was taken in the meantime, "
            "the service will check and notify you again when it's available!"
        )
        email_sent = send_email(email_data)
        # We want to reset the status, so it will email us when the room is available again.
        set_email_status(not email_sent)
        print("Email sent should be False:", get_email_status())

    print("End of script.")