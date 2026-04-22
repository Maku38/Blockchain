import requests
import json
from logger import get_logger
from database.db import get_inventory, update_inventory_availability

logger = get_logger("inventory_agent")
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

def ollama(prompt, system=""):
    payload = {"model": MODEL, "prompt": prompt, "system": system, "stream": False}
    r = requests.post(OLLAMA_URL, json=payload, timeout=60)
    return r.json()["response"].strip()

def check_equipment_availability(lab: str, equipment_needed: list) -> dict:
    """Check if requested equipment is available in the lab"""
    inventory = get_inventory(lab=lab)
    result = {"available": True, "items": [], "unavailable": []}

    for item_type in equipment_needed:
        matches = [i for i in inventory if i["item_type"] == item_type]
        if not matches:
            result["unavailable"].append({"type": item_type, "reason": "Not available in this lab"})
            result["available"] = False
        else:
            item = matches[0]
            if item["available"] <= 0 or item["status"] != "working":
                result["unavailable"].append({
                    "type": item_type,
                    "reason": item["notes"] or "Currently unavailable"
                })
                result["available"] = False
            else:
                result["items"].append({
                    "id": item["id"],
                    "type": item_type,
                    "name": item["item_name"],
                    "available": item["available"]
                })

    logger.info(f"Inventory check for {lab}: {equipment_needed} → available={result['available']}")
    return result

def get_lab_summary(lab: str) -> dict:
    """Get full inventory summary for a lab"""
    inventory = get_inventory(lab=lab)
    summary = {
        "lab": lab,
        "workstations": 0,
        "workstations_available": 0,
        "projector": False,
        "projector_status": "none",
        "software": [],
        "issues": []
    }
    for item in inventory:
        if item["item_type"] == "workstation":
            summary["workstations"] = item["total"]
            summary["workstations_available"] = item["available"]
        elif item["item_type"] == "projector":
            summary["projector"] = item["available"] > 0 and item["status"] == "working"
            summary["projector_status"] = item["status"]
            if item["notes"]:
                summary["issues"].append(f"Projector: {item['notes']}")
        elif item["item_type"] == "software":
            summary["software"].append({
                "name": item["item_name"],
                "licenses": item["available"]
            })
    return summary

def get_all_inventory_status() -> list:
    """Get inventory status for all labs"""
    labs = ["Lab-A", "Lab-B", "Lab-C", "Classroom-1", "Classroom-2"]
    return [get_lab_summary(lab) for lab in labs]

def generate_inventory_report() -> str:
    """Use LLM to generate a human-readable inventory report"""
    inventory = get_all_inventory_status()
    inv_text = json.dumps(inventory, indent=2)
    return ollama(
        f"Generate a brief inventory status report for a CS department based on this data:\n{inv_text}\n"
        "Keep it to 5-6 lines. Highlight any issues.",
        system="You are a lab resource manager. Be concise and factual."
    )

def reserve_equipment(booking_id: int, items: list):
    """Reserve equipment items for a booking"""
    for item in items:
        update_inventory_availability(item["id"], -1)
        logger.info(f"Reserved {item['name']} for booking #{booking_id}")

def release_equipment(booking_id: int, items: list):
    """Release equipment after booking ends"""
    for item in items:
        update_inventory_availability(item["id"], +1)
        logger.info(f"Released {item['name']} from booking #{booking_id}")
