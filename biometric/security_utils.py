import os
import datetime
import cv2
import numpy as np
import smtplib
import re
import requests

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# =====================================================
# 🔥 IMPORTANT — PUT YOUR NGROK URL HERE
# =====================================================
BASE_URL = "https://smart-atm-security-system.onrender.com"
# Example:
# BASE_URL = "https://abcd-1234.ngrok-free.app"


INTRUDER_DIR = "intruders"
os.makedirs(INTRUDER_DIR, exist_ok=True)


# =====================================================
# GET LOCATION
# =====================================================
def get_location_details():
    try:
        data = requests.get("https://ipinfo.io/json", timeout=5).json()

        return f"{data.get('city')}, {data.get('region')}, {data.get('country')} | IP: {data.get('ip')}"

    except:
        return "Location unavailable"


# =====================================================
# SAVE IMAGE
# =====================================================
def save_intruder_snapshot(image_bytes, username="unknown", reason="event"):

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{INTRUDER_DIR}/{username}_{reason}_{ts}.jpg"

    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    cv2.imwrite(path, img)

    return path


def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


# =====================================================
# 🚨 UNAUTHORIZED ACCESS EMAIL
# (IMAGE + LOCATION ONLY)
# =====================================================
def send_intrusion_alert(image_bytes, username, to_email, reason="Unauthorized Access"):

    sender = "rohithchelimilla@gmail.com"

    # 👉 Use Gmail App Password
    password = "hzqjxgvlblzglu us".replace(" ", "")

    if not to_email or not is_valid_email(to_email):
        to_email = sender

    path = save_intruder_snapshot(image_bytes, username, reason)
    location = get_location_details()

    html_body = f"""
    <html>
    <body style="font-family:Arial;">

        <h2 style="color:red;">🚨 Unauthorized ATM Access Detected</h2>

        <p><b>User:</b> {username}</p>
        <p><b>Reason:</b> {reason}</p>
        <p><b>Location:</b> {location}</p>

        <p>An unauthorized attempt was detected on your ATM account.</p>

        <p>Please review the captured image attached.</p>

        <p>If this was NOT you, contact your bank immediately.</p>

    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = f"🚨 Unauthorized ATM Access - {username}"

    msg.attach(MIMEText(html_body, "html"))

    with open(path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())

        encoders.encode_base64(part)

        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{os.path.basename(path)}"'
        )

        msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)


# =====================================================
# 🌐 REMOTE AUTHORIZATION EMAIL
# (IMAGE + LOCATION + OPEN CAMERA BUTTON)
# =====================================================
def send_remote_auth_email(image_bytes, username, to_email):

    sender = "rohithchelimilla@gmail.com"
    password = "hzqjxgvlblzglu us".replace(" ", "")

    if not to_email or not is_valid_email(to_email):
        to_email = sender

    path = save_intruder_snapshot(image_bytes, username, "remote_request")
    location = get_location_details()

    verify_link = f"{BASE_URL}/?verify_proxy=true&user={username}"
    deny_link = f"{BASE_URL}/?proxy=deny&user={username}"

    html_body = f"""
    <html>
    <body style="font-family:Arial;">

        <h2 style="color:orange;">🌐 Remote ATM Access Request</h2>

        <p><b>User:</b> {username}</p>
        <p><b>Location:</b> {location}</p>

        <p>A trusted person is requesting ATM access.</p>

        <h3>Verify Identity to Allow Access</h3>

        <a href="{verify_link}" 
        style="
            background-color:green;
            color:white;
            padding:16px 28px;
            text-decoration:none;
            font-size:18px;
            border-radius:10px;">
            📷 OPEN CAMERA & VERIFY
        </a>

        <br><br>

        <a href="{deny_link}" 
        style="
            background-color:red;
            color:white;
            padding:14px 24px;
            text-decoration:none;
            border-radius:10px;">
            ❌ DENY ACCESS
        </a>

        <p>If you did not authorize this request, please deny immediately.</p>

    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = f"Remote ATM Authorization - {username}"

    msg.attach(MIMEText(html_body, "html"))

    with open(path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())

        encoders.encode_base64(part)

        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{os.path.basename(path)}"'
        )

        msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)

