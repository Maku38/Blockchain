import requests
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database.db import check_conflict, add_booking, get_bookings

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

LABS = ["Lab-A", "Lab-B", "Lab-C"]

def ollama(prompt, system=""):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False
    }
    r = requests.post(OLLAMA_URL, json=payload)
    return r.json()["response"].strip()

def suggest_alternate_time(lab, date, start_time, end_time):
    """Suggest next available 2-hour slot after the conflict"""
    from datetime import datetime, timedelta
    fmt = "%H:%M"
    t = datetime.strptime(end_time, fmt)
    for _ in range(6):
        new_start = t.strftime(fmt)
        new_end = (t + timedelta(hours=2)).strftime(fmt)
        conflicts = check_conflict(lab, date, new_start, new_end)
        if not conflicts:
            return new_start, new_end
        t += timedelta(hours=1)
    return None, None

def process_booking_request(request: dict) -> dict:
    """
    Lab Agent: receives structured booking request, checks availability,
    negotiates if conflict, confirms booking.
    """
    lab = request.get("lab")
    teacher = request.get("teacher")
    date = request.get("date")
    start_time = request.get("start_time")
    end_time = request.get("end_time")
    purpose = request.get("purpose", "Lab session")

    # Validate lab exists
    if lab not in LABS:
        return {
            "status": "error",
            "message": f"Lab '{lab}' does not exist. Available labs: {', '.join(LABS)}"
        }

    # Check for conflicts
    conflicts = check_conflict(lab, date, start_time, end_time)

    if conflicts:
        # Try to negotiate alternate time
        alt_start, alt_end = suggest_alternate_time(lab, date, start_time, end_time)

        # Use LLM to generate a natural language negotiation message
        conflict_info = f"Lab: {lab}, Date: {date}, Requested: {start_time}-{end_time}"
        alt_info = f"Suggested alternate: {alt_start}-{alt_end}" if alt_start else "No alternate available"

        msg = ollama(
            f"You are a lab resource manager. There is a booking conflict. {conflict_info}. {alt_info}. "
            f"Write a short 1-2 sentence message to the teacher suggesting the alternate time or apologizing if none available.",
            system="You are a helpful lab resource manager. Be concise and professional."
        )

        return {
            "status": "conflict",
            "message": msg,
            "alternate_start": alt_start,
            "alternate_end": alt_end,
            "lab": lab,
            "date": date
        }

    # No conflict — confirm booking
    return {
        "status": "available",
        "message": f"Lab {lab} is available on {date} from {start_time} to {end_time}.",
        "lab": lab,
        "teacher": teacher,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "purpose": purpose
    }

def confirm_booking(booking_details: dict, tx_id: str = None) -> int:
    """Finalize booking in database with blockchain tx_id"""
    booking_id = add_booking(
        lab=booking_details["lab"],
        teacher=booking_details["teacher"],
        date=booking_details["date"],
        start_time=booking_details["start_time"],
        end_time=booking_details["end_time"],
        purpose=booking_details["purpose"],
        tx_id=tx_id
    )
    return booking_id
