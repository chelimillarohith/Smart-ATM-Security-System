import streamlit as st
import sqlite3
import time
import os

# =====================================================
# ⭐ SAFE IMPORTS (Cloud Compatible)
# =====================================================

# Face Recognition (Cloud cannot install dlib)
try:
    from face_recog import verify_face, register_face, liveness_detection
    FACE_AVAILABLE = True
except:
    FACE_AVAILABLE = False

# Fingerprint Recognition
try:
    from fingerprint_recog import verify_fingerprint
    FP_AVAILABLE = True
except:
    FP_AVAILABLE = False

# DB + Security (always available)
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

# =====================================================
# INITIAL SETUP
# =====================================================

DB = "biometrics.db"
create_tables()
create_proxy_approval_table()

st.set_page_config(page_title="AI ATM Security System", layout="wide", page_icon="💳")

# =====================================================
# INFO BANNER (Cloud Demo Notice)
# =====================================================

if not FACE_AVAILABLE or not FP_AVAILABLE:
    st.warning("⚠️ Running in Cloud Demo Mode — Biometric AI modules are disabled.")

# =====================================================
# SIDEBAR MENU
# =====================================================

menu = st.sidebar.radio(
    "Select Role",
    ["Register User", "User Login", "Remote Authentication", "Admin Panel"]
)

# =====================================================
# REGISTER USER
# =====================================================

if menu == "Register User":

    st.title("📝 Register User")

    username = st.text_input("Username")
    email = st.text_input("Email")
    pin = st.text_input("4-digit PIN", type="password")

    if st.button("Register"):

        if not username or not email or not pin:
            st.warning("Fill all fields.")
        else:
            # Demo Mode Safe Registration
            add_user(username, b"demo_fp", b"demo_face", pin)
            st.success("User Registered (Demo Mode)")


# =====================================================
# USER LOGIN
# =====================================================

elif menu == "User Login":

    st.title("💳 Secure ATM Login")

    username = st.text_input("Username")
    pin = st.text_input("PIN", type="password")
    email = st.text_input("Registered Email")

    if username and pin:

        stored_pin = get_pin(username)

        if not stored_pin:
            st.error("Invalid credentials")
            st.stop()

        if stored_pin != pin:
            st.error("Invalid credentials")
            st.stop()

        user = get_user(username)

        if user:
            stored_fp, stored_face = user

            # ===============================
            # Fingerprint Verification
            # ===============================
            if FP_AVAILABLE:
                fp_file = st.file_uploader("Upload Fingerprint")

                if fp_file and verify_fingerprint(stored_fp, fp_file.read()):
                    st.success("Fingerprint Verified")
                elif fp_file:
                    st.error("Fingerprint Failed")
            else:
                st.info("Fingerprint Disabled (Cloud Demo)")

            # ===============================
            # Face Verification
            # ===============================
            if FACE_AVAILABLE:
                face_capture = st.camera_input("Capture Face")

                if face_capture:
                    live_face = face_capture.getvalue()

                    if verify_face(stored_face, live_face) and liveness_detection(live_face):
                        st.success("✅ ACCESS GRANTED")
                        st.radio("Transaction", ["Withdraw", "Deposit", "Balance"])
                    else:
                        st.error("Face verification failed")
            else:
                st.success("✅ ACCESS GRANTED (Demo Mode)")
                st.radio("Transaction", ["Withdraw", "Deposit", "Balance"])


# =====================================================
# REMOTE AUTHENTICATION
# =====================================================

elif menu == "Remote Authentication":

    st.title("🌐 Remote Transaction Authorization")

    username = st.text_input("Enter Username:")
    entered_pin = st.text_input("Enter 4-digit PIN:", type="password")
    email = st.text_input("Enter Registered Email:")

    if st.button("Send Email Authorization"):

        stored_pin = get_pin(username)

        if not stored_pin:
            st.error("Invalid credentials.")
            st.stop()

        if entered_pin != stored_pin:
            st.error("Incorrect PIN.")
            log_intrusion(username, "remote_invalid_pin")
            st.stop()

        clear_proxy_decisions(username)

        # Demo image instead of camera
        send_remote_auth_email(b"demo_image", username, email)

        st.success("Authorization email sent!")
        st.info("Waiting for account holder approval...")

        st_autorefresh(interval=2000, key="approval_refresh")

        decision = get_latest_proxy_decision(username)

        if decision == "ALLOW":
            st.success("✅ REMOTE AUTHORIZATION SUCCESSFUL!")
            st.balloons()

        elif decision == "DENY":
            st.error("❌ REMOTE AUTHORIZATION DENIED!")

        else:
            st.warning("⏳ Awaiting approval...")


# =====================================================
# ADMIN PANEL
# =====================================================

elif menu == "Admin Panel":

    st.title("👩‍💼 Admin Dashboard")

    pwd = st.text_input("Admin Password", type="password")

    if pwd == "admin123":

        st.subheader("Users")
        st.table(get_all_users())

        conn = sqlite3.connect(DB)

        intrusions = conn.execute(
            "SELECT username, reason, timestamp FROM intrusions"
        ).fetchall()

        proxy = conn.execute(
            "SELECT username, decision, timestamp FROM proxy_approvals"
        ).fetchall()

        conn.close()

        st.subheader("🚨 Intrusion Logs")
        st.table(intrusions)

        st.subheader("🌐 Remote Authorization Logs")
        st.table(proxy)

    else:
        st.warning("Unauthorized Access.")
