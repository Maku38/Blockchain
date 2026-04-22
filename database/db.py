import sqlite3
import os
from typing import Optional
from logger import get_logger

logger = get_logger("database")
DB_PATH = os.path.join(os.path.dirname(__file__), "labs.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
                role TEXT DEFAULT 'teacher',
                date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                purpose TEXT,
                status TEXT DEFAULT 'confirmed',
                tx_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lab TEXT NOT NULL,
                item_type TEXT NOT NULL,
                item_name TEXT NOT NULL,
                total INTEGER DEFAULT 1,
                available INTEGER DEFAULT 1,
                status TEXT DEFAULT 'working',
                notes TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS inventory_bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER,
                inventory_id INTEGER,
                quantity INTEGER DEFAULT 1,
                FOREIGN KEY(booking_id) REFERENCES bookings(id),
                FOREIGN KEY(inventory_id) REFERENCES inventory(id)
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS hod_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                booking_id INTEGER,
                reason TEXT,
                performed_by TEXT DEFAULT 'HOD',
                tx_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        _seed_inventory()
    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def _seed_inventory():
    """Seed default inventory if empty"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM inventory")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    items = [
        # Lab-A
        ("Lab-A", "workstation", "Dell Workstation", 20, 20, "working", None),
        ("Lab-A", "projector",   "Epson Projector",   1,  1, "working", None),
        ("Lab-A", "software",    "MATLAB License",   20, 20, "working", None),
        # Lab-B
        ("Lab-B", "workstation", "HP Workstation",   15, 15, "working", None),
        ("Lab-B", "projector",   "BenQ Projector",    1,  1, "working", None),
        ("Lab-B", "software",    "Cisco Packet Tracer",15,15,"working", None),
        # Lab-C
        ("Lab-C", "workstation", "Lenovo Workstation",10,10, "working", None),
        ("Lab-C", "projector",   "Sony Projector",    1,  1, "working", "Under maintenance"),
        ("Lab-C", "software",    "Visual Studio",    10, 10, "working", None),
        # Classrooms
        ("Classroom-1", "projector", "Laser Projector", 1, 1, "working", None),
        ("Classroom-2", "projector", "HD Projector",    1, 1, "working", None),
    ]
    c.executemany('''
        INSERT INTO inventory (lab, item_type, item_name, total, available, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', items)
    conn.commit()
    conn.close()
    logger.info("Inventory seeded with default items")

# ─── Bookings ────────────────────────────────────────────────────────────────

def get_bookings(lab=None, date=None, role=None) -> list:
    try:
        conn = get_connection()
        c = conn.cursor()
        query = "SELECT * FROM bookings WHERE 1=1"
        params = []
        if lab:
            query += " AND lab=?"; params.append(lab)
        if date:
            query += " AND date=?"; params.append(date)
        if role:
            query += " AND role=?"; params.append(role)
        query += " ORDER BY date, start_time"
        c.execute(query, params)
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return rows
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch bookings: {e}")
        raise

def add_booking(lab, teacher, date, start_time, end_time,
                purpose, tx_id=None, role="teacher", status="confirmed") -> int:
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO bookings
            (lab, teacher, role, date, start_time, end_time, purpose, status, tx_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (lab, teacher, role, date, start_time, end_time, purpose, status, tx_id))
        booking_id = c.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Booking #{booking_id}: {lab} | {teacher} ({role}) | {date} {start_time}-{end_time}")
        return booking_id
    except sqlite3.Error as e:
        logger.error(f"Failed to add booking: {e}")
        raise

def update_booking_status(booking_id: int, status: str, tx_id: str = None):
    try:
        conn = get_connection()
        c = conn.cursor()
        if tx_id:
            c.execute("UPDATE bookings SET status=?, tx_id=? WHERE id=?", (status, tx_id, booking_id))
        else:
            c.execute("UPDATE bookings SET status=? WHERE id=?", (status, booking_id))
        conn.commit()
        conn.close()
        logger.info(f"Booking #{booking_id} status → {status}")
    except sqlite3.Error as e:
        logger.error(f"Failed to update booking: {e}")
        raise

def check_conflict(lab, date, start_time, end_time) -> list:
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT * FROM bookings
            WHERE lab=? AND date=? AND status != 'cancelled'
            AND NOT (end_time <= ? OR start_time >= ?)
        ''', (lab, date, start_time, end_time))
        conflicts = [dict(row) for row in c.fetchall()]
        conn.close()
        if conflicts:
            logger.info(f"Conflict in {lab} on {date} {start_time}-{end_time}: {len(conflicts)} conflict(s)")
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

# ─── Inventory ───────────────────────────────────────────────────────────────

def get_inventory(lab=None, item_type=None) -> list:
    try:
        conn = get_connection()
        c = conn.cursor()
        query = "SELECT * FROM inventory WHERE 1=1"
        params = []
        if lab:
            query += " AND lab=?"; params.append(lab)
        if item_type:
            query += " AND item_type=?"; params.append(item_type)
        c.execute(query, params)
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return rows
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch inventory: {e}")
        raise

def update_inventory_availability(inventory_id: int, delta: int):
    """delta = -1 to reserve, +1 to release"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            UPDATE inventory SET available = available + ?,
            updated_at = CURRENT_TIMESTAMP WHERE id=?
        ''', (delta, inventory_id))
        conn.commit()
        conn.close()
        logger.info(f"Inventory #{inventory_id} availability changed by {delta}")
    except sqlite3.Error as e:
        logger.error(f"Failed to update inventory: {e}")
        raise

# ─── HOD Actions ─────────────────────────────────────────────────────────────

def add_hod_action(action, booking_id=None, reason=None, tx_id=None) -> int:
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO hod_actions (action, booking_id, reason, tx_id)
            VALUES (?, ?, ?, ?)
        ''', (action, booking_id, reason, tx_id))
        action_id = c.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"HOD action #{action_id}: {action} on booking #{booking_id}")
        return action_id
    except sqlite3.Error as e:
        logger.error(f"Failed to add HOD action: {e}")
        raise

def get_hod_actions() -> list:
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM hod_actions ORDER BY created_at DESC")
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return rows
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch HOD actions: {e}")
        raise

if __name__ == "__main__":
    init_db()
    print("Database initialized!")
