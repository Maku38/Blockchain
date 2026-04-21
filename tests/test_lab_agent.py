import sys
import os
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from unittest.mock import patch
from database.db import init_db, add_booking

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test.db")
    monkeypatch.setattr("database.db.DB_PATH", test_db)
    init_db()

def test_invalid_lab():
    from agents.lab_agent import process_booking_request
    result = process_booking_request({
        "lab": "Lab-Z", "teacher": "Prof. A",
        "date": "2026-05-01", "start_time": "10:00",
        "end_time": "12:00", "purpose": "Test"
    })
    assert result["status"] == "error"
    assert "does not exist" in result["message"]

def test_available_slot():
    from agents.lab_agent import process_booking_request
    result = process_booking_request({
        "lab": "Lab-A", "teacher": "Prof. A",
        "date": "2026-05-01", "start_time": "10:00",
        "end_time": "12:00", "purpose": "Test"
    })
    assert result["status"] == "available"
    assert result["lab"] == "Lab-A"

def test_conflict_slot():
    from agents.lab_agent import process_booking_request
    add_booking("Lab-A", "Prof. A", "2026-05-01", "10:00", "12:00", "Existing")
    with patch("agents.lab_agent.ollama", return_value="Sorry, conflict. Try 12:00-14:00."):
        result = process_booking_request({
            "lab": "Lab-A", "teacher": "Prof. B",
            "date": "2026-05-01", "start_time": "10:00",
            "end_time": "12:00", "purpose": "New session"
        })
    assert result["status"] == "conflict"
    assert result["alternate_start"] is not None

def test_alternate_time_suggestion():
    from agents.lab_agent import suggest_alternate_time
    add_booking("Lab-A", "Prof. A", "2026-05-01", "10:00", "12:00", "Existing")
    alt_start, alt_end = suggest_alternate_time("Lab-A", "2026-05-01", "10:00", "12:00")
    assert alt_start == "12:00"
    assert alt_end == "14:00"

def test_confirm_booking():
    from agents.lab_agent import confirm_booking
    booking_id = confirm_booking({
        "lab": "Lab-A", "teacher": "Prof. A",
        "date": "2026-05-01", "start_time": "10:00",
        "end_time": "12:00", "purpose": "Test"
    }, tx_id="faketxid123")
    assert booking_id == 1
