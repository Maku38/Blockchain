import sqlite3
import os
from typing import Optional
from logger import get_logger

logger = get_logger("database")
DB_PATH = os.path.join(os.path.dirname(__file__), "labs.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # allows dict-like access
    return conn

def init_db():
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lab TEXT NOT NULL,
                teacher TEXT NOT NULL,
                date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                purpose TEXT,
                tx_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def get_bookings(lab: Optional[str] = None, date: Optional[str] = None) -> list:
    try:
        conn = get_connection()
        c = conn.cursor()
        if lab and date:
            c.execute("SELECT * FROM bookings WHERE lab=? AND date=? ORDER BY start_time", (lab, date))
        elif lab:
            c.execute("SELECT * FROM bookings WHERE lab=? ORDER BY date, start_time", (lab,))
        else:
            c.execute("SELECT * FROM bookings ORDER BY date, start_time")
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        logger.debug(f"Fetched {len(rows)} bookings")
        return rows
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch bookings: {e}")
        raise

def add_booking(lab: str, teacher: str, date: str, start_time: str,
                end_time: str, purpose: str, tx_id: Optional[str] = None) -> int:
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO bookings (lab, teacher, date, start_time, end_time, purpose, tx_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (lab, teacher, date, start_time, end_time, purpose, tx_id))
        booking_id = c.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Booking added: ID={booking_id}, lab={lab}, teacher={teacher}, date={date}, {start_time}-{end_time}")
        return booking_id
    except sqlite3.Error as e:
        logger.error(f"Failed to add booking: {e}")
        raise

def check_conflict(lab: str, date: str, start_time: str, end_time: str) -> list:
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT * FROM bookings
            WHERE lab=? AND date=?
            AND NOT (end_time <= ? OR start_time >= ?)
        ''', (lab, date, start_time, end_time))
        conflicts = [dict(row) for row in c.fetchall()]
        conn.close()
        if conflicts:
            logger.info(f"Conflict found for {lab} on {date} {start_time}-{end_time}: {len(conflicts)} conflict(s)")
        return conflicts
    except sqlite3.Error as e:
        logger.error(f"Conflict check failed: {e}")
        raise

def get_booking_by_id(booking_id: int) -> Optional[dict]:
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM bookings WHERE id=?", (booking_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch booking {booking_id}: {e}")
        raise

if __name__ == "__main__":
    init_db()
    print("Database initialized!")
