import requests
import json
from logger import get_logger
from database.db import (get_bookings, update_booking_status,
                          add_hod_action, get_hod_actions, check_conflict)

logger = get_logger("hod_agent")
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

def ollama(prompt, system=""):
    payload = {"model": MODEL, "prompt": prompt, "system": system, "stream": False}
    r = requests.post(OLLAMA_URL, json=payload, timeout=60)
    return r.json()["response"].strip()

def evaluate_override(student_booking: dict, conflicting_booking: dict) -> dict:
    """
    HOD Agent evaluates whether to override a student booking in favor of a teacher,
    or to protect a student booking from being bumped.
    Returns decision with reasoning.
    """
    prompt = f"""You are the Head of Department making a scheduling decision.

Student booking:
- Student: {student_booking.get('teacher')}
- Lab: {student_booking.get('lab')}
- Date: {student_booking.get('date')} {student_booking.get('start_time')}-{student_booking.get('end_time')}
- Purpose: {student_booking.get('purpose')}

Conflicting booking:
- Person: {conflicting_booking.get('teacher')}
- Role: {conflicting_booking.get('role', 'teacher')}
- Purpose: {conflicting_booking.get('purpose')}

Should the student booking be cancelled to accommodate the conflicting booking?
Reply with ONLY a JSON object like:
{{"decision": "override" or "protect", "reason": "one sentence reason"}}"""

    response = ollama(prompt, system="You are a fair HOD. Teachers get priority over students for academic sessions.")
    try:
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            logger.info(f"HOD decision: {result['decision']} — {result['reason']}")
            return result
    except Exception as e:
        logger.error(f"HOD evaluation failed: {e}")
    return {"decision": "protect", "reason": "Could not evaluate, defaulting to protect student booking"}

def override_booking(booking_id: int, reason: str, tx_id: str = None) -> int:
    """Cancel a student booking and log HOD action"""
    update_booking_status(booking_id, "cancelled", tx_id)
    action_id = add_hod_action("override", booking_id, reason, tx_id)
    logger.info(f"HOD overrode booking #{booking_id}: {reason}")
    return action_id

def get_department_overview() -> dict:
    """Get full department booking and resource overview"""
    all_bookings = get_bookings()
    teacher_bookings = [b for b in all_bookings if b["role"] == "teacher"]
    student_bookings = [b for b in all_bookings if b["role"] == "student"]
    hod_actions = get_hod_actions()

    summary_prompt = f"""Summarize the current department lab usage:
Total bookings: {len(all_bookings)}
Teacher bookings: {len(teacher_bookings)}
Student bookings: {len(student_bookings)}
HOD interventions: {len(hod_actions)}

Write a 3-sentence department status summary."""

    summary = ollama(summary_prompt, system="You are a HOD assistant. Be brief and professional.")

    return {
        "total_bookings": len(all_bookings),
        "teacher_bookings": len(teacher_bookings),
        "student_bookings": len(student_bookings),
        "hod_actions": len(hod_actions),
        "summary": summary,
        "recent_actions": hod_actions[:5]
    }

def generate_hod_report() -> str:
    """Generate a detailed HOD report using LLM"""
    overview = get_department_overview()
    return overview["summary"]
