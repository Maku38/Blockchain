import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "labs.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
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

def get_bookings(lab=None, date=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if lab and date:
        c.execute("SELECT * FROM bookings WHERE lab=? AND date=?", (lab, date))
    elif lab:
        c.execute("SELECT * FROM bookings WHERE lab=?", (lab,))
    else:
        c.execute("SELECT * FROM bookings ORDER BY date, start_time")
    rows = c.fetchall()
    conn.close()
    return rows

def add_booking(lab, teacher, date, start_time, end_time, purpose, tx_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO bookings (lab, teacher, date, start_time, end_time, purpose, tx_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (lab, teacher, date, start_time, end_time, purpose, tx_id))
    booking_id = c.lastrowid
    conn.commit()
    conn.close()
    return booking_id

def check_conflict(lab, date, start_time, end_time):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT * FROM bookings 
        WHERE lab=? AND date=?
        AND NOT (end_time <= ? OR start_time >= ?)
    ''', (lab, date, start_time, end_time))
    conflicts = c.fetchall()
    conn.close()
    return conflicts

if __name__ == "__main__":
    init_db()
    print("Database initialized!")
