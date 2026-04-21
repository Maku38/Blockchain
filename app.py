from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

sys.path.append(os.path.dirname(__file__))

from database.db import init_db, get_bookings
from agents.teacher_agent import parse_booking_request, generate_confirmation_message
from agents.lab_agent import process_booking_request, confirm_booking
from blockchain.cscoin import log_booking_to_blockchain, get_blockchain_info, get_balance

app = Flask(__name__)
CORS(app)

# Initialize database on startup
init_db()

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "CS-Coin Agent System running"})

@app.route('/api/blockchain/info', methods=['GET'])
def blockchain_info():
    try:
        info = get_blockchain_info()
        balance = get_balance()
        return jsonify({"status": "ok", "info": info, "balance": balance})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/bookings', methods=['GET'])
def list_bookings():
    bookings = get_bookings()
    result = []
    for b in bookings:
        result.append({
            "id": b[0], "lab": b[1], "teacher": b[2],
            "date": b[3], "start_time": b[4], "end_time": b[5],
            "purpose": b[6], "tx_id": b[7], "created_at": b[8]
        })
    return jsonify({"status": "ok", "bookings": result})

@app.route('/api/book', methods=['POST'])
def book_lab():
    data = request.json
    natural_input = data.get("request")
    teacher_name = data.get("teacher", "Prof. Unknown")

    if not natural_input:
        return jsonify({"status": "error", "message": "No request provided"}), 400

    # Step 1: Teacher Agent parses natural language
    print(f"[Teacher Agent] Parsing: {natural_input}")
    parsed = parse_booking_request(natural_input, teacher_name)

    if parsed["status"] == "error":
        return jsonify({"status": "error", "message": parsed["message"], "raw": parsed.get("raw")}), 400

    booking_data = parsed["data"]
    print(f"[Teacher Agent] Parsed: {booking_data}")

    # Step 2: Lab Agent checks availability
    print(f"[Lab Agent] Checking availability for {booking_data}")
    availability = process_booking_request(booking_data)
    print(f"[Lab Agent] Result: {availability['status']}")

    if availability["status"] == "conflict":
        response = {
            "status": "conflict",
            "message": availability["message"],
            "parsed_request": booking_data,
            "alternate_start": availability.get("alternate_start"),
            "alternate_end": availability.get("alternate_end"),
            "lab": availability.get("lab"),
            "date": availability.get("date")
        }
        return jsonify(response)

    # Step 3: Log to CS-Coin blockchain
    print(f"[Blockchain] Logging booking to CS-Coin...")
    try:
        tx_id = log_booking_to_blockchain(booking_data)
        print(f"[Blockchain] TX ID: {tx_id}")
    except Exception as e:
        print(f"[Blockchain] Warning: {e}")
        tx_id = "blockchain-unavailable"

    # Step 4: Confirm booking in database
    booking_id = confirm_booking(booking_data, tx_id)
    print(f"[Database] Booking confirmed with ID: {booking_id}")

    # Step 5: Teacher Agent generates confirmation message
    confirmation_msg = generate_confirmation_message(booking_data, tx_id, booking_id)

    return jsonify({
        "status": "confirmed",
        "booking_id": booking_id,
        "tx_id": tx_id,
        "message": confirmation_msg,
        "booking": booking_data
    })

@app.route('/api/book/confirm-alternate', methods=['POST'])
def confirm_alternate():
    """Accept an alternate time suggested by Lab Agent"""
    data = request.json
    booking_data = {
        "teacher": data["teacher"],
        "lab": data["lab"],
        "date": data["date"],
        "start_time": data["start_time"],
        "end_time": data["end_time"],
        "purpose": data.get("purpose", "Lab session")
    }

    # Log to blockchain
    try:
        tx_id = log_booking_to_blockchain(booking_data)
    except Exception as e:
        tx_id = "blockchain-unavailable"

    booking_id = confirm_booking(booking_data, tx_id)
    confirmation_msg = generate_confirmation_message(booking_data, tx_id, booking_id)

    return jsonify({
        "status": "confirmed",
        "booking_id": booking_id,
        "tx_id": tx_id,
        "message": confirmation_msg,
        "booking": booking_data
    })

if __name__ == '__main__':
    print("Starting CS-Coin Agent System...")
    print("Make sure bitcoind is running: bitcoind -regtest -datadir=$HOME/.cscoin -daemon")
    app.run(debug=True, port=5000)
