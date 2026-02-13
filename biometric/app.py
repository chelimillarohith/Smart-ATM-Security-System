import streamlit as st
import sqlite3
import time

from face_recog import verify_face, register_face, liveness_detection, FACE_AVAILABLE
from fingerprint_recog import verify_fingerprint, FP_AVAILABLE

from db import (
    create_tables, add_user, get_user, get_all_users,
    log_intrusion, get_pin,
    create_proxy_approval_table,
    save_proxy_decision,
    get_latest_proxy_decision,
    clear_proxy_decisions
)

from security_utils import send_intrusion_alert, send_remote_auth_email
from streamlit_autorefresh import st_autorefresh

DB = "biometrics.db"
create_tables()
create_proxy_approval_table()

st.set_page_config(page_title="AI ATM Security System", layout="wide")

# ================= INFO =================
if not FACE_AVAILABLE or not FP_AVAILABLE:
    st.warning("⚠️ Cloud Demo Mode — Biometric AI disabled.")

menu = st.sidebar.radio(
    "Select Role",
    ["Register User", "User Login", "Remote Authentication", "Admin Panel"]
)

# ================= REGISTER =================
if menu == "Register User":

    st.title("Register User")

    username = st.text_input("Username")
    email = st.text_input("Email")
    pin = st.text_input("PIN", type="password")

    if st.button("Register"):

        if username and email and pin:
            add_user(username, b"demo_fp", b"demo_face", pin)
            st.success("Registered (Demo Mode)")

# ================= LOGIN =================
elif menu == "User Login":

    st.title("User Login")

    username = st.text_input("Username")
    pin = st.text_input("PIN", type="password")

    if username and pin:

        stored_pin = get_pin(username)

        if stored_pin != pin:
            st.error("Invalid credentials")
        else:
            if FACE_AVAILABLE:
                st.camera_input("Capture Face")
            else:
                st.success("ACCESS GRANTED (Demo Mode)")
                st.radio("Transaction", ["Withdraw", "Deposit", "Balance"])

# ================= REMOTE =================
elif menu == "Remote Authentication":

    st.title("Remote Authentication")

    username = st.text_input("Username")
    pin = st.text_input("PIN", type="password")
    email = st.text_input("Email")

    if st.button("Send Email"):

        stored_pin = get_pin(username)

        if stored_pin == pin:
            clear_proxy_decisions(username)
            send_remote_auth_email(b"demo", username, email)

    st_autorefresh(interval=2000)

    decision = get_latest_proxy_decision(username)

    if decision == "ALLOW":
        st.success("REMOTE ACCESS GRANTED")

    elif decision == "DENY":
        st.error("REMOTE ACCESS DENIED")

# ================= ADMIN =================
elif menu == "Admin Panel":

    pwd = st.text_input("Admin Password", type="password")

    if pwd == "admin123":
        st.table(get_all_users())
