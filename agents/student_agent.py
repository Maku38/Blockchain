import requests
import json
import re
from datetime import datetime, timedelta
from logger import get_logger

logger = get_logger("student_agent")
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

def ollama(prompt, system=""):
    payload = {"model": MODEL, "prompt": prompt, "system": system, "stream": False}
    r = requests.post(OLLAMA_URL, json=payload, timeout=60)
    return r.json()["response"].strip()

def parse_student_request(natural_language_input: str, student_name: str) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    system_prompt = """You are a smart assistant that extracts lab booking details from student requests.
Always respond with ONLY a valid JSON object, no explanation, no markdown.
Available labs: Lab-A, Lab-B, Lab-C. Available classrooms: Classroom-1, Classroom-2.
Date format: YYYY-MM-DD. Time format: HH:MM (24h).
Students typically book for self-study, project work, or practice sessions."""

    prompt = f"""Today is {today}. Tomorrow is {tomorrow}.
Extract booking details from this student request: "{natural_language_input}"
Student name: {student_name}

Respond with ONLY this JSON:
{{
  "student": "{student_name}",
  "lab": "Lab-A",
  "date": "YYYY-MM-DD",
  "start_time": "HH:MM",
  "end_time": "HH:MM",
  "purpose": "brief description",
  "equipment_needed": ["workstation", "projector"]
}}"""

    response = ollama(prompt, system=system_prompt)
    logger.debug(f"LLM response: {response[:100]}")

    try:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            logger.info(f"Student request parsed: {parsed.get('lab')} on {parsed.get('date')}")
            return {"status": "parsed", "data": parsed}
        return {"status": "error", "message": "Could not parse request", "raw": response}
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        return {"status": "error", "message": "Invalid response from LLM", "raw": response}

def generate_student_confirmation(booking_details: dict, tx_id: str, booking_id: int) -> str:
    prompt = f"""Generate a short friendly confirmation for a student lab booking:
Lab: {booking_details['lab']}
Student: {booking_details.get('student', booking_details.get('teacher', 'Student'))}
Date: {booking_details['date']}
Time: {booking_details['start_time']} - {booking_details['end_time']}
Purpose: {booking_details['purpose']}
Booking ID: #{booking_id}
TX ID: {tx_id[:16]}...

2 sentences max. Mention booking is on CS-Coin blockchain."""
    return ollama(prompt, system="You are a helpful university assistant. Be brief and friendly.")
