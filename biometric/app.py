import streamlit as st
import sqlite3
import time
from fingerprint_recog import verify_fingerprint
from face_recog import verify_face, register_face, liveness_detection
from db import (
    create_tables, add_user, get_user, get_all_users,
    log_intrusion, get_pin,
    create_proxy_approval_table,
    save_proxy_decision,
    get_latest_proxy_decision
)
from security_utils import send_intrusion_alert, send_remote_auth_email
import cv2
import os


DB = "biometrics.db"
create_tables()
create_proxy_approval_table()

st.set_page_config(page_title="AI ATM Security System", layout="wide", page_icon="💳")

query_params = st.experimental_get_query_params()


# =========================================================
# ✅ HANDLE ALLOW / DENY FROM EMAIL
# =========================================================
if "proxy" in query_params and "user" in query_params:

    decision = query_params["proxy"][0].upper()
    user = query_params["user"][0]

    if decision in ["ALLOW", "DENY"]:
        save_proxy_decision(user, decision)

        if decision == "ALLOW":
            st.success("✅ Remote Access Approved.")
        else:
            st.error("❌ Remote Access Denied.")

        st.stop()


# =========================================================
# ✅ HANDLE CAMERA VERIFY LINK
# =========================================================
if "verify_proxy" in query_params and "user" in query_params:

    verify_user = query_params["user"][0]

    st.title("📷 Remote Face Verification")

    face_capture = st.camera_input("Show your face")

    if face_capture:

        live_face = face_capture.getvalue()
        user_data = get_user(verify_user)

        if user_data:
            stored_fp, stored_face = user_data

            if verify_face(stored_face, live_face) and liveness_detection(live_face):
                save_proxy_decision(verify_user, "ALLOW")
                st.success("✅ Identity Verified. Access Approved.")
            else:
                save_proxy_decision(verify_user, "DENY")
                st.error("❌ Face verification failed.")

        st.stop()


# =========================================================
# SIDEBAR
# =========================================================
menu = st.sidebar.radio(
    "Select Role",
    ["Register User", "User Login", "Remote Authentication", "Admin Panel"]
)


# =========================================================
# CAMERA FUNCTION (STABLE)
# =========================================================
def try_auto_capture_one_frame():

    try:
        if os.name == "nt":
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            return None

        time.sleep(1)

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return None

        ret2, encimg = cv2.imencode('.jpg', frame)
        return encimg.tobytes() if ret2 else None

    except:
        return None


# =========================================================
# REGISTER USER
# =========================================================
if menu == "Register User":

    st.title("📝 Register New User")

    username = st.text_input("Username")
    email = st.text_input("Email")
    fingerprint = st.file_uploader("Upload Fingerprint")
    face = st.camera_input("Capture Face")
    pin = st.text_input("4-digit PIN", type="password")

    if st.button("Register"):

        if not all([username, email, fingerprint, face, pin]):
            st.warning("Fill all fields.")

        elif len(pin) != 4 or not pin.isdigit():
            st.error("PIN must be exactly 4 digits.")

        else:
            face_enc = register_face(face.getvalue())
            add_user(username, fingerprint.read(), face_enc, pin)

            st.success("✅ User Registered Successfully!")


# =========================================================
# USER LOGIN
# =========================================================
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

            img = try_auto_capture_one_frame()
            if img:
                send_intrusion_alert(img, username, email, "Invalid PIN")

            st.stop()

        user = get_user(username)

        if user:
            stored_fp, stored_face = user

            fp_file = st.file_uploader("Upload Fingerprint")

            if fp_file and verify_fingerprint(stored_fp, fp_file.read()):

                face_capture = st.camera_input("Capture Face")

                if face_capture:

                    live_face = face_capture.getvalue()

                    if verify_face(stored_face, live_face) and liveness_detection(live_face):

                        st.success("✅ ACCESS GRANTED")
                        st.radio("Transaction", ["Withdraw", "Deposit", "Balance"])

                    else:
                        st.error("Face verification failed")

                        img = try_auto_capture_one_frame()
                        if img:
                            send_intrusion_alert(img, username, email, "Face Failure")

            elif fp_file:
                st.error("Fingerprint mismatch")

                img = try_auto_capture_one_frame()
                if img:
                    send_intrusion_alert(img, username, email, "Fingerprint Failure")


# =========================================================
# ⭐ REMOTE AUTHENTICATION WITH LIVE STATUS
# =========================================================
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

        img = try_auto_capture_one_frame()

        if img:
            send_remote_auth_email(img, username, email)

            st.success("✅ Authorization email sent!")
            status_box = st.empty()

            # ⭐ LIVE POLLING
            while True:

                decision = get_latest_proxy_decision(username)

                if decision == "ALLOW":
                    status_box.success("✅ REMOTE AUTHORIZATION SUCCESSFUL!")
                    st.balloons()
                    break

                elif decision == "DENY":
                    status_box.error("❌ REMOTE AUTHORIZATION DENIED!")
                    break

                else:
                    status_box.warning("⏳ Waiting for approval...")
                    time.sleep(3)
                    st.experimental_rerun()

        else:
            st.error("Camera not available.")


# =========================================================
# ADMIN PANEL
# =========================================================
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
