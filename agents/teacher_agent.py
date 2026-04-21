import requests
import json
import re
from datetime import datetime, timedelta

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

def ollama(prompt, system=""):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False
    }
    r = requests.post(OLLAMA_URL, json=payload)
    return r.json()["response"].strip()

def parse_booking_request(natural_language_input: str, teacher_name: str) -> dict:
    """
    Teacher Agent: takes natural language input, uses LLM to extract
    structured booking details.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    system_prompt = """You are a smart assistant that extracts lab booking details from natural language.
Always respond with ONLY a valid JSON object, no explanation, no markdown.
Available labs are: Lab-A, Lab-B, Lab-C.
Date format: YYYY-MM-DD. Time format: HH:MM (24h).
If no specific lab is mentioned, default to Lab-A.
If duration is mentioned but not end time, calculate end_time = start_time + duration.
If date is relative (today, tomorrow, friday), resolve it."""

    prompt = f"""Today is {today}. Tomorrow is {tomorrow}.
Extract booking details from this request: "{natural_language_input}"
Teacher name: {teacher_name}

Respond with ONLY this JSON (no markdown, no explanation):
{{
  "teacher": "{teacher_name}",
  "lab": "Lab-A",
  "date": "YYYY-MM-DD",
  "start_time": "HH:MM",
  "end_time": "HH:MM",
  "purpose": "brief description"
}}"""

    response = ollama(prompt, system=system_prompt)

    # Extract JSON from response
    try:
        # Try to find JSON in response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            return {"status": "parsed", "data": parsed}
        else:
            return {"status": "error", "message": "Could not parse booking details", "raw": response}
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON from LLM", "raw": response}

def generate_confirmation_message(booking_details: dict, tx_id: str, booking_id: int) -> str:
    """Generate a natural language confirmation message"""
    prompt = f"""Generate a short friendly confirmation message for this lab booking:
Lab: {booking_details['lab']}
Teacher: {booking_details['teacher']}  
Date: {booking_details['date']}
Time: {booking_details['start_time']} - {booking_details['end_time']}
Purpose: {booking_details['purpose']}
Blockchain TX ID: {tx_id[:16]}...
Booking ID: {booking_id}

Keep it to 2-3 sentences. Mention the booking is recorded on CS-Coin blockchain."""

    return ollama(prompt, system="You are a helpful university booking assistant. Be concise and friendly.")
