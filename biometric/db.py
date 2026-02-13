import sqlite3
from encryption import encrypt, decrypt

DB = "biometrics.db"

# ------------------ ORIGINAL TABLES ------------------
def create_tables():
    conn = sqlite3.connect(DB)

    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        fingerprint_enc BLOB,
        face_enc BLOB,
        pin_enc BLOB
    )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS intrusions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        reason TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.close()

# ------------------ NEW TABLE (ADD ONLY) ------------------
def create_proxy_approval_table():
    conn = sqlite3.connect(DB)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS proxy_approvals (
            username TEXT,
            decision TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.close()

# ------------------ ORIGINAL FUNCTIONS ------------------
def add_user(username, fingerprint_bytes, face_bytes, pin):
    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT OR REPLACE INTO users (username, fingerprint_enc, face_enc, pin_enc) VALUES (?, ?, ?, ?)",
        (
            username,
            encrypt(fingerprint_bytes),
            encrypt(face_bytes),
            encrypt(pin.encode())
        )
    )
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect(DB)
    row = conn.execute(
        "SELECT fingerprint_enc, face_enc FROM users WHERE username=?",
        (username,)
    ).fetchone()
    conn.close()
    return (decrypt(row[0]), decrypt(row[1])) if row else None

def get_pin(username):
    conn = sqlite3.connect(DB)
    row = conn.execute(
        "SELECT pin_enc FROM users WHERE username=?",
        (username,)
    ).fetchone()
    conn.close()
    return decrypt(row[0]).decode() if row else None

def get_all_users():
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT username FROM users").fetchall()
    conn.close()
    return rows

def log_intrusion(username, reason):
    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT INTO intrusions (username, reason) VALUES (?, ?)",
        (username, reason)
    )
    conn.commit()
    conn.close()

# ------------------ NEW PROXY FUNCTIONS ------------------
def save_proxy_decision(username, decision):
    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT INTO proxy_approvals (username, decision) VALUES (?, ?)",
        (username, decision)
    )
    conn.commit()
    conn.close()

def get_latest_proxy_decision(username):
    conn = sqlite3.connect(DB)
    row = conn.execute(
        "SELECT decision FROM proxy_approvals WHERE username=? ORDER BY timestamp DESC LIMIT 1",
        (username,)
    ).fetchone()
    conn.close()
    return row[0] if row else None
