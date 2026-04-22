from flask import Flask, request, jsonify
from flask_cors import CORS
import sys, os, json
sys.path.append(os.path.dirname(__file__))

from database.db import init_db, get_bookings, get_inventory, get_hod_actions
from agents.teacher_agent import parse_booking_request, generate_confirmation_message
from agents.student_agent import parse_student_request, generate_student_confirmation
from agents.lab_agent import process_booking_request, confirm_booking
from agents.inventory_agent import check_equipment_availability, get_all_inventory_status, generate_inventory_report
from agents.hod_agent import evaluate_override, override_booking, get_department_overview
from blockchain.cscoin import log_booking_to_blockchain, get_blockchain_info, get_balance
from logger import get_logger

logger = get_logger("app")
app = Flask(__name__)
CORS(app)
init_db()

# ─── Health ──────────────────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "CS-Coin Agent System running"})

# ─── Blockchain ──────────────────────────────────────────────────────────────

@app.route('/api/blockchain/info', methods=['GET'])
def blockchain_info():
    try:
        return jsonify({"status": "ok", "info": get_blockchain_info(), "balance": get_balance()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ─── Bookings ────────────────────────────────────────────────────────────────

@app.route('/api/bookings', methods=['GET'])
def list_bookings():
    role = request.args.get('role')
    lab = request.args.get('lab')
    bookings = get_bookings(lab=lab, role=role)
    return jsonify({"status": "ok", "bookings": bookings})

@app.route('/api/book', methods=['POST'])
def book_lab():
    data = request.json
    natural_input = data.get("request")
    teacher_name = data.get("teacher", "Prof. Unknown")

    if not natural_input:
        return jsonify({"status": "error", "message": "No request provided"}), 400

    logger.info(f"[Teacher Agent] Request from {teacher_name}: {natural_input}")
    parsed = parse_booking_request(natural_input, teacher_name)
    if parsed["status"] == "error":
        return jsonify({"status": "error", "message": parsed["message"]}), 400

    booking_data = parsed["data"]
    booking_data["role"] = "teacher"

    # Check inventory if needed
    equipment = booking_data.get("equipment_needed", ["workstation", "projector"])
    inv_check = check_equipment_availability(booking_data["lab"], equipment)
    if not inv_check["available"]:
        issues = ", ".join([i["reason"] for i in inv_check["unavailable"]])
        return jsonify({"status": "inventory_issue", "message": f"Equipment issue: {issues}", "details": inv_check}), 200

    availability = process_booking_request(booking_data)
    if availability["status"] == "conflict":
        return jsonify({
            "status": "conflict",
            "message": availability["message"],
            "parsed_request": booking_data,
            "alternate_start": availability.get("alternate_start"),
            "alternate_end": availability.get("alternate_end"),
            "lab": availability.get("lab"),
            "date": availability.get("date")
        })

    try:
        tx_id = log_booking_to_blockchain(booking_data)
    except Exception as e:
        logger.warning(f"Blockchain logging failed: {e}")
        tx_id = "blockchain-unavailable"

    booking_id = confirm_booking(booking_data, tx_id)
    msg = generate_confirmation_message(booking_data, tx_id, booking_id)
    logger.info(f"Teacher booking confirmed: #{booking_id}, TX={tx_id[:16]}...")
    return jsonify({"status": "confirmed", "booking_id": booking_id, "tx_id": tx_id, "message": msg, "booking": booking_data})

@app.route('/api/student/book', methods=['POST'])
def student_book():
    data = request.json
    natural_input = data.get("request")
    student_name = data.get("student", "Student")

    if not natural_input:
        return jsonify({"status": "error", "message": "No request provided"}), 400

    logger.info(f"[Student Agent] Request from {student_name}: {natural_input}")
    parsed = parse_student_request(natural_input, student_name)
    if parsed["status"] == "error":
        return jsonify({"status": "error", "message": parsed["message"]}), 400

    booking_data = parsed["data"]
    booking_data["teacher"] = booking_data.get("student", student_name)
    booking_data["role"] = "student"

    # Check inventory
    equipment = booking_data.get("equipment_needed", ["workstation"])
    inv_check = check_equipment_availability(booking_data["lab"], equipment)
    if not inv_check["available"]:
        issues = ", ".join([i["reason"] for i in inv_check["unavailable"]])
        return jsonify({"status": "inventory_issue", "message": f"Equipment issue: {issues}"}), 200

    availability = process_booking_request(booking_data)
    if availability["status"] == "conflict":
        # Check if conflict is with a teacher booking
        from database.db import check_conflict, get_booking_by_id
        conflicts = check_conflict(booking_data["lab"], booking_data["date"],
                                   booking_data["start_time"], booking_data["end_time"])
        teacher_conflicts = [c for c in conflicts if c.get("role") == "teacher"]
        if teacher_conflicts:
            return jsonify({
                "status": "conflict",
                "message": availability["message"],
                "conflict_type": "teacher_priority",
                "alternate_start": availability.get("alternate_start"),
                "alternate_end": availability.get("alternate_end"),
                "lab": availability.get("lab"),
                "date": availability.get("date")
            })
        return jsonify({
            "status": "conflict",
            "message": availability["message"],
            "conflict_type": "student_conflict",
            "alternate_start": availability.get("alternate_start"),
            "alternate_end": availability.get("alternate_end"),
        })

    try:
        tx_id = log_booking_to_blockchain(booking_data)
    except Exception as e:
        logger.warning(f"Blockchain logging failed: {e}")
        tx_id = "blockchain-unavailable"

    booking_id = confirm_booking(booking_data, tx_id)
    msg = generate_student_confirmation(booking_data, tx_id, booking_id)
    logger.info(f"Student booking confirmed: #{booking_id}")
    return jsonify({"status": "confirmed", "booking_id": booking_id, "tx_id": tx_id, "message": msg, "booking": booking_data})

@app.route('/api/book/confirm-alternate', methods=['POST'])
def confirm_alternate():
    data = request.json
    booking_data = {
        "teacher": data["teacher"], "lab": data["lab"],
        "date": data["date"], "start_time": data["start_time"],
        "end_time": data["end_time"], "purpose": data.get("purpose", "Lab session"),
        "role": data.get("role", "teacher")
    }
    try:
        tx_id = log_booking_to_blockchain(booking_data)
    except Exception as e:
        tx_id = "blockchain-unavailable"
    booking_id = confirm_booking(booking_data, tx_id)
    msg = generate_confirmation_message(booking_data, tx_id, booking_id)
    return jsonify({"status": "confirmed", "booking_id": booking_id, "tx_id": tx_id, "message": msg, "booking": booking_data})

# ─── Inventory ───────────────────────────────────────────────────────────────

@app.route('/api/inventory', methods=['GET'])
def inventory_status():
    lab = request.args.get('lab')
    if lab:
        items = get_inventory(lab=lab)
        return jsonify({"status": "ok", "lab": lab, "inventory": items})
    return jsonify({"status": "ok", "inventory": get_all_inventory_status()})

@app.route('/api/inventory/report', methods=['GET'])
def inventory_report():
    report = generate_inventory_report()
    return jsonify({"status": "ok", "report": report})

# ─── HOD ─────────────────────────────────────────────────────────────────────

@app.route('/api/hod/overview', methods=['GET'])
def hod_overview():
    overview = get_department_overview()
    return jsonify({"status": "ok", "overview": overview})

@app.route('/api/hod/override', methods=['POST'])
def hod_override():
    data = request.json
    booking_id = data.get("booking_id")
    reason = data.get("reason", "HOD override")
    if not booking_id:
        return jsonify({"status": "error", "message": "booking_id required"}), 400
    try:
        tx_id = log_booking_to_blockchain({"lab": "HOD", "teacher": "HOD",
            "date": "override", "start_time": "00:00", "end_time": "00:00"})
    except Exception:
        tx_id = "blockchain-unavailable"
    action_id = override_booking(booking_id, reason, tx_id)
    return jsonify({"status": "ok", "message": f"Booking #{booking_id} cancelled by HOD", "action_id": action_id, "tx_id": tx_id})

@app.route('/api/hod/actions', methods=['GET'])
def hod_actions():
    return jsonify({"status": "ok", "actions": get_hod_actions()})


# ─── Wallet API ──────────────────────────────────────────────────────────────

@app.route('/api/wallet/info', methods=['GET'])
def wallet_info():
    try:
        from blockchain.cscoin import cli
        balance = get_balance()
        addresses = json.loads(cli(["listreceivedbyaddress", "0", "true"]))
        new_addr = cli(["getnewaddress"])
        txs = json.loads(cli(["listtransactions", "*", "10"]))
        return jsonify({
            "status": "ok",
            "balance": balance,
            "receive_address": new_addr,
            "addresses": addresses[:5],
            "transactions": txs
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/wallet/send', methods=['POST'])
def wallet_send():
    try:
        from blockchain.cscoin import cli
        data = request.json
        to_address = data.get("address")
        amount = data.get("amount")
        if not to_address or not amount:
            return jsonify({"status": "error", "message": "address and amount required"}), 400
        tx_id = cli(["sendtoaddress", to_address, str(amount)])
        logger.info(f"Sent {amount} CSC to {to_address}, TX={tx_id}")
        return jsonify({"status": "ok", "tx_id": tx_id, "amount": amount, "to": to_address})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/wallet/address', methods=['GET'])
def new_address():
    try:
        from blockchain.cscoin import cli
        addr = cli(["getnewaddress"])
        return jsonify({"status": "ok", "address": addr})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/wallet/transactions', methods=['GET'])
def transactions():
    try:
        from blockchain.cscoin import cli
        import json
        txs = json.loads(cli(["listtransactions", "*", "20"]))
        return jsonify({"status": "ok", "transactions": txs})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/wallet/mine', methods=['POST'])
def mine():
    try:
        from blockchain.cscoin import mine_block
        block_hash = mine_block()
        balance = get_balance()
        return jsonify({"status": "ok", "block_hash": block_hash, "new_balance": balance})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    logger.info('Starting CS-Coin Agent System...')
    print('Make sure bitcoind is running')
    app.run(debug=True, port=5000)
