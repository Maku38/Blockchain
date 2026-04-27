import sqlite3
import os
import bcrypt
from logger import get_logger

logger = get_logger("users")
DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_users_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            csc_address TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Users DB initialized")

def create_user(username: str, password: str, csc_address: str) -> dict:
    try:
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO users (username, password_hash, csc_address)
            VALUES (?, ?, ?)
        ''', (username, password_hash, csc_address))
        user_id = c.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"User created: {username} → {csc_address}")
        return {"id": user_id, "username": username, "csc_address": csc_address}
    except sqlite3.IntegrityError:
        raise ValueError(f"Username '{username}' already exists")

def get_user(username: str) -> dict | None:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def verify_password(username: str, password: str) -> dict | None:
    user = get_user(username)
    if not user:
        return None
    if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return user
    return None

def get_all_users() -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, csc_address, created_at FROM users")
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows
