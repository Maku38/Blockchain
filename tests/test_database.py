import sys
import os
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database.db import init_db, add_booking, get_bookings, check_conflict, get_booking_by_id

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test.db")
    monkeypatch.setattr("database.db.DB_PATH", test_db)
    init_db()

def test_init_db():
    assert isinstance(get_bookings(), list)

def test_add_and_get_booking():
    booking_id = add_booking("Lab-A", "Prof. Test", "2026-05-01", "10:00", "12:00", "Test session")
    assert booking_id == 1
    bookings = get_bookings()
    assert len(bookings) == 1
    assert bookings[0]["lab"] == "Lab-A"

def test_get_booking_by_id():
    booking_id = add_booking("Lab-B", "Prof. X", "2026-05-01", "14:00", "16:00", "Test")
    booking = get_booking_by_id(booking_id)
    assert booking is not None
    assert booking["lab"] == "Lab-B"

def test_get_booking_by_id_not_found():
    assert get_booking_by_id(9999) is None

def test_no_conflict_different_lab():
    add_booking("Lab-A", "Prof. A", "2026-05-01", "10:00", "12:00", "Session 1")
    assert len(check_conflict("Lab-B", "2026-05-01", "10:00", "12:00")) == 0

def test_no_conflict_different_date():
    add_booking("Lab-A", "Prof. A", "2026-05-01", "10:00", "12:00", "Session 1")
    assert len(check_conflict("Lab-A", "2026-05-02", "10:00", "12:00")) == 0

def test_no_conflict_adjacent_times():
    add_booking("Lab-A", "Prof. A", "2026-05-01", "10:00", "12:00", "Session 1")
    assert len(check_conflict("Lab-A", "2026-05-01", "12:00", "14:00")) == 0

def test_conflict_same_slot():
    add_booking("Lab-A", "Prof. A", "2026-05-01", "10:00", "12:00", "Session 1")
    assert len(check_conflict("Lab-A", "2026-05-01", "10:00", "12:00")) == 1

def test_conflict_overlapping():
    add_booking("Lab-A", "Prof. A", "2026-05-01", "10:00", "12:00", "Session 1")
    assert len(check_conflict("Lab-A", "2026-05-01", "11:00", "13:00")) == 1

def test_conflict_contained():
    add_booking("Lab-A", "Prof. A", "2026-05-01", "10:00", "14:00", "Long session")
    assert len(check_conflict("Lab-A", "2026-05-01", "11:00", "13:00")) == 1

def test_get_bookings_filter_by_lab():
    add_booking("Lab-A", "Prof. A", "2026-05-01", "10:00", "12:00", "A session")
    add_booking("Lab-B", "Prof. B", "2026-05-01", "10:00", "12:00", "B session")
    lab_a = get_bookings(lab="Lab-A")
    assert len(lab_a) == 1
    assert lab_a[0]["lab"] == "Lab-A"

def test_booking_with_tx_id():
    fake_tx = "abc123def456" * 5
    booking_id = add_booking("Lab-C", "Prof. Z", "2026-05-01", "09:00", "11:00", "Blockchain test", tx_id=fake_tx)
    booking = get_booking_by_id(booking_id)
    assert booking["tx_id"] == fake_tx
