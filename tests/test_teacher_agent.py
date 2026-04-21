import sys
import os
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from unittest.mock import patch

def test_parse_valid_request():
    from agents.teacher_agent import parse_booking_request
    mock_response = '{"teacher": "Prof. A", "lab": "Lab-A", "date": "2026-05-01", "start_time": "14:00", "end_time": "16:00", "purpose": "OS lab"}'
    with patch("agents.teacher_agent.ollama", return_value=mock_response):
        result = parse_booking_request("Book Lab-A on May 1st at 2pm for 2 hours", "Prof. A")
    assert result["status"] == "parsed"
    assert result["data"]["lab"] == "Lab-A"
    assert result["data"]["start_time"] == "14:00"

def test_parse_invalid_response():
    from agents.teacher_agent import parse_booking_request
    with patch("agents.teacher_agent.ollama", return_value="Sorry I cannot help"):
        result = parse_booking_request("something", "Prof. A")
    assert result["status"] == "error"

def test_parse_extracts_json_from_markdown():
    from agents.teacher_agent import parse_booking_request
    mock_response = '```json\n{"teacher": "Prof. A", "lab": "Lab-B", "date": "2026-05-02", "start_time": "10:00", "end_time": "13:00", "purpose": "DB lab"}\n```'
    with patch("agents.teacher_agent.ollama", return_value=mock_response):
        result = parse_booking_request("Book Lab-B tomorrow at 10am for 3 hours", "Prof. A")
    assert result["status"] == "parsed"
    assert result["data"]["lab"] == "Lab-B"

def test_confirmation_message_generated():
    from agents.teacher_agent import generate_confirmation_message
    with patch("agents.teacher_agent.ollama", return_value="Your booking is confirmed!"):
        msg = generate_confirmation_message(
            {"lab": "Lab-A", "teacher": "Prof. A", "date": "2026-05-01",
             "start_time": "14:00", "end_time": "16:00", "purpose": "Test"},
            tx_id="abc123" * 10, booking_id=1
        )
    assert "confirmed" in msg.lower()
